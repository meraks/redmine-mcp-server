# Redmine MCP Server Tutorial (Claude Code)

Complete guide for installing, configuring, and using **this fork** of Redmine MCP Server with Claude Code.

> This project is a fork of `jztan/redmine-mcp-server` that has diverged from upstream and is maintained independently. It is **not** published to PyPI or any container registry — install from the prebuilt wheel or from source (see below). All licensing and permissions are consistent with the original repository (MIT).

---

## Prerequisites

- Python 3.10+
- Access to a Redmine instance (URL + API key)
- Claude Code installed

---

## 1. Install Redmine MCP Server

This fork is not on PyPI, so `uv tool install redmine-mcp-server` would fetch the **upstream** package, not this fork. Use one of the following.

### Option A: prebuilt wheel (recommended)

Download the latest `redmine_mcp_server-*.whl` from the project's Releases page, then:

```bash
# Install into the current environment
pip install redmine_mcp_server-*.whl

# Or install the MCP command globally via uv
uv tool install redmine_mcp_server-*.whl
```

### Option B: from source

```bash
git clone <this-repository-url>
cd redmine-mcp-server

# Install the tool (editable) via uv
uv tool install --from . redmine-mcp-server
# or, into the current environment:
pip install .
```

### Option C: Docker (build locally)

This fork does not publish prebuilt images, so build from the source checkout:

```bash
docker build -t redmine-mcp-server .
docker run -p 8000:8000 --env-file .env.docker redmine-mcp-server
```

---

## 2. Configure Environment

Create a `.env` file in your project directory:

```bash
cat > .env << 'EOF'
# Redmine connection (required)
REDMINE_URL=http://your-redmine-server.com

# Authentication - Use API key (recommended) or username/password
REDMINE_API_KEY=your_api_key
# OR use username/password:
# REDMINE_USERNAME=your_username
# REDMINE_PASSWORD=your_password

# Server configuration (optional, defaults shown)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Public URL for file serving (optional)
PUBLIC_HOST=localhost
PUBLIC_PORT=8000

# File management (optional)
ATTACHMENTS_DIR=./attachments
AUTO_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=10
ATTACHMENT_EXPIRES_MINUTES=60
EOF
```

**Get your API key**: Redmine → My account → API access key → Show

---

## 3. Two Transport Modes

| Mode | Command | Best for |
|------|---------|----------|
| **stdio (recommended for local)** | `redmine-mcp-server --stdio` | Local Claude Code, no network needed |
| **HTTP** | `redmine-mcp-server` | Remote, Docker, multi-client |

### stdio Mode (Recommended)

```bash
# Run directly with stdio transport
redmine-mcp-server --stdio
```

### HTTP Mode (Remote/Shared Server)

```bash
# Start server
redmine-mcp-server

# Verify
curl http://localhost:8000/health
```

---

## 4. Configure Claude Code

### stdio Mode (Recommended for Local Use)

```bash
claude mcp add redmine -- redmine-mcp-server --stdio
```

