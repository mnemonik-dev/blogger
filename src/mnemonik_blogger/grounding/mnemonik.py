"""Grounding: pull protocol facts to anchor content, and record what was published.

Two responsibilities:
  1. recall(): fetch facts about the Mnemonik protocol to ground a post.
  2. attest(): record a verifiable memory of what was published.

The Mnemonik protocol is itself an MCP server (mnemonic_recall / mnemonic_sign_memory
/ mnemonic_verify). Those tools live in the agent host, not in this library, so we
define a small `Grounding` protocol with two concrete fallbacks:

  * `FileGrounding`  - reads facts from a YAML file (offline, deterministic).
  * `StaticGrounding` - ships sensible defaults derived from the protocol's own
    MCP tool descriptions; use until the live MCP is wired in.

To use the live MCP, implement `Grounding` in the agent runtime and have recall()
call mnemonic_recall and attest() call mnemonic_sign_memory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import yaml

from ..models import ProtocolFact

# Derived from the Mnemonik MCP tool descriptions. Treat as provisional until the
# live MCP / official BRAND is confirmed.
DEFAULT_FACTS: list[str] = [
    "Mnemonik is a protocol for verifiable memory: agents can recall past "
    "decisions and cryptographically prove them.",
    "Each memory is a signed attestation - canonical CBOR, a blake3 content hash, "
    "and a COSE_Sign1 Ed25519 signature.",
    "Attestations are stored permanently on Arweave and anchored as an SPL Memo "
    "on Solana, so the record is tamper-evident.",
    "Recall uses semantic similarity search over an agent's attested memory pool.",
    "Verification recomputes the hash and checks the signature and on-chain record.",
    "Identity is portable via did:sol and did:key, tied to a Solana public key.",
    "Local mode keeps memories free and offline; participate mode anchors on-chain "
    "(may incur cost).",
]


class Grounding(Protocol):
    """Source of protocol facts and sink for publish attestations."""

    def recall(self, query: str, limit: int = 5) -> list[ProtocolFact]: ...

    def attest(self, content: str, tags: list[str] | None = None) -> str | None:
        """Persist a verifiable memory; return an attestation id (or None if no-op)."""
        ...


class StaticGrounding:
    """Ships built-in default facts. No persistence."""

    def recall(self, query: str, limit: int = 5) -> list[ProtocolFact]:
        return [ProtocolFact(text=t, source="static") for t in DEFAULT_FACTS[:limit]]

    def attest(self, content: str, tags: list[str] | None = None) -> str | None:
        return None


class FileGrounding:
    """Reads facts from a YAML file: ``facts: [ "...", ... ]``."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def recall(self, query: str, limit: int = 5) -> list[ProtocolFact]:
        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        facts = data.get("facts", []) if isinstance(data, dict) else []
        return [ProtocolFact(text=str(t), source="facts-file") for t in facts[:limit]]

    def attest(self, content: str, tags: list[str] | None = None) -> str | None:
        return None


def default_grounding(facts_path: str | None) -> Grounding:
    return FileGrounding(facts_path) if facts_path else StaticGrounding()
