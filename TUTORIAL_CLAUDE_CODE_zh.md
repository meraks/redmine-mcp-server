# Redmine MCP Server 中文教程 (Claude Code)

完整指南：安装、配置和使用 **本 fork** 的 Redmine MCP Server 与 Claude Code。

> 本项目是 `jztan/redmine-mcp-server` 的一个分叉，已与原仓库偏离并独立维护。它**未**发布到 PyPI 或任何容器镜像仓库——请从预构建的 wheel 或源码安装（见下文）。所有许可与权限均与原仓库保持一致（MIT）。

---

## 前置要求

- Python 3.10+
- 可访问的 Redmine 实例（URL + API Key）
- 已安装 Claude Code

---

## 1. 安装 Redmine MCP Server

本 fork 不在 PyPI 上，因此 `uv tool install redmine-mcp-server` 会安装**上游**包，而不是本 fork。请使用以下方式之一。

### 方式 A：预构建 wheel（推荐）

从项目的 Releases 页面下载最新的 `redmine_mcp_server-*.whl`，然后：

```bash
# 安装到当前环境
pip install redmine_mcp_server-*.whl

# 或用 uv 全局安装该命令
uv tool install redmine_mcp_server-*.whl
```

### 方式 B：从源码安装

```bash
git clone <本仓库地址>
cd redmine-mcp-server

# 用 uv 安装（可编辑）
uv tool install --from . redmine-mcp-server
# 或安装到当前环境：
pip install .
```

### 方式 C：Docker（本地构建）

本 fork 不发布预构建镜像，需从源码构建：

```bash
docker build -t redmine-mcp-server .
docker run -p 8000:8000 --env-file .env.docker redmine-mcp-server
```

---

## 2. 配置环境

在项目目录下创建 `.env` 文件：

```bash
cat > .env << 'EOF'
# Redmine 连接（必需）
REDMINE_URL=http://your-redmine-server.com

# 认证 - 推荐使用 API Key
REDMINE_API_KEY=your_api_key

# 或使用用户名/密码：
# REDMINE_USERNAME=your_username
# REDMINE_PASSWORD=your_password

# 服务器配置（可选，显示默认值）
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 文件服务公网地址（可选）
PUBLIC_HOST=localhost
PUBLIC_PORT=8000

# 文件管理（可选）
ATTACHMENTS_DIR=./attachments
AUTO_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=10
ATTACHMENT_EXPIRES_MINUTES=60
EOF
```

**获取 API Key**：Redmine → 我的账户 → API 访问密钥 → 显示

---

## 3. 两种传输模式

| 模式 | 命令 | 适用场景 |
|------|------|----------|
| **stdio（推荐用于本地）** | `redmine-mcp-server --stdio` | 本地 Claude Code，无需网络 |
| **HTTP** | `redmine-mcp-server` | 远程部署、Docker、多客户端共享 |

### stdio 模式（推荐）

```bash
# 直接以 stdio 传输运行
redmine-mcp-server --stdio
```

### HTTP 模式（远程/多客户端）

```bash
# 启动服务
redmine-mcp-server

# 验证
curl http://localhost:8000/health
```

---

## 4. 配置 Claude Code

### stdio 模式（推荐用于本地）

```bash
claude mcp add redmine -- redmine-mcp-server --stdio
```

或手动编辑 `~/.claude.json`：

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

### HTTP 模式（远程/共享服务器）

```bash
claude mcp add --transport http redmine http://localhost:8000/mcp
```

或手动编辑 `~/.claude.json`：

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

**如果使用本地源码配合 uv：**

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

重启 Claude Code 以加载服务器。

---

## 5. 验证连接

在 Claude Code 中：

```
> 使用 get_mcp_server_info 工具检查服务器状态
```

预期响应：

```json
{
  "version": "2.11.0",
  "auth_mode": "legacy",
  "read_only": false,
  "current_user": {"id": 1, "name": "Your Name"}
}
```

---

## 6. 所有可用工具（共 42 个核心工具）

本 fork 提供 42 个核心 MCP 工具（另有 1 个由 `REDMINE_MCP_EXPOSE_ADMIN_TOOLS=true` 暴露的运维工具）。上游的可选插件工具（Checklists、Products、CRM/Contacts、DMSF Documents）以及 MCP Apps UI **未包含**在本 fork 中。

### 问题操作（13 个）

