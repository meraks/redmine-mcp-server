"""Required-field discovery tool.

``get_required_fields`` exposes the operator-declared conditional
required-field rules (``required_fields.json``) that the Redmine REST API
cannot describe on its own -- workflow rules, role-based field permissions,
and tracker/category-bound required-field settings (see the #119 caveat).
"""

from typing import Any, Dict, Optional

from .._offload import offloaded
from ..required_fields import _load_required_fields_config, _resolve_rules
from ..server import mcp


@mcp.tool()
@offloaded
def get_required_fields(
    tracker_name: Optional[str] = None,
    category_name: Optional[str] = None,
    status_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the required-field rules for this Redmine's issue model.

    Stock Redmine's REST API only reports the ``is_required`` flag on each
    custom field's definition; it cannot see required-ness imposed by
    workflow rules, role permissions, or tracker/category-bound settings.
    When this deployment's issue model differs from stock (required fields
    varying by tracker or category), those rules live in a
    ``required_fields.json`` file that this tool surfaces.

    Call with no arguments to read the whole rule set, or pass
    ``tracker_name`` / ``category_name`` / ``status_name`` (matched
    case-insensitively) to get the rules that apply to a specific context.

    Args:
        tracker_name: Optional tracker name (e.g. ``"Bug"``) to filter by.
        category_name: Optional issue-category name to filter by.
        status_name: Optional status name to filter by.

    Returns:
        With no filters, ``{"rules": <full config>}``. With any filter,
        ``{"required": [...], "defaults": {...}}`` merged across the
        matching dimensions. Each entry in ``required`` names a standard
        issue field by API key (``priority_id``, ``subject``, ...) or a
        custom field by display name (``Department``).
    """
    config = _load_required_fields_config()
    if tracker_name is None and category_name is None and status_name is None:
        return {"rules": config}
    return _resolve_rules(
        config,
        tracker_name=tracker_name,
        category_name=category_name,
        status_name=status_name,
    )