Or manually edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "redmine": {
      "command": "redmine-mcp-server",
      "args": ["--stdio"],
      "env": {
        "REDMINE_URL": "http://your-redmine-server.com",
        "REDMINE_API_KEY": "your_api_key"
      }
    }
  }
}
```

### HTTP Mode (Remote/Shared Server)

```bash
claude mcp add --transport http redmine http://localhost:8000/mcp
```

Or manually edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "redmine": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**If using local source with uv:**

```json
{
  "mcpServers": {
    "redmine": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/redmine-mcp", "python", "-m", "redmine_mcp_server.main", "--stdio"],
      "env": {
        "REDMINE_URL": "http://your-redmine-server.com",
        "REDMINE_API_KEY": "your_api_key"
      }
    }
  }
}
```

Restart Claude Code to load the server.

---

## 5. Verify Connection

In Claude Code:

```
> Use the get_mcp_server_info tool to check server status
```

Expected response:

```json
{
  "version": "2.11.0",
  "auth_mode": "legacy",
  "read_only": false,
  "current_user": {"id": 1, "name": "Your Name"}
}
```

---

## 6. Available Tools (42 core tools)

This fork provides 42 core MCP tools (plus 1 operator tool exposed by `REDMINE_MCP_EXPOSE_ADMIN_TOOLS=true`). The optional plugin tools from upstream (Checklists, Products, CRM/Contacts, DMSF Documents) and the MCP Apps UI are **not included** in this fork.

### Issue Operations (13)

| Tool | Description |
|------|-------------|
| `get_redmine_issue` | Get issue details with journals, attachments, custom fields |
| `list_redmine_issues` | List issues with filters, pagination, field selection |
| `search_redmine_issues` | Text search across issues |
| `create_redmine_issue` | Create new issues |
| `update_redmine_issue` | Update existing issues |
| `delete_redmine_issue` | Hard delete with confirmation |
| `copy_issue` | Duplicate an issue |
| `list_subtasks` | List child issues |
| `manage_issue_relation` | List/create/delete issue relations |
| `manage_issue_watcher` | Add/remove watchers |
| `manage_issue_note` | Edit/toggle privacy of journal notes |
| `get_private_notes` | Retrieve private notes only |
| `manage_issue_category` | Manage issue categories |

### Project Operations (9)

| Tool | Description |
|------|-------------|
| `list_redmine_projects` | List all accessible projects |
| `list_project_issue_custom_fields` | List custom fields for a project |
| `list_redmine_versions` | List versions/milestones |
| `manage_redmine_version` | Create/update/delete versions |
| `list_project_members` | List project members and roles |
| `summarize_project_status` | Comprehensive project summary |
| `list_redmine_roles` | List all roles |
| `get_project_modules` | Get enabled modules |
| `manage_project_member` | Add/update/remove project membership |

### Time Tracking (4)

| Tool | Description |
|------|-------------|
| `list_time_entries` | List time entries with filters |
| `manage_time_entry` | Create/update time entries |
| `list_time_entry_activities` | List available activities |
| `import_time_entries` | Bulk import time entries |

### Discovery / Enumeration (8)

| Tool | Description |
|------|-------------|
| `list_redmine_trackers` | List all trackers (Bug, Feature, etc.) |
| `list_project_trackers` | List trackers for a project |
| `list_redmine_issue_statuses` | List all statuses with is_closed flag |
| `list_redmine_issue_priorities` | List all priority levels |
| `list_redmine_users` | Filter/list users (admin) |
| `get_current_user` | Get authenticated user profile |
| `list_redmine_queries` | List saved custom queries |
| `get_required_fields` | Get conditional required-field rules |

### Search & Wiki (2)

| Tool | Description |
|------|-------------|
| `search_entire_redmine` | Global search (issues + wiki) |
| `manage_redmine_wiki_page` | List/get/create/update/delete/rename wiki pages |

### File Operations (4)

| Tool | Description |
|------|-------------|
| `list_files` | List project files |
| `upload_file` | Upload file (base64, URL, or server path) |
| `delete_file` | Delete project file |
| `get_redmine_attachment` | Download attachment |

### Gantt (1)

| Tool | Description |
|------|-------------|
| `get_gantt_chart` | Project timeline with dates, dependencies, milestones |

### Meta (1)

| Tool | Description |
|------|-------------|
| `get_mcp_server_info` | Server version, auth mode, current user |

---

## 7. Common Commands Reference

> Replace the placeholders below with values from **your** Redmine:
> `<PROJECT_ID>`, `<ISSUE_ID>`, `<USER_ID>`, `<CF_ID>` (a custom field id), and `<VALUE>`.

### 7.1 List Issues

```bash
# All issues in a project
Use list_redmine_issues with project_id=<PROJECT_ID>

# With filters
Use list_redmine_issues with project_id=<PROJECT_ID>, status_id="open", tracker_id=1, limit=20

# Pagination
Use list_redmine_issues with project_id=<PROJECT_ID>, limit=10, offset=0, include_pagination_info=true

# Assigned to me
Use list_redmine_issues with assigned_to_id="me"

# Field selection (reduce token usage)
Use list_redmine_issues with project_id=<PROJECT_ID>, fields=["id", "subject", "status", "priority"]
```

### 7.2 Get Issue Details

```bash
Use get_redmine_issue with issue_id=<ISSUE_ID>, include_journals=true, include_attachments=true, include_custom_fields=true
```

### 7.3 Create Issue

**Minimal Bug:**

```bash
Use create_redmine_issue with project_id=<PROJECT_ID>, subject="Bug title", description="Description", fields={"tracker_id": 1}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

**Full Bug with custom fields:**

```bash
Use create_redmine_issue with project_id=<PROJECT_ID>, subject="Login fails", description="Users cannot login", fields={"tracker_id": 1, "priority_id": 3, "assigned_to_id": <USER_ID>, "fixed_version_id": 10, "category_id": 5, "start_date": "2026-08-27", "due_date": "2026-09-03", "estimated_hours": 4.0}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}]}
```

**Feature/Task:**

