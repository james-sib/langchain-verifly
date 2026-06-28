"""Unit tests for VeriflyEmailVerifier (no network calls)."""

import httpx
import pytest

from langchain_core.tools import BaseTool

from langchain_verifly import VeriflyEmailVerifier, VeriflyToolInput

_SAMPLE_RESPONSE = {
    "success": True,
    "email": "lead@example.com",
    "is_valid": True,
    "result": "deliverable",
    "reason": "Mailbox exists",
    "confidence": 95,
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
    "credits": {"used": 1, "remaining": 99},
    "request_id": "abc-123",
}


def _mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/verify"
        assert request.url.params.get("email") == "lead@example.com"
        assert request.headers["Authorization"] == "Bearer vf_test"
        return httpx.Response(200, json=_SAMPLE_RESPONSE)

    return httpx.MockTransport(handler)


def test_is_a_langchain_tool():
    tool = VeriflyEmailVerifier(api_key="vf_test")
    assert isinstance(tool, BaseTool)
    assert tool.name == "verifly_email_verifier"
    assert tool.args_schema is VeriflyToolInput


def test_input_schema_requires_email():
    with pytest.raises(Exception):
        VeriflyToolInput()  # type: ignore[call-arg]
    assert VeriflyToolInput(email="a@b.com").email == "a@b.com"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("VERIFLY_API_KEY", raising=False)
    tool = VeriflyEmailVerifier()
    with pytest.raises(ValueError, match="VERIFLY_API_KEY"):
        tool.invoke({"email": "lead@example.com"})


def test_run_shapes_verdict(monkeypatch):
    tool = VeriflyEmailVerifier(api_key="vf_test")
    real_client = httpx.Client

    def patched_client(*args, **kwargs):
        kwargs["transport"] = _mock_transport()
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", patched_client)

    result = tool.invoke({"email": "lead@example.com"})
    assert result["result"] == "deliverable"
    assert result["reason"] == "Mailbox exists"
    assert result["confidence"] == 95
    assert result["is_valid"] is True
    assert result["recommendation"] == "send"
    assert result["details"]["provider"] == "example.com"
    # raw-only fields should be stripped out
    assert "credits" not in result
    assert "request_id" not in result


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("VERIFLY_API_KEY", "vf_test")
    tool = VeriflyEmailVerifier()
    real_client = httpx.Client

    def patched_client(*args, **kwargs):
        kwargs["transport"] = _mock_transport()
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", patched_client)
    result = tool.invoke({"email": "lead@example.com"})
    assert result["email"] == "lead@example.com"


@pytest.mark.asyncio
async def test_arun_shapes_verdict(monkeypatch):
    tool = VeriflyEmailVerifier(api_key="vf_test")
    real_async_client = httpx.AsyncClient

    def patched_async_client(*args, **kwargs):
        kwargs["transport"] = _mock_transport()
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", patched_async_client)

    result = await tool.ainvoke({"email": "lead@example.com"})
    assert result["result"] == "deliverable"
    assert result["confidence"] == 95
