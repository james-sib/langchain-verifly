"""LangChain integration for Verifly — agent-native email verification.

Exposes :class:`VeriflyEmailVerifier`, a LangChain ``BaseTool`` that verifies
the deliverability of an email address through the Verifly API
(https://verifly.email) and returns a structured verdict (result, reason,
confidence, and deliverability flags).
"""

from importlib import metadata

from langchain_verifly.tool import VeriflyEmailVerifier, VeriflyToolInput

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:  # pragma: no cover - local source tree
    __version__ = ""

__all__ = ["VeriflyEmailVerifier", "VeriflyToolInput", "__version__"]
