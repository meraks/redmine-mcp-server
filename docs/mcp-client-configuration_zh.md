# MCP 客户端配置指南（中文）

本指南介绍如何配置各类 MCP 客户端以使用 Redmine MCP Server。

---

## 传输模式

Redmine MCP Server 支持两种传输模式：

| 模式 | 命令 | 适用场景 |
|------|------|----------|
| **stdio** | `redmine-mcp-server --stdio` | 本地客户端 - 推荐用于本地开发 |
| **HTTP** | `redmine-mcp-server` | 远程部署、Docker、多客户端共享、网络访问 |

---

## 快速开始：环境配置

创建 `.env` 文件并填入 Redmine 凭据：

```bash
cat > .env << 'EOF'
REDMINE_URL=http://your-redmine-server.com
REDMINE_API_KEY=your_api_key_here
# 或使用用户名/密码：
# REDMINE_USERNAME=your_username
# REDMINE_PASSWORD=your_password
EOF
```

---

## 客户端配置详解

### 1. Claude Code（推荐：stdio 模式）

```bash
# 方案 A：CLI 一键配置（最简单）
claude mcp add redmine -- redmine-mcp-server --stdio

# 方案 B：带显式环境变量
claude mcp add redmine -- redmine-mcp-server --stdio \
  --env REDMINE_URL=http://your-redmine.com \
  --env REDMINE_API_KEY=your_key

# 方案 C：手动编辑 ~/.claude.json
{
  "mcpServers": {
    "redmine": {
      "command": "redmine-mcp-server",
      "args": ["--stdio"],
      "env": {
        "REDMINE_URL": "http://your-redmine.com",
        "REDMINE_API_KEY": "your_key"
      }
    }
  }
}
```

### 2. Claude Desktop（需 HTTP + 桥接）

Claude Desktop 仅支持 stdio 传输，需使用 FastMCP 桥接：

**macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**：`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "redmine": {
      "command": "uv",
      "args": [
        "run",
        "--with", "fastmcp",
        "fastmcp",
        "run",
        "http://localhost:8000/mcp"
      ]
    }
  }
}
```

**前置步骤：**
1. 先启动 HTTP 服务：`redmine-mcp-server`（运行在 localhost:8000）
2. 安装 uv：`pip install uv`
3. 完全重启 Claude Desktop

### 3. VS Code（原生支持 HTTP）

**使用 CLI：**
```bash
code --add-mcp '{"name":"redmine","type":"http","url":"http://localhost:8000/mcp"}'
```