| 工具 | 说明 |
|------|------|
| `get_redmine_issue` | 获取问题详情，含日志、附件、自定义字段 |
| `list_redmine_issues` | 列出问题，支持过滤、分页、字段选择 |
| `search_redmine_issues` | 全文搜索问题 |
| `create_redmine_issue` | 创建新问题 |
| `update_redmine_issue` | 更新现有问题 |
| `delete_redmine_issue` | 硬删除（需确认） |
| `copy_issue` | 复制问题 |
| `list_subtasks` | 列出子任务 |
| `manage_issue_relation` | 列出/创建/删除问题关联 |
| `manage_issue_watcher` | 添加/移除关注者 |
| `manage_issue_note` | 编辑/切换日志备注隐私 |
| `get_private_notes` | 仅获取私有备注 |
| `manage_issue_category` | 管理问题分类 |

### 项目操作（9 个）

| 工具 | 说明 |
|------|------|
| `list_redmine_projects` | 列出所有可访问项目 |
| `list_project_issue_custom_fields` | 列出项目的自定义字段 |
| `list_redmine_versions` | 列出版本/里程碑 |
| `manage_redmine_version` | 创建/更新/删除版本 |
| `list_project_members` | 列出项目成员和角色 |
| `summarize_project_status` | 项目状态综合摘要 |
| `list_redmine_roles` | 列出所有角色 |
| `get_project_modules` | 获取启用的模块 |
| `manage_project_member` | 添加/更新/移除项目成员 |

### 时间跟踪（4 个）

| 工具 | 说明 |
|------|------|
| `list_time_entries` | 列出工时记录（支持过滤） |
| `manage_time_entry` | 创建/更新工时记录 |
| `list_time_entry_activities` | 列出可用活动类型 |
| `import_time_entries` | 批量导入工时记录 |

### 发现/枚举（8 个）

| 工具 | 说明 |
|------|------|
| `list_redmine_trackers` | 列出所有追踪器 |
| `list_project_trackers` | 列出项目的追踪器 |
| `list_redmine_issue_statuses` | 列出所有状态（含 is_closed） |
| `list_redmine_issue_priorities` | 列出所有优先级 |
| `list_redmine_users` | 过滤/列出用户（仅管理员） |
| `get_current_user` | 获取当前认证用户信息 |
| `list_redmine_queries` | 列出保存的自定义查询 |
| `get_required_fields` | 获取条件必填字段规则 |

### 搜索与 Wiki（2 个）

| 工具 | 说明 |
|------|------|
| `search_entire_redmine` | 全局搜索（问题 + Wiki） |
| `manage_redmine_wiki_page` | 列出/获取/创建/更新/删除/重命名 Wiki 页面 |

### 文件操作（4 个）

| 工具 | 说明 |
|------|------|
| `list_files` | 列出项目文件 |
| `upload_file` | 上传文件 |
| `delete_file` | 删除项目文件 |
| `get_redmine_attachment` | 下载附件 |

### 甘特图（1 个）

| 工具 | 说明 |
|------|------|
| `get_gantt_chart` | 项目时间线（日期、依赖、里程碑） |

### 元信息（1 个）

| 工具 | 说明 |
|------|------|
| `get_mcp_server_info` | 服务器版本、认证模式、当前用户 |

---

## 7. 常用命令参考

> 请将下列占位符替换为**你的** Redmine 中的值：
> `<PROJECT_ID>`、`<ISSUE_ID>`、`<USER_ID>`、`<CF_ID>`（自定义字段 ID）、`<VALUE>`。

### 7.1 列出问题

```bash
# 项目所有问题
使用 list_redmine_issues，project_id=<PROJECT_ID>

# 带过滤
使用 list_redmine_issues，project_id=<PROJECT_ID>, status_id="open", tracker_id=1, limit=20

# 分页
使用 list_redmine_issues，project_id=<PROJECT_ID>, limit=10, offset=0, include_pagination_info=true

# 分配给我
使用 list_redmine_issues，assigned_to_id="me"

# 字段选择（减少 token）
使用 list_redmine_issues，project_id=<PROJECT_ID>, fields=["id", "subject", "status", "priority"]
```

### 7.2 获取问题详情

```bash
使用 get_redmine_issue，issue_id=<ISSUE_ID>, include_journals=true, include_attachments=true, include_custom_fields=true
```

### 7.3 创建问题

**最小化 Bug：**

```bash
使用 create_redmine_issue，project_id=<PROJECT_ID>, subject="Bug标题", description="描述", fields={"tracker_id": 1}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

**完整 Bug（含自定义字段）：**

```bash
使用 create_redmine_issue，project_id=<PROJECT_ID>, subject="登录失败", description="用户无法登录", fields={"tracker_id": 1, "priority_id": 3, "assigned_to_id": <USER_ID>, "fixed_version_id": 10, "category_id": 5, "start_date": "2026-08-27", "due_date": "2026-09-03", "estimated_hours": 4.0}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}]}
```

**Feature/Task：**

```bash
使用 create_redmine_issue，project_id=<PROJECT_ID>, subject="新功能", description="描述", fields={"tracker_id": 2}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

### 7.4 更新问题