```bash
Use create_redmine_issue with project_id=<PROJECT_ID>, subject="New feature", description="Description", fields={"tracker_id": 2}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

### 7.4 Update Issue

```bash
# Update progress
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"done_ratio": 50}

# Change status
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"status_id": 3}

# Reassign
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"assigned_to_id": <USER_ID>}

# Update custom fields
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}]}

# Add a comment
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"notes": "Working on fix"}

# With attachments
Use update_redmine_issue with issue_id=<ISSUE_ID>, fields={"notes": "Added screenshots"}, uploads=[{"token": "upload_token", "filename": "screenshot.png"}]
```

### 7.5 Search Issues

```bash
Use search_redmine_issues with query="login error", limit=20
Use search_redmine_issues with query="bug", scope="my_project", open_issues=true
```

### 7.6 Copy Issue

```bash
Use copy_issue with issue_id=<ISSUE_ID>, project_id=<PROJECT_ID>, subject="Copy of bug", link_original=true, copy_subtasks=true, copy_attachments=false
```

### 7.7 Delete Issue

```bash
# Simple delete
Use delete_redmine_issue with issue_id=<ISSUE_ID>, confirm_delete=true

# With subtasks
Use delete_redmine_issue with issue_id=<ISSUE_ID>, confirm_delete=true, confirm_delete_with_children=true
```

---

## 8. Custom Fields

Custom field IDs and allowed values are specific to **your** Redmine. Discover them with:

```bash
Use list_project_issue_custom_fields with project_id=<PROJECT_ID>
```

Then pass them via `extra_fields`, e.g. `extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}`.

**Note:** if your issue model requires fields that vary by tracker/category/status and Redmine's API does not enforce them, see Conditional Required Fields (section 19) to declare them.

---

## 9. Time Tracking

```bash
# List time entries
Use list_time_entries with project_id=<PROJECT_ID>, limit=20

# Create a time entry
Use manage_time_entry with action="create", issue_id=<ISSUE_ID>, hours=2.5, activity_id=14, spent_on="2026-08-27", comments="Fixed login bug"

# List activities
Use list_time_entry_activities
```

---

## 10. Issue Relations

```bash
# List relations
Use manage_issue_relation with action="list", issue_id=<ISSUE_ID>

# Create relation (blocks, duplicates, relates, etc.)
Use manage_issue_relation with action="create", issue_id=<ISSUE_ID>, issue_to_id=<ISSUE_ID>, relation_type="blocks"

# Delete relation
Use manage_issue_relation with action="delete", relation_id=123
```

Types: `relates`, `duplicates`, `duplicated`, `blocks`, `blocked`, `precedes`, `follows`, `copied_to`, `copied_from`

---

## 11. Watchers

```bash
Use manage_issue_watcher with action="add", issue_id=<ISSUE_ID>, user_id=<USER_ID>
Use manage_issue_watcher with action="remove", issue_id=<ISSUE_ID>, user_id=<USER_ID>
```

---

## 12. Subtasks

```bash
# List subtasks
Use list_subtasks with issue_id=<ISSUE_ID>

# Create a subtask
Use create_redmine_issue with project_id=<PROJECT_ID>, subject="Subtask", fields={"tracker_id": 1, "parent_issue_id": <ISSUE_ID>}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

---

## 13. Project Operations

```bash
Use list_redmine_projects
Use list_redmine_versions with project_id=<PROJECT_ID>
Use list_project_members with project_id=<PROJECT_ID>
Use list_project_issue_custom_fields with project_id=<PROJECT_ID>
```

---

## 14. File Operations

```bash
# Upload a file
Use upload_file with project_id=<PROJECT_ID>, filename="doc.pdf", content_base64="base64_content"

# List files
Use list_files with project_id=<PROJECT_ID>

# Download an attachment
Use get_redmine_attachment with attachment_id=123
```

---

## 15. Wiki Operations

```bash
Use manage_redmine_wiki_page with action="list", project_id=<PROJECT_ID>
Use manage_redmine_wiki_page with action="get", project_id=<PROJECT_ID>, wiki_page_title="Home"
Use manage_redmine_wiki_page with action="create", project_id=<PROJECT_ID>, wiki_page_title="NewPage", text="# New Page\nContent"
Use manage_redmine_wiki_page with action="update", project_id=<PROJECT_ID>, wiki_page_title="NewPage", text="# Updated"
Use manage_redmine_wiki_page with action="delete", project_id=<PROJECT_ID>, wiki_page_title="NewPage"
```

---

## 16. Gantt Chart

```bash
Use get_gantt_chart with project_id=<PROJECT_ID>
```

---

