"""Config-driven required-field rules for non-standard issue models.

Redmine's REST API exposes only the field-definition ``is_required`` flag
(see the #119 caveat on ``list_project_issue_custom_fields``); it cannot see
workflow rules, role-based field permissions, or tracker/category-bound
required-field settings. Deployments whose issue model differs from stock
Redmine -- required fields varying by tracker or category -- declare those
rules in a ``required_fields.json`` file, which this module loads and
evaluates.

Config shape::

    {
      "by_tracker": {
        "Bug": {"required": ["priority_id", "Department"],
                "defaults": {"Department": "Eng"}}
      },
      "by_category": {
        "Hardware": {"required": ["cf_20"]}
      },
      "by_status": {
        "In Progress": {"required": ["cf_8"]}
      }
    }

Keys are matched case-insensitively. ``required`` entries name standard
issue fields by their API key (``priority_id``, ``subject``, ...) and custom
fields by their display name (``Department``); ``defaults`` supply values for
fields the caller left out.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _is_missing(value: Any) -> bool:
    """Return True when a value should be treated as absent."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _parse_required_fields_config(text: Optional[str]) -> Dict[str, Any]:
    """Parse a ``required_fields.json`` document into a config dict.

    Returns ``{}`` for a blank document. Raises ``ValueError`` on invalid
    JSON or a non-object document.
    """
    if text is None:
        return {}
    raw = text.strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid required_fields JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("required_fields config must be a JSON object.")
    return parsed


def _load_required_fields_config() -> Dict[str, Any]:
    """Load the operator-declared required-field rules from disk.

    The path is taken from ``REDMINE_REQUIRED_FIELDS_FILE`` (default
    ``./required_fields.json``). A missing file yields ``{}`` (rules are
    optional); an unreadable or invalid file raises ``ValueError`` so a
    misconfigured deployment fails loudly rather than silently skipping
    the rules.
    """
    path = os.getenv("REDMINE_REQUIRED_FIELDS_FILE", "./required_fields.json")
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read required_fields file {path}: {exc}") from exc
    return _parse_required_fields_config(text)


def _norm(name: str) -> str:
    """Normalize a tracker/category/status name for case-insensitive match."""
    return str(name).strip().lower()


def _find_rule(group: Dict[str, Any], norm_name: str) -> Optional[Dict[str, Any]]:
    """Return the rule whose key matches ``norm_name`` (case-insensitive)."""
    for key, rule in group.items():
        if _norm(key) == norm_name:
            return rule
    return None


def _resolve_rules(
    config: Dict[str, Any],
    tracker_name: Optional[str] = None,
    category_name: Optional[str] = None,
    status_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Merge the rules matching the given tracker/category/status context.

    Returns ``{"required": [...], "defaults": {...}}``. Multiple dimensions
    combine: ``required`` entries are de-duplicated in first-seen order and
    ``defaults`` merge with later dimensions winning.
    """
    required: List[str] = []
    defaults: Dict[str, Any] = {}

    dimensions = (
        ("tracker", tracker_name),
        ("category", category_name),
        ("status", status_name),
    )
    for dim, name in dimensions:
        if name is None:
            continue
        group = config.get(f"by_{dim}")
        if not isinstance(group, dict):
            continue
        rule = _find_rule(group, _norm(name))
        if rule is None:
            continue
        for field in rule.get("required") or []:
            if field not in required:
                required.append(field)
        rule_defaults = rule.get("defaults")
        if isinstance(rule_defaults, dict):
            defaults.update(rule_defaults)

    return {"required": required, "defaults": defaults}


def _missing_required(rules: Dict[str, Any], payload: Dict[str, Any]) -> List[str]:
    """Return the required fields absent from ``payload`` (in declared order).

    A field counts as present only when it is a key of ``payload`` with a
    non-missing value (``None``, blank string, and empty containers are
    missing).
    """
    missing: List[str] = []
    for field in rules.get("required") or []:
        if field not in payload or _is_missing(payload.get(field)):
            missing.append(field)
    return missing


def _apply_defaults(rules: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return ``payload`` with missing fields filled from ``rules`` defaults.

    Never overwrites an existing non-missing value, and never injects a
    default whose own value is missing.
    """
    updated = dict(payload)
    for field, value in (rules.get("defaults") or {}).items():
        if _is_missing(updated.get(field)) and not _is_missing(value):
            updated[field] = value
    return updated
