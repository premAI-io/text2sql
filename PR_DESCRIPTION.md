## Summary

This PR addresses security vulnerabilities (#40), fixes dependency conflicts (#37), and adds new features for better model support and deployment experience.

---

## Dependency Fixes (Issue #37)

Fixed version conflicts reported during installation:

| Conflict                                                | Cause                              | Resolution               |
| ------------------------------------------------------- | ---------------------------------- | ------------------------ |
| `httpx<0.29` vs `>=0.27` required by ollama/browser-use | fastapi 0.112 pinned old httpx     | Update fastapi >=0.115.0 |
| `starlette>=0.41.3` vs 0.38.6                           | fastapi 0.112 pinned old starlette | Update fastapi >=0.115.0 |
| `python==3.12 not compatible`                           | Version range `^3.10`              | Extend to `>=3.10,<3.13` |

**Changes in pyproject.toml:**

```toml
# Before
python = "^3.10"
fastapi = "^0.112.0"

# After
python = ">=3.10,<3.13"  # Support 3.11, 3.12
fastapi = ">=0.115.0"    # Brings httpx>=0.27, starlette>=0.41
httpx = ">=0.27.0"       # Explicit for clarity
starlette = ">=0.41.0"   # Explicit for clarity
```

---

## Security Fixes (Issue #40)

### Critical Severity
- **RCE via eval()** → Replace with `ast.literal_eval()`
- **SSRF** → `normalize_base_url()` restricts to loopback addresses
- **Missing Authentication** → Token-based auth via `PREMSQL_API_TOKEN`

### High Severity
- **SQL Write Operations** → `enforce_read_only_sql()` blocks INSERT/UPDATE/DELETE/DROP
- **Path Traversal** → Whitelist validation: `[A-Za-z0-9_-]{1,64}`
- **Information Disclosure** → Removed sensitive fields from API responses
- **Error Message Leakage** → `safe_error_message()` whitelist mechanism

### Medium Severity
- **Pickle RCE** → Add `weights_only=True` to `torch.load()`
- **Swagger Exposure** → Restrict access based on DEBUG mode
- **Process Management** → PID file-based precise process tracking
- **SQL Injection** → Parameterized queries with `?` placeholders

---

## New Features

### 1. LLM Provider Support

Added new generators for self-hosted and custom LLM deployments:

| Generator                           | Use Case                                                 |
| ----------------------------------- | -------------------------------------------------------- |
| `Text2SQLGeneratorVLLM`             | vLLM deployed models (auto Qwen3 thinking mode handling) |
| `Text2SQLGeneratorOpenAICompatible` | Any OpenAI-compatible API (LM Studio, LocalAI, etc.)     |

**Usage:**
```python
from premsql.generators import Text2SQLGeneratorVLLM

generator = Text2SQLGeneratorVLLM(
    model_name="/models/qwen",
    base_url="http://localhost:8000/v1",
    experiment_name="test", type="test"
)
```

### 2. Easy Deployment Script

Added `start_agent.py` for one-command AgentServer startup:

```bash
# Configure in .env, then:
python start_agent.py
```

Auto-detects configured LLM provider from environment variables.

### 3. Bug Fixes

| Fix                     | Description                                                                    |
| ----------------------- | ------------------------------------------------------------------------------ |
| Plot image generation   | Fixed `plot_image=False` hardcoded in server_mode, now generates base64 images |
| Matplotlib backend      | Added `Agg` backend for non-interactive server mode                            |
| Session duplicate error | Auto-delete existing session when creating new one with same name              |
| Session deletion memory | Recreate memory DB table after deletion to prevent OperationalError            |
| API token propagation   | Fixed Django backend not passing API token to AgentServer                      |
| Environment loading     | Added dotenv loading in Django manage.py and Streamlit main.py                 |

### 4. UI Improvements

- Session list now shows delete button for each session (no need to type session name)
- Delete operation auto-refreshes the page
- Simplified session creation form with placeholder hints

---

## Configuration

### Environment Variables (.env)

All configuration is optional for local development - tokens are auto-generated if not set.

```bash
# Security (auto-generated for local dev)
#PREMSQL_API_TOKEN=your-token-here
#PREMSQL_DJANGO_SECRET_KEY=your-secret-here

# LLM Provider (choose one)
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=/models/your-model

# Or custom OpenAI-compatible service
CUSTOM_BASE_URL=http://localhost:1234/v1
CUSTOM_MODEL_NAME=local-model

# Or official OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL_NAME=gpt-4o-mini
```

### Quick Start

```bash
# 1. Copy and configure .env
cp .env.example .env
# Edit .env to set your LLM provider

# 2. Start services
python start_agent.py          # AgentServer on port 8100
premsql launch all             # Django + Streamlit

# 3. Open browser
http://localhost:8501          # PremSQL Playground
```

---

## Security Configuration

### Development Mode (Recommended for Local Testing)

Set `PREMSQL_DJANGO_DEBUG=true` to enable development mode:

```bash
# .env for development
PREMSQL_DJANGO_DEBUG=true
# No need to set PREMSQL_API_TOKEN - auto-generated
```

In development mode:
- API token is auto-generated (printed in startup logs)
- Authentication is skipped for all services
- Suitable for local testing only

### Production Mode (Required for Deployment)

**IMPORTANT**: Production mode requires explicit token configuration:

```bash
# .env for production
PREMSQL_DJANGO_DEBUG=false
PREMSQL_API_TOKEN=<your-strong-random-token>  # REQUIRED!
PREMSQL_DJANGO_SECRET_KEY=<your-strong-random-secret>
```

**How to generate secure tokens:**

```bash
# Using Python (recommended)
python -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32

# Using UUID
python -c "import uuid; print(uuid.uuid4().hex)"
```

Example output: `a1b2c3d4e5f6...` (64 characters hex string)

**Security behavior summary:**

| Mode        | PREMSQL_API_TOKEN | Behavior                     |
| ----------- | ----------------- | ---------------------------- |
| Development | Not set           | Auto-generated, auth skipped |
| Development | Set               | Use configured token         |
| Production  | Not set           | **Service fails to start**   |
| Production  | Set               | Enforce authentication       |

---

Resolves #37 #40 