**使用命令面板：**
1. `Cmd/Ctrl+Shift+P` → `MCP: Open User Configuration`
2. 添加：
```json
{
  "servers": {
    "redmine": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**手动创建 `.vscode/mcp.json`（工作区级）：**
```json
{
  "servers": {
    "redmine": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 4. Cursor（原生支持 HTTP）

创建 `~/.cursor/mcp.json`（全局）或 `.cursor/mcp.json`（项目级）：

```json
{
  "mcpServers": {
    "redmine": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**OAuth 模式下**，需在服务器 `.env` 添加：
```
REDMINE_OAUTH_DISCOVERY_AS=self
```

### 5. Codex CLI

```bash
codex mcp add redmine -- npx -y mcp-client-http http://localhost:8000/mcp
```

或 `~/.codex/config.toml`：
```toml
[mcp_servers.redmine]
command = "npx"
args = ["-y", "mcp-client-http", "http://localhost:8000/mcp"]
```

### 6. Kiro

`.kiro/settings/mcp.json`：
```json
{
  "mcpServers": {
    "redmine": {
      "command": "npx",
      "args": ["-y", "mcp-client-http", "http://localhost:8000/mcp"],
      "disabled": false
    }
  }
}
```

### 7. 通用 MCP 客户端（HTTP）

标准配置：
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

带 HTTP 桥接（仅支持 stdio 的客户端）：
```json
{
  "mcpServers": {
    "redmine": {
      "command": "npx",
      "args": ["-y", "mcp-client-http", "http://localhost:8000/mcp"]
    }
  }
}
```

---

## Docker 部署

### 使用 docker-compose
```bash
cp .env.docker.example .env.docker
# 编辑 .env.docker
docker-compose up --build
```

### 使用预构建镜像
```bash
docker pull ghcr.io/jztan/redmine-mcp-server:latest
docker run -p 8000:8000 --env-file .env.docker ghcr.io/jztan/redmine-mcp-server:latest
```

客户端连接 `http://localhost:8000/mcp`（或服务器 IP）。

---

## 生产环境部署

```bash
chmod +x deploy.sh
./deploy.sh
```

自动配置 systemd 服务、nginx 反向代理和 SSL。

---

## 认证模式

| 模式 | 环境变量 | 要求 | 适用场景 |
|------|----------|------|----------|
| **legacy**（默认） | `REDMINE_AUTH_MODE=legacy` | API Key 或用户/密码 | 单一共享凭据 |
| **oauth** | `REDMINE_AUTH_MODE=oauth` | Redmine 6.1+、Doorkeeper 应用 | 多用户、各自 Token |
| **oauth-proxy** | `REDMINE_AUTH_MODE=oauth-proxy` | Redmine 6.1+、JWT 密钥 | 托管部署、客户端自注册 |
| **legacy-per-user** | `REDMINE_AUTH_MODE=legacy-per-user` | TLS、反向代理 | 多用户、旧版 Redmine |

### Legacy 模式（最简单）
```bash
REDMINE_AUTH_MODE=legacy
REDMINE_API_KEY=your_key
# 或
REDMINE_USERNAME=user
REDMINE_PASSWORD=pass
```

### OAuth 模式（多用户）
```bash
REDMINE_AUTH_MODE=oauth
REDMINE_URL=https://redmine.example.com
REDMINE_MCP_BASE_URL=https://your-mcp-server.com
REDMINE_INTROSPECT_CLIENT_ID=xxx
REDMINE_INTROSPECT_CLIENT_SECRET=xxx
```

---

## 故障排除

### 服务器无法启动
```bash
# 检查 .env 是否存在且正确
cat .env

# 手动测试连接
curl -H "X-Redmine-API-Key: your_key" http://your-redmine.com/projects.json
```

### 工具不显示
- 确保服务器运行：`curl http://localhost:8000/health`
- stdio 模式：检查客户端日志中的初始化错误
- HTTP 模式：验证 `/mcp` 端点返回 200

### "Connection refused"
- HTTP 模式：客户端连接前服务器必须已运行
- 检查防火墙/端口 8000
- 确认 `SERVER_HOST=0.0.0.0` 允许外部访问

### SSL/证书错误
```bash
# 自签名证书
REDMINE_SSL_CERT=/path/to/ca.crt

# 禁用验证（仅开发环境！）
REDMINE_SSL_VERIFY=false
```

---

## 环境变量完整参考

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `REDMINE_URL` | 是 | - | Redmine 基础 URL |
| `REDMINE_API_KEY` | 是* | - | API Key (legacy 模式) |
| `REDMINE_USERNAME` | 是* | - | 用户名 (legacy 模式) |
| `REDMINE_PASSWORD` | 是* | - | 密码 (legacy 模式) |
| `REDMINE_AUTH_MODE` | 否 | `legacy` | 认证模式 |
| `SERVER_HOST` | 否 | `0.0.0.0` | 绑定地址 |
| `SERVER_PORT` | 否 | `8000` | 端口 |
| `REDMINE_MCP_READ_ONLY` | 否 | `false` | 禁用写操作 |
| `REDMINE_SSL_VERIFY` | 否 | `true` | SSL 验证 |
| `REDMINE_SSL_CERT` | 否 | - | 自定义 CA 证书路径 |
| `ATTACHMENTS_DIR` | 否 | `./attachments` | 附件存储目录 |
| `REDMINE_REQUIRED_FIELDS_FILE` | 否 | `./required_fields.json` | 条件必填字段配置 |

*legacy 模式下二选一：API Key 或 用户名+密码。

---

## 测试配置

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试 MCP 端点（需有效会话）
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

---

## 快速对照表

| 客户端 | 配置方式 | 传输模式 |
|--------|----------|----------|
| **Claude Code** | `claude mcp add redmine -- redmine-mcp-server --stdio` | stdio |
| **Claude Desktop** | FastMCP 桥接 `uv run fastmcp run http://localhost:8000/mcp` | HTTP→stdio |
| **VS Code** | `code --add-mcp '{"name":"redmine","type":"http","url":"http://localhost:8000/mcp"}'` | HTTP |
| **Cursor** | `~/.cursor/mcp.json` 配置 `{"url": "http://localhost:8000/mcp"}` | HTTP |
| **Codex CLI** | `codex mcp add redmine -- npx -y mcp-client-http http://localhost:8000/mcp` | HTTP |
| **Kiro** | `.kiro/settings/mcp.json` 配置 npx 桥接 | HTTP |
| **通用客户端** | 标准 HTTP 或 npx 桥接 | HTTP |

**关键文件：**
- `.env` - Redmine 凭据（所有模式必需）
- `redmine-mcp-server --stdio` - 用于 stdio 客户端
- `redmine-mcp-server` - 用于 HTTP 客户端、Docker

---

## 技术支持

- **GitHub**: https://github.com/jztan/redmine-mcp-server
- **Issues**: https://github.com/jztan/redmine-mcp-server/issues
- **OAuth 设置**: 见 `docs/oauth-setup.md`
- **Legacy Per-User 认证**: 见 `docs/legacy-per-user-auth.md`
- **故障排除**: 见 `docs/troubleshooting.md`
- **中文教程**: 见 `TUTORIAL_CLAUDE_CODE_zh.md`