# MCP Client Configuration Guide

This guide covers how to configure various MCP clients to use the Redmine MCP Server.

---

## Transport Modes

The Redmine MCP Server supports two transport modes:

| Mode | Command | Use Case |
|------|---------|----------|
| **stdio** | `redmine-mcp-server --stdio` | Local clients (Claude Code, Claude Desktop, VS Code, Cursor) |
| **HTTP** | `redmine-mcp-server` | Remote servers, Docker, multiple clients, network access |

---

## Quick Start: Environment Setup

Create `.env` file with your Redmine credentials:

```bash
cat > .env << 'EOF'
REDMINE_URL=http://your-redmine-server.com
REDMINE_API_KEY=your_api_key_here
# Or use username/password:
# REDMINE_USERNAME=your_username
# REDMINE_PASSWORD=your_password
EOF
```

---

## Client Configurations

### 1. Claude Code (Recommended: stdio)

```bash
# Option A: CLI (easiest)
claude mcp add redmine -- redmine-mcp-server --stdio

# Option B: With explicit env vars
claude mcp add redmine -- redmine-mcp-server --stdio \
  --env REDMINE_URL=http://your-redmine.com \
  --env REDMINE_API_KEY=your_key

# Option C: Manual ~/.claude.json
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

### 2. Claude Desktop (Requires HTTP + bridge)

Claude Desktop only supports stdio transport. Use FastMCP's bridge:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

**Prerequisites:**
1. Start HTTP server first: `redmine-mcp-server` (runs on localhost:8000)
2. Install uv: `pip install uv`
3. Restart Claude Desktop completely

### 3. VS Code (Native HTTP Support)

**Using CLI:**
```bash
code --add-mcp '{"name":"redmine","type":"http","url":"http://localhost:8000/mcp"}'
```

**Using Command Palette:**
1. `Cmd/Ctrl+Shift+P` → `MCP: Open User Configuration`
2. Add:
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

**Manual `.vscode/mcp.json` (workspace):**
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

### 4. Cursor (Native HTTP Support)

Create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "redmine": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**For OAuth mode**, add to server `.env`:
```
REDMINE_OAUTH_DISCOVERY_AS=self
```

### 5. Codex CLI

```bash
codex mcp add redmine -- npx -y mcp-client-http http://localhost:8000/mcp
```

Or `~/.codex/config.toml`:
```toml
[mcp_servers.redmine]
command = "npx"
args = ["-y", "mcp-client-http", "http://localhost:8000/mcp"]
```

### 6. Kiro

`.kiro/settings/mcp.json`:
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

### 7. Generic MCP Clients (HTTP)

Standard configuration:
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

With HTTP bridge (for stdio-only clients):
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

## Docker Deployment

### Using docker-compose
```bash
cp .env.docker.example .env.docker
# Edit .env.docker with your settings
docker-compose up --build
```

### Building locally (this fork is not published to GHCR)
```bash
docker build -t redmine-mcp-server .
docker run -p 8000:8000 --env-file .env.docker redmine-mcp-server
```

Then connect clients to `http://localhost:8000/mcp` (or your server's IP).

---

## Production Deployment

```bash
chmod +x deploy.sh
./deploy.sh
```

This sets up systemd service, nginx reverse proxy, and SSL.

---

## Authentication Modes

| Mode | Env Var | Requirements | Best For |
|------|---------|--------------|----------|
| **legacy** (default) | `REDMINE_AUTH_MODE=legacy` | API key or user/pass | Single shared credential |
| **oauth** | `REDMINE_AUTH_MODE=oauth` | Redmine 6.1+, Doorkeeper app | Multi-user, per-user tokens |
| **oauth-proxy** | `REDMINE_AUTH_MODE=oauth-proxy` | Redmine 6.1+, JWT key | Hosted, client self-registration |
| **legacy-per-user** | `REDMINE_AUTH_MODE=legacy-per-user` | TLS, reverse proxy | Multi-user, older Redmine |

### Legacy Mode (Simplest)
```bash
REDMINE_AUTH_MODE=legacy
REDMINE_API_KEY=your_key
# OR
REDMINE_USERNAME=user
REDMINE_PASSWORD=pass
```

### OAuth Mode (Multi-user)
```bash
REDMINE_AUTH_MODE=oauth
REDMINE_URL=https://redmine.example.com
REDMINE_MCP_BASE_URL=https://your-mcp-server.com
REDMINE_INTROSPECT_CLIENT_ID=xxx
REDMINE_INTROSPECT_CLIENT_SECRET=xxx
```

---

## Troubleshooting

### Server won't start
```bash
# Check .env exists and has correct values
cat .env

# Test connection manually
curl -H "X-Redmine-API-Key: your_key" http://your-redmine.com/projects.json
```

### Tools not appearing
- Ensure server is running: `curl http://localhost:8000/health`
- For stdio: Check client logs for initialization errors
- For HTTP: Verify `/mcp` endpoint returns 200

### "Connection refused"
- HTTP mode: Server must be running before client connects
- Check firewall/port 8000
- Verify `SERVER_HOST=0.0.0.0` for external access

### SSL/Certificate errors
```bash
# Self-signed cert
REDMINE_SSL_CERT=/path/to/ca.crt

# Disable verify (dev only!)
REDMINE_SSL_VERIFY=false
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDMINE_URL` | Yes | - | Redmine base URL |
| `REDMINE_API_KEY` | Yes* | - | API key (legacy mode) |
| `REDMINE_USERNAME` | Yes* | - | Username (legacy mode) |
| `REDMINE_PASSWORD` | Yes* | - | Password (legacy mode) |
| `REDMINE_AUTH_MODE` | No | `legacy` | Auth mode |
| `SERVER_HOST` | No | `0.0.0.0` | Bind address |
| `SERVER_PORT` | No | `8000` | Port |
| `REDMINE_MCP_READ_ONLY` | No | `false` | Block write operations |
| `REDMINE_SSL_VERIFY` | No | `true` | SSL verification |
| `REDMINE_SSL_CERT` | No | - | Custom CA cert path |
| `ATTACHMENTS_DIR` | No | `./attachments` | Attachment storage |
| `REDMINE_REQUIRED_FIELDS_FILE` | No | `./required_fields.json` | Conditional required fields |

*Either API key or username+password required for legacy mode.

---

## Testing Your Setup

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test MCP endpoint (requires valid session)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

---

## Support

- **GitHub**: https://github.com/meraks/redmine-mcp-server
- **Issues**: https://github.com/meraks/redmine-mcp-server/issues
- **OAuth Setup**: See `docs/oauth-setup.md`
- **Legacy Per-User Auth**: See `docs/legacy-per-user-auth.md`
- **Troubleshooting**: See `docs/troubleshooting.md`