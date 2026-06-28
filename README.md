# langchain-verifly

LangChain integration for [Verifly](https://verifly.email) — **agent-native email verification**.

`langchain-verifly` gives any LangChain agent a single, well-described tool to
check whether an email address is real and deliverable *before* it sends a
message or accepts a signup. It wraps the Verifly verification API and returns a
clean, structured verdict (deliverable / undeliverable / risky), the reason, a
confidence score, and an actionable send-or-reject recommendation.

## Installation

```bash
pip install -U langchain-verifly
```

## Setup

Set your Verifly API key in the environment. You can self-onboard for a key
(with free credits) at [verifly.email](https://verifly.email).

```bash
export VERIFLY_API_KEY="vf_..."
```

## Tool: `VeriflyEmailVerifier`

A LangChain `BaseTool` with both sync and async support.

```python
from langchain_verifly import VeriflyEmailVerifier

verifier = VeriflyEmailVerifier()  # reads VERIFLY_API_KEY from the environment

verifier.invoke({"email": "lead@example.com"})
```

```python
{
    "email": "lead@example.com",
    "result": "deliverable",
    "reason": "Mailbox exists",
    "confidence": 95,
    "is_valid": True,
    "recommendation": "send",
    "did_you_mean": None,
    "details": {
        "syntax_valid": True,
        "domain_exists": True,
        "mx_records": True,
        "smtp_valid": True,
        "is_disposable": False,
        "is_role_account": False,
        "is_catch_all": False,
        "is_free_provider": False,
        "provider": "example.com",
    },
}
```

Async works too:

```python
await verifier.ainvoke({"email": "lead@example.com"})
```

You can also pass the key explicitly instead of using the environment variable:

```python
verifier = VeriflyEmailVerifier(api_key="vf_...")
```

## Use it in an agent

```python
from langchain.agents import create_react_agent  # or any agent constructor
from langchain_verifly import VeriflyEmailVerifier

tools = [VeriflyEmailVerifier()]
# ... wire `tools` into your agent / model.bind_tools(tools) as usual
```

The agent can now verify an address on its own — for example, scrubbing a lead
list, validating a user-supplied email at signup, or confirming a contact
before drafting an outreach email.

## Verdict fields

| Field | Meaning |
|-------|---------|
| `result` | `deliverable`, `undeliverable`, or `risky` |
| `reason` | Human-readable explanation of the verdict |
| `confidence` | Confidence score, 0–100 |
| `is_valid` | Whether the address is considered valid/usable |
| `recommendation` | `send`, `do_not_send`, or `risky` |
| `did_you_mean` | A suggested correction for likely typos, if any |
| `details` | Syntax / domain / MX / SMTP / disposable / role / catch-all / free-provider flags |

## License

MIT
