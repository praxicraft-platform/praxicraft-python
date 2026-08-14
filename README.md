# Praxicraft Python SDK

Official Python client for the **[Praxicraft Assess](https://assess.praxicraft.com)** Public API.

Use it to invite candidates, check invite quota, manage webhooks, enroll hiring pipelines, and fetch results from your ATS, backend, or automation scripts.

```bash
pip install praxicraft
```

**Requires Python 3.10+.** Full API reference: [docs.praxicraft.com](https://docs.praxicraft.com)

## Table of Contents

- [Authentication](#authentication)
- [Quickstart](#quickstart)
- [What you can do](#what-you-can-do)
  - [Check invite quota before bulk sends](#check-invite-quota-before-bulk-sends)
  - [Bulk invites](#bulk-invites)
  - [Build and activate an assessment via API](#build-and-activate-an-assessment-via-api)
  - [Register and test a webhook](#register-and-test-a-webhook)
  - [Enroll into a hiring pipeline](#enroll-into-a-hiring-pipeline)
  - [Paginate cohort results](#paginate-cohort-results)
  - [Verify webhook signatures](#verify-webhook-signatures)
- [Errors](#errors)
- [Requirements & support](#requirements--support)
- [License](#license)

---

## Authentication

Create an organisation API key in Assess:

**Assess → Developer → API Keys** → create key → copy `ct_live_…` (shown once).

```bash
export PRAXICRAFT_API_KEY="ct_live_xxxxxxxxxxxxxxxx"
```

Or pass the key when constructing the client:

```python
from praxicraft import Client

client = Client(api_key="ct_live_xxxxxxxxxxxxxxxx")
```

Optional: override the API host with `PRAXICRAFT_API_BASE_URL` or `Client(base_url=...)`.
Default host: `https://assess.praxicraft.com`.

Never commit API keys. Prefer environment variables or a secrets manager.

Scopes and rotation: [Authentication](https://docs.praxicraft.com/authentication)

---

## Quickstart

```python
from praxicraft import Client

client = Client()  # reads PRAXICRAFT_API_KEY

# List assessments
page = client.assessments.list()
for assessment in page["results"]:
    print(assessment["slug"], assessment["status"])

# Invite a candidate (idempotent on email — safe to retry)
invite = client.invites.create(
    "senior-backend-screen",
    email="candidate@example.com",
    name="Jane Doe",
    send_email=True,
)
print(invite["invite_token"], invite.get("invite_url"))

# Fetch that candidate's result
result = client.results.retrieve(invite_token=invite["invite_token"])
print(result)
```

Responses are **flat JSON** (same shape as the Public API — no `{ "data": … }` wrapper).

---

## What you can do

| Resource | Common methods |
|----------|----------------|
| `client.org` | `retrieve()`, `stats()` |
| `client.assessments` | `list()`, `retrieve()`, `create()`, `update()`, `activate()`, `list_cases()`, `attach_cases()`, `replace_cases()`, `remove_case()` |
| `client.invites` | `create()`, `bulk_create()`, `list()`, `retrieve()`, `remind()`, `cancel()` |
| `client.results` | `list()`, `retrieve()`, `iter_all()` |
| `client.webhooks` | `list()`, `create()`, `retrieve()`, `update()`, `delete()`, `test()`, `deliveries()` |
| `client.pipelines` | `list()`, `retrieve()`, `enroll()`, `bulk_enroll()`, `list_enrollments()`, `get_enrollment()` |
| `verify_signature` | Verify `X-Praxicraft-Signature` on webhook payloads |

All paths target `/api/v1/public/…` on the Assess host.

### Check invite quota before bulk sends

```python
org = client.org.retrieve()
if (org.get("invites_remaining") or 0) < len(candidates):
    raise SystemExit("Not enough invites remaining this month")
```

### Bulk invites

```python
client.invites.bulk_create(
    "senior-backend-screen",
    candidates=[
        {"email": "a@example.com", "name": "Alex"},
        {"email": "b@example.com", "name": "Blair"},
    ],
    send_email=True,
)
```

### Build and activate an assessment via API

```python
assessment = client.assessments.create(title="Backend screen")
client.assessments.attach_cases(
    assessment["slug"],
    cases=[{"case_id": "<platform-or-org-case-uuid>", "source": "platform"}],
)
client.assessments.activate(assessment["slug"])
```

### Register and test a webhook

```python
hook = client.webhooks.create(
    url="https://example.com/hooks/praxicraft",
    events=["assessment.completed", "candidate.passed"],
)
# Store hook["secret_key"] (whsec_…) — shown once
client.webhooks.test(hook["id"])
client.webhooks.update(hook["id"], is_active=True)
```

### Enroll into a hiring pipeline

```python
enrollment = client.pipelines.enroll(
    "grad-2025",
    email="alex@example.com",
    name="Alex Lee",
    send_email=True,
)
status = client.pipelines.get_enrollment(enrollment["enrollment_id"])
```

### Paginate cohort results

```python
for row in client.results.iter_all("senior-backend-screen", page_size=50):
    print(row.get("email"), row.get("score_percentage"), row.get("passed"))
```

### Verify webhook signatures

Assess signs the **raw request body** with your webhook secret (`whsec_…`):

```python
from praxicraft import verify_signature

def handle_webhook(raw_body: bytes, signature_header: str, secret: str) -> bool:
    return verify_signature(secret, raw_body, signature_header)
```

Header format: `X-Praxicraft-Signature: sha256=<hex>`

Event catalog and payload examples: [Webhooks](https://docs.praxicraft.com/webhooks)

---

## Errors

Public API errors look like:

```json
{
  "error": {
    "code": "INSUFFICIENT_SCOPE",
    "message": "This API key does not have the 'candidates:read' scope."
  }
}
```

The SDK raises typed exceptions. **Branch on `exc.code`**, not the message text:

```python
from praxicraft import (
    AuthenticationError,
    InsufficientScopeError,
    RateLimitError,
    ValidationError,
)

try:
    client.invites.create("demo", email="candidate@example.com")
except ValidationError as exc:
    # e.g. ASSESSMENT_NOT_ACTIVE, REMINDER_COOLDOWN, VALIDATION_ERROR
    print(exc.code, exc.details)
except InsufficientScopeError as exc:
    print(exc.code)  # INSUFFICIENT_SCOPE, INVITE_QUOTA_EXCEEDED, …
except AuthenticationError as exc:
    print(exc.code)  # INVALID_API_KEY, EXPIRED_API_KEY
except RateLimitError as exc:
    print(exc.retry_after)  # seconds from Retry-After, when present
```

Error codes: [Errors](https://docs.praxicraft.com/errors)

---

## Requirements & support

- Python **3.10**, **3.11**, or **3.12+**
- Dependency: [`httpx`](https://www.python-httpx.org/)
- Product docs: [docs.praxicraft.com](https://docs.praxicraft.com)
- Issues: [GitHub Issues](https://github.com/praxicraft-platform/praxicraft-python/issues)

---

## License

[MIT](LICENSE)
