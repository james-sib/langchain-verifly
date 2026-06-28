"""Verifly email-verification tool for LangChain."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

DEFAULT_BASE_URL = "https://verifly.email"
_VERIFY_PATH = "/api/v1/verify"
_DEFAULT_TIMEOUT = 30.0


class VeriflyToolInput(BaseModel):
    """Input schema for :class:`VeriflyEmailVerifier`."""

    email: str = Field(
        ...,
        description="The email address to verify, e.g. 'lead@example.com'.",
    )


class VeriflyEmailVerifier(BaseTool):
    """Verify the deliverability of an email address with Verifly.

    Agent-native email verification: given a single email address, this tool
    calls the Verifly API (``GET /api/v1/verify``) and returns a structured
    verdict describing whether the address is deliverable, undeliverable, or
    risky, along with the reason, a confidence score, and the actionable
    send/reject recommendation. Use it to validate a lead or signup before
    sending mail.

    Setup:
        Install the package and set your Verifly API key in the environment.

        .. code-block:: bash

            pip install -U langchain-verifly
            export VERIFLY_API_KEY="vf_..."

        A key (with free credits) can be obtained at https://verifly.email.

    Instantiate:
        .. code-block:: python

            from langchain_verifly import VeriflyEmailVerifier

            verifier = VeriflyEmailVerifier()
            # or pass the key explicitly:
            verifier = VeriflyEmailVerifier(api_key="vf_...")

    Invoke directly:
        .. code-block:: python

            verifier.invoke({"email": "lead@example.com"})

    The tool returns a dict such as::

        {
            "email": "lead@example.com",
            "result": "deliverable",
            "reason": "Mailbox exists",
            "confidence": 95,
            "is_valid": True,
            "recommendation": "send",
            "details": {...},
        }
    """

    name: str = "verifly_email_verifier"
    description: str = (
        "Verify whether a single email address is deliverable using Verifly. "
        "Input is one email address. Returns the verdict (deliverable, "
        "undeliverable, or risky), the reason, a confidence score (0-100), "
        "and a send/reject recommendation. Use before emailing a lead or "
        "accepting a signup to avoid bounces and bad addresses."
    )
    args_schema: type[BaseModel] = VeriflyToolInput

    api_key: Optional[str] = Field(
        default=None,
        description=(
            "Verifly API key. Falls back to the VERIFLY_API_KEY environment "
            "variable when not set."
        ),
    )
    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="Base URL of the Verifly API.",
    )
    timeout: float = Field(
        default=_DEFAULT_TIMEOUT,
        description="HTTP request timeout in seconds.",
    )

    def _resolve_key(self) -> str:
        key = self.api_key or os.environ.get("VERIFLY_API_KEY")
        if not key:
            raise ValueError(
                "A Verifly API key is required. Pass api_key=... or set the "
                "VERIFLY_API_KEY environment variable. Get a free key at "
                "https://verifly.email."
            )
        return key

    @staticmethod
    def _shape(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce the raw API response to the relevant verdict fields."""
        return {
            "email": payload.get("email"),
            "result": payload.get("result"),
            "reason": payload.get("reason"),
            "confidence": payload.get("confidence"),
            "is_valid": payload.get("is_valid"),
            "recommendation": payload.get("recommendation"),
            "did_you_mean": payload.get("did_you_mean"),
            "details": payload.get("details"),
        }

    def _request_args(self, email: str) -> Dict[str, Any]:
        return {
            "url": f"{self.base_url.rstrip('/')}{_VERIFY_PATH}",
            "params": {"email": email},
            "headers": {
                "Authorization": f"Bearer {self._resolve_key()}",
                "Accept": "application/json",
            },
            "timeout": self.timeout,
        }

    def _run(
        self,
        email: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.get(**self._request_args(email))
            response.raise_for_status()
            return self._shape(response.json())

    async def _arun(
        self,
        email: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(**self._request_args(email))
            response.raise_for_status()
            return self._shape(response.json())