## 17. Common Workflows

### Workflow 1: Create Bug → Assign → Work → Log Time → Close

```
1. create_redmine_issue(project_id=<PROJECT_ID>, subject="...", fields={"tracker_id": 1}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]})
2. update_redmine_issue(issue_id=NEW_ID, fields={"assigned_to_id": "me"})
3. update_redmine_issue(issue_id=NEW_ID, fields={"status_id": 2})  # In Progress
4. manage_time_entry(action="create", issue_id=NEW_ID, hours=2.0, activity_id=14, spent_on="2026-08-27", comments="Investigation")
5. update_redmine_issue(issue_id=NEW_ID, fields={"done_ratio": 50, "notes": "Found root cause"})
6. update_redmine_issue(issue_id=NEW_ID, fields={"status_id": 5, "done_ratio": 100, "notes": "Fixed and tested"})  # Closed
```

### Workflow 2: Search → View → Update

```
1. search_redmine_issues(query="login", limit=10)
2. get_redmine_issue(issue_id=FOUND_ID, include_journals=true)
3. update_redmine_issue(issue_id=FOUND_ID, fields={"priority_id": 4}, notes="Elevated priority")
```

---

## 18. Troubleshooting

| Issue | Solution |
|-------|----------|
| "`<field>` cannot be blank" | Include that custom field in `custom_fields` (see section 8) |
| "Field not in list" | Check valid values with `list_project_issue_custom_fields` or your Redmine admin |
| "403 Forbidden" | Check the API key's permissions in Redmine |
| "Connection refused" | Verify `REDMINE_URL` and that the server is running |
| Tools not showing in stdio | Ensure `from . import tools` runs in `main.py` before the stdio check |

---

## 19. Advanced Configuration

### Read-Only Mode

```bash
REDMINE_MCP_READ_ONLY=true
```

### SSL Configuration

```bash
# Self-signed cert
REDMINE_SSL_CERT=/path/to/ca.crt

# Disable SSL verify (dev only!)
REDMINE_SSL_VERIFY=false
```

### Conditional Required Fields

This fork adds a `get_required_fields` tool and a `REDMINE_REQUIRED_FIELDS_FILE` config so you can declare required-field rules that vary by tracker / category / status. `create_redmine_issue` auto-fills declared defaults and rejects a still-missing required field with a clear message before it calls Redmine.

Create `required_fields.json` (schema in `required_fields.example.json`):

```json
{
  "by_tracker": {
    "Bug": {
      "required": ["<Required Field Name>"],
      "defaults": { "<Required Field Name>": "<VALUE>", "<Other Field>": "<VALUE>" }
    }
  }
}
```

Set: `REDMINE_REQUIRED_FIELDS_FILE=./required_fields.json`

---

## 20. Quick Command Summary

| Operation | Tool | Key Parameters |
|-----------|------|----------------|
| List issues | `list_redmine_issues` | project_id, status_id, tracker_id, assigned_to_id, limit, offset, fields |
| Get issue | `get_redmine_issue` | issue_id, include_journals, include_attachments |
| Create issue | `create_redmine_issue` | project_id, subject, description, fields, extra_fields, uploads |
| Update issue | `update_redmine_issue` | issue_id, fields, uploads |
| Search issues | `search_redmine_issues` | query, limit, scope |
| Copy issue | `copy_issue` | issue_id, project_id, subject, field_overrides |
| Delete issue | `delete_redmine_issue` | issue_id, confirm_delete |
| Time entry | `manage_time_entry` | action, issue_id, hours, activity_id, spent_on |
| Relations | `manage_issue_relation` | action, issue_id, issue_to_id, relation_type |
| Watchers | `manage_issue_watcher` | action, issue_id, user_id |
| Subtasks | `list_subtasks` | issue_id |
| Projects | `list_redmine_projects` | - |
| Versions | `list_redmine_versions` | project_id |
| Custom fields | `list_project_issue_custom_fields` | project_id |
| Wiki | `manage_redmine_wiki_page` | action, project_id, wiki_page_title, text |
| Files | `upload_file`, `list_files`, `get_redmine_attachment` | - |
| Gantt | `get_gantt_chart` | project_id |

---

## 21. Further Reading

- **Tool reference**: `docs/tool-reference.md`
- **MCP client configuration**: `docs/mcp-client-configuration.md`
- **OAuth setup**: `docs/oauth-setup.md`
- **Troubleshooting**: `docs/troubleshooting.md`
- **Differences from upstream**: see `README.md` ( Differences from upstream )

---

*Redmine MCP Server (fork) — v2.11.0*