```bash
# 更新进度
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"done_ratio": 50}

# 更改状态
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"status_id": 3}

# 重新分配
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"assigned_to_id": <USER_ID>}

# 更新自定义字段
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}, {"id": <CF_ID>, "value": "<VALUE>"}]}

# 添加备注
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"notes": "正在修复"}

# 带附件
使用 update_redmine_issue，issue_id=<ISSUE_ID>, fields={"notes": "添加截图"}, uploads=[{"token": "upload_token", "filename": "screenshot.png"}]
```

### 7.5 搜索问题

```bash
使用 search_redmine_issues，query="登录错误", limit=20
使用 search_redmine_issues，query="bug", scope="my_project", open_issues=true
```

### 7.6 复制问题

```bash
使用 copy_issue，issue_id=<ISSUE_ID>, project_id=<PROJECT_ID>, subject="Bug副本", link_original=true, copy_subtasks=true, copy_attachments=false
```

### 7.7 删除问题

```bash
# 简单删除
使用 delete_redmine_issue，issue_id=<ISSUE_ID>, confirm_delete=true

# 有子任务时
使用 delete_redmine_issue，issue_id=<ISSUE_ID>, confirm_delete=true, confirm_delete_with_children=true
```

---

## 8. 自定义字段

自定义字段的 ID 与可选值取决于**你的** Redmine。用以下命令查询：

```bash
使用 list_project_issue_custom_fields，project_id=<PROJECT_ID>
```

然后通过 `extra_fields` 传入，例如 `extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}`。

**注意：** 如果你的 issue 模型存在随 tracker/分类/状态变化的必填字段，而 Redmine API 未强制校验，参见第 19 节「条件必填字段」进行声明。

---

## 9. 时间跟踪

```bash
# 列出工时记录
使用 list_time_entries，project_id=<PROJECT_ID>, limit=20

# 创建工时记录
使用 manage_time_entry，action="create", issue_id=<ISSUE_ID>, hours=2.5, activity_id=14, spent_on="2026-08-27", comments="修复登录Bug"

# 列出活动类型
使用 list_time_entry_activities
```

---

## 10. 问题关联

```bash
# 列出关联
使用 manage_issue_relation，action="list", issue_id=<ISSUE_ID>

# 创建关联
使用 manage_issue_relation，action="create", issue_id=<ISSUE_ID>, issue_to_id=<ISSUE_ID>, relation_type="blocks"

# 删除关联
使用 manage_issue_relation，action="delete", relation_id=123
```

类型：`relates`, `duplicates`, `duplicated`, `blocks`, `blocked`, `precedes`, `follows`, `copied_to`, `copied_from`

---

## 11. 关注者

```bash
使用 manage_issue_watcher，action="add", issue_id=<ISSUE_ID>, user_id=<USER_ID>
使用 manage_issue_watcher，action="remove", issue_id=<ISSUE_ID>, user_id=<USER_ID>
```

---

## 12. 子任务

```bash
# 列出子任务
使用 list_subtasks，issue_id=<ISSUE_ID>

# 创建子任务
使用 create_redmine_issue，project_id=<PROJECT_ID>, subject="子任务", fields={"tracker_id": 1, "parent_issue_id": <ISSUE_ID>}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]}
```

---

## 13. 项目操作

```bash
使用 list_redmine_projects
使用 list_redmine_versions，project_id=<PROJECT_ID>
使用 list_project_members，project_id=<PROJECT_ID>
使用 list_project_issue_custom_fields，project_id=<PROJECT_ID>
```

---

## 14. 文件操作

```bash
# 上传文件
使用 upload_file，project_id=<PROJECT_ID>, filename="doc.pdf", content_base64="base64内容"

# 列出文件
使用 list_files，project_id=<PROJECT_ID>

# 下载附件
使用 get_redmine_attachment，attachment_id=123
```

---

## 15. Wiki 操作

```bash
使用 manage_redmine_wiki_page，action="list", project_id=<PROJECT_ID>
使用 manage_redmine_wiki_page，action="get", project_id=<PROJECT_ID>, wiki_page_title="Home"
使用 manage_redmine_wiki_page，action="create", project_id=<PROJECT_ID>, wiki_page_title="NewPage", text="# New Page\nContent"
使用 manage_redmine_wiki_page，action="update", project_id=<PROJECT_ID>, wiki_page_title="NewPage", text="# Updated"
使用 manage_redmine_wiki_page，action="delete", project_id=<PROJECT_ID>, wiki_page_title="NewPage"
```

---

## 16. 甘特图

```bash
使用 get_gantt_chart，project_id=<PROJECT_ID>
```

---

## 17. 常用工作流

### 工作流 1：创建 Bug → 分配 → 工作 → 记录工时 → 关闭

