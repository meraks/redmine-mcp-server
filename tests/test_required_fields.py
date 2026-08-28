"""Tests for the config-driven required-field rules (#conditional-required).

Redmine's REST API exposes only the field-definition ``is_required`` flag
(see the #119 caveat on ``list_project_issue_custom_fields``). It cannot
see workflow rules, role-based field permissions, or tracker/category-bound
required-field settings. For deployments whose issue model differs from
stock Redmine -- required fields varying by tracker or category -- an
operator-declared ``required_fields.json`` file fills that gap.

The pure helpers under test translate that file into: (a) merged rules for a
given tracker/category/status context, (b) the list of still-missing required
fields given a payload, and (c) default values applied to missing fields.
"""

import pytest
from unittest.mock import patch

from redmine_mcp_server.required_fields import (
    _apply_defaults,
    _load_required_fields_config,
    _missing_required,
    _parse_required_fields_config,
    _resolve_rules,
)


class TestParseRequiredFieldsConfig:
    def test_parses_valid_config(self):
        cfg = _parse_required_fields_config(
            '{"by_tracker": {"Bug": {"required": ["priority_id", "Department"],'
            ' "defaults": {"Department": "Eng"}}}}'
        )
        assert cfg["by_tracker"]["Bug"]["required"] == ["priority_id", "Department"]
        assert cfg["by_tracker"]["Bug"]["defaults"] == {"Department": "Eng"}

    def test_blank_or_empty_object_returns_empty(self):
        assert _parse_required_fields_config("") == {}
        assert _parse_required_fields_config("{}") == {}
        assert _parse_required_fields_config("   ") == {}

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_required_fields_config("{not valid json")


class TestResolveRules:
    def _cfg(self):
        return {
            "by_tracker": {
                "Bug": {"required": ["priority_id"], "defaults": {"priority_id": 4}},
                "Feature": {"required": ["cf_15"]},
            },
            "by_category": {
                "Hardware": {"required": ["Department"], "defaults": {"Department": "HW"}}
            },
        }

    def test_matches_tracker_by_name_case_insensitive(self):
        rules = _resolve_rules(self._cfg(), tracker_name="bug")
        assert rules["required"] == ["priority_id"]
        assert rules["defaults"] == {"priority_id": 4}

    def test_merges_tracker_and_category_rules(self):
        rules = _resolve_rules(self._cfg(), tracker_name="Bug", category_name="hardware")
        assert set(rules["required"]) == {"priority_id", "Department"}
        assert rules["defaults"] == {"priority_id": 4, "Department": "HW"}

    def test_no_match_returns_empty_rules(self):
        rules = _resolve_rules(self._cfg(), tracker_name="Task", category_name="Software")
        assert rules == {"required": [], "defaults": {}}

    def test_none_context_returns_empty_rules(self):
        assert _resolve_rules(self._cfg()) == {"required": [], "defaults": {}}


class TestMissingRequired:
    def test_reports_missing_standard_and_custom_name_fields(self):
        rules = {"required": ["priority_id", "Department"]}
        assert set(_missing_required(rules, {"subject": "x"})) == {
            "priority_id",
            "Department",
        }

    def test_present_fields_not_reported(self):
        rules = {"required": ["priority_id", "Department"]}
        assert _missing_required(rules, {"priority_id": 3, "Department": "Eng"}) == []

    def test_empty_values_count_as_missing(self):
        rules = {"required": ["Department"]}
        assert _missing_required(rules, {"Department": ""}) == ["Department"]
        assert _missing_required(rules, {"Department": None}) == ["Department"]
        assert _missing_required(rules, {"Department": []}) == ["Department"]

    def test_empty_rules_report_nothing(self):
        assert _missing_required({"required": []}, {}) == []


class TestApplyDefaults:
    def test_fills_missing_defaults_only(self):
        rules = {"defaults": {"Department": "Eng", "priority_id": 3}}
        out = _apply_defaults(rules, {"Department": "Hardware"})
        # Existing value is preserved.
        assert out["Department"] == "Hardware"
        # Missing value is filled.
        assert out["priority_id"] == 3

    def test_no_defaults_leaves_payload_unchanged(self):
        payload = {"subject": "x"}
        out = _apply_defaults({"defaults": {}}, payload)
        assert out == payload

    def test_does_not_fill_empty_required_default_into_absent_key(self):
        # A default value that itself is missing should not be injected.
        out = _apply_defaults({"defaults": {"Department": ""}}, {})
        assert "Department" not in out