```
1. create_redmine_issue(project_id=<PROJECT_ID>, subject="...", fields={"tracker_id": 1}, extra_fields={"custom_fields": [{"id": <CF_ID>, "value": "<VALUE>"}]})
2. update_redmine_issue(issue_id=NEW_ID, fields={"assigned_to_id": "me"})
3. update_redmine_issue(issue_id=NEW_ID, fields={"status_id": 2})  # 进行中
4. manage_time_entry(action="create", issue_id=NEW_ID, hours=2.0, activity_id=14, spent_on="2026-08-27", comments="调查")
5. update_redmine_issue(issue_id=NEW_ID, fields={"done_ratio": 50, "notes": "找到根因"})
6. update_redmine_issue(issue_id=NEW_ID, fields={"status_id": 5, "done_ratio": 100, "notes": "已修复并测试"})  # 已关闭
```

### 工作流 2：搜索 → 查看 → 更新

```
1. search_redmine_issues(query="login", limit=10)
2. get_redmine_issue(issue_id=FOUND_ID, include_journals=true)
3. update_redmine_issue(issue_id=FOUND_ID, fields={"priority_id": 4}, notes="提升优先级")
```

---

## 18. 故障排除

| 问题 | 解决方案 |
|------|----------|
| "`<field>` cannot be blank" | 在 `custom_fields` 中包含该自定义字段（见第 8 节） |
| "Field not in list" | 用 `list_project_issue_custom_fields` 或咨询 Redmine 管理员获取有效值 |
| "403 Forbidden" | 检查 Redmine 中 API Key 的权限 |
| "Connection refused" | 验证 `REDMINE_URL` 和服务器运行状态 |
| stdio 模式工具不显示 | 确保 `main.py` 中 `from . import tools` 在 stdio 检查之前执行 |

---

## 19. 高级配置

### 只读模式

```bash
REDMINE_MCP_READ_ONLY=true
```

### SSL 配置

```bash
# 自签名证书
REDMINE_SSL_CERT=/path/to/ca.crt

# 禁用 SSL 验证（仅开发环境！）
REDMINE_SSL_VERIFY=false
```

### 条件必填字段

本 fork 新增了 `get_required_fields` 工具以及 `REDMINE_REQUIRED_FIELDS_FILE` 配置，用于声明随 tracker/分类/状态变化的必填字段规则。`create_redmine_issue` 会自动填充声明的默认值，并在调用 Redmine 前对仍缺失的必填字段给出明确报错。

创建 `required_fields.json`（格式见 `required_fields.example.json`）：

```json
{
  "by_tracker": {
    "Bug": {
      "required": ["<必填字段名>"],
      "defaults": { "<必填字段名>": "<VALUE>", "<其他字段>": "<VALUE>" }
    }
  }
}
```

设置：`REDMINE_REQUIRED_FIELDS_FILE=./required_fields.json`

---

## 20. 命令快速总结

| 操作 | 工具 | 关键参数 |
|------|------|----------|
| 列出问题 | `list_redmine_issues` | project_id, status_id, tracker_id, assigned_to_id, limit, offset, fields |
| 获取问题 | `get_redmine_issue` | issue_id, include_journals, include_attachments |
| 创建问题 | `create_redmine_issue` | project_id, subject, description, fields, extra_fields, uploads |
| 更新问题 | `update_redmine_issue` | issue_id, fields, uploads |
| 搜索问题 | `search_redmine_issues` | query, limit, scope |
| 复制问题 | `copy_issue` | issue_id, project_id, subject, field_overrides |
| 删除问题 | `delete_redmine_issue` | issue_id, confirm_delete |
| 工时记录 | `manage_time_entry` | action, issue_id, hours, activity_id, spent_on |
| 问题关联 | `manage_issue_relation` | action, issue_id, issue_to_id, relation_type |
| 关注者 | `manage_issue_watcher` | action, issue_id, user_id |
| 子任务 | `list_subtasks` | issue_id |
| 项目列表 | `list_redmine_projects` | - |
| 版本列表 | `list_redmine_versions` | project_id |
| 自定义字段 | `list_project_issue_custom_fields` | project_id |
| Wiki | `manage_redmine_wiki_page` | action, project_id, wiki_page_title, text |
| 文件 | `upload_file`, `list_files`, `get_redmine_attachment` | - |
| 甘特图 | `get_gantt_chart` | project_id |

---

## 21. 进一步阅读

- **工具参考**：`docs/tool-reference.md`
- **MCP 客户端配置**：`docs/mcp-client-configuration.md`
- **OAuth 设置**：`docs/oauth-setup.md`
- **故障排除**：`docs/troubleshooting.md`
- **与原仓库的差异**：见 `README.md`（Differences from upstream 一节）

---

*Redmine MCP Server（fork）— v2.11.0*