class TestLoadRequiredFieldsConfig:
    def test_returns_empty_when_file_missing(self, monkeypatch):
        monkeypatch.setenv("REDMINE_REQUIRED_FIELDS_FILE", "/nonexistent/req.json")
        assert _load_required_fields_config() == {}

    def test_reads_file_and_parses(self, monkeypatch, tmp_path):
        p = tmp_path / "required_fields.json"
        p.write_text('{"by_tracker": {"Bug": {"required": ["priority_id"]}}}')
        monkeypatch.setenv("REDMINE_REQUIRED_FIELDS_FILE", str(p))
        cfg = _load_required_fields_config()
        assert cfg["by_tracker"]["Bug"]["required"] == ["priority_id"]

    def test_invalid_json_raises(self, monkeypatch, tmp_path):
        p = tmp_path / "required_fields.json"
        p.write_text("{not json")
        monkeypatch.setenv("REDMINE_REQUIRED_FIELDS_FILE", str(p))
        with pytest.raises(ValueError):
            _load_required_fields_config()


class TestGetRequiredFieldsTool:
    @pytest.mark.asyncio
    async def test_no_filters_returns_full_config(self, monkeypatch):
        from redmine_mcp_server.tools.required_fields import get_required_fields

        cfg = {"by_tracker": {"Bug": {"required": ["priority_id"]}}}
        monkeypatch.setattr(
            "redmine_mcp_server.tools.required_fields._load_required_fields_config",
            lambda: cfg,
        )
        result = await get_required_fields()
        assert result["rules"] == cfg

    @pytest.mark.asyncio
    async def test_filters_resolve_rules(self, monkeypatch):
        from redmine_mcp_server.tools.required_fields import get_required_fields

        cfg = {
            "by_tracker": {"Bug": {"required": ["priority_id"]}},
            "by_category": {"Hardware": {"required": ["Department"]}},
        }
        monkeypatch.setattr(
            "redmine_mcp_server.tools.required_fields._load_required_fields_config",
            lambda: cfg,
        )
        result = await get_required_fields(tracker_name="bug", category_name="hardware")
        assert set(result["required"]) == {"priority_id", "Department"}


class TestCreateIssueRequiredFieldEnforcement:
    """``create_redmine_issue`` pre-validates against the conditional rules
    before touching Redmine: it auto-fills defaults, blocks with a clear
    error when a required field is still missing, and passes through
    unchanged when no rules apply."""

    @pytest.mark.asyncio
    async def test_missing_required_field_blocks_create(self, monkeypatch):
        from redmine_mcp_server.tools.issues import create_redmine_issue

        cfg = {"by_tracker": {"Bug": {"required": ["Department"]}}}
        monkeypatch.setattr(
            "redmine_mcp_server.tools.issues._load_required_fields_config",
            lambda: cfg,
        )
        with patch("redmine_mcp_server._client.redmine") as m:
            m.tracker.get.return_value.name = "Bug"
            result = await create_redmine_issue(
                project_id=1, subject="x", fields={"tracker_id": 2}
            )

        assert "error" in result
        assert "Department" in result["error"]
        m.issue.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_defaults_fill_missing_field_and_create_proceeds(self, monkeypatch):
        from redmine_mcp_server.tools.issues import create_redmine_issue

        cfg = {
            "by_tracker": {
                "Bug": {"required": ["Department"], "defaults": {"Department": "Eng"}}
            }
        }
        monkeypatch.setattr(
            "redmine_mcp_server.tools.issues._load_required_fields_config",
            lambda: cfg,
        )
        with patch("redmine_mcp_server._client.redmine") as m:
            m.tracker.get.return_value.name = "Bug"
            m.issue.create.return_value = type("Issue", (), {"id": 123})()
            result = await create_redmine_issue(
                project_id=1, subject="x", fields={"tracker_id": 2}
            )

        assert "error" not in result
        m.issue.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_present_field_does_not_block(self, monkeypatch):
        from redmine_mcp_server.tools.issues import create_redmine_issue

        cfg = {"by_tracker": {"Bug": {"required": ["Department"]}}}
        monkeypatch.setattr(
            "redmine_mcp_server.tools.issues._load_required_fields_config",
            lambda: cfg,
        )
        with patch("redmine_mcp_server._client.redmine") as m:
            m.tracker.get.return_value.name = "Bug"
            m.issue.create.return_value = type("Issue", (), {"id": 123})()
            result = await create_redmine_issue(
                project_id=1, subject="x", fields={"tracker_id": 2, "Department": "Eng"}
            )

        assert "error" not in result
        m.issue.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_config_passes_through_unchanged(self, monkeypatch):
        from redmine_mcp_server.tools.issues import create_redmine_issue

        monkeypatch.setattr(
            "redmine_mcp_server.tools.issues._load_required_fields_config",
            lambda: {},
        )
        with patch("redmine_mcp_server._client.redmine") as m:
            m.issue.create.return_value = type("Issue", (), {"id": 123})()
            result = await create_redmine_issue(
                project_id=1, subject="x", fields={"tracker_id": 2}
            )

        assert "error" not in result
        m.issue.create.assert_called_once()
        # No name-resolution round-trip when no rules are configured.
        m.tracker.get.assert_not_called()
