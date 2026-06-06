"""Mnemonik brand voice and content guardrails.

These defaults are derived from the Mnemonik MCP's own tool descriptions
(verifiable memory attestations: canonical CBOR + blake3, COSE_Sign1 / Ed25519
signatures, Arweave storage, Solana SPL-Memo anchoring, did:sol / did:key
identity). Confirm and refine against the official BRAND/VOICE once the Mnemonik
MCP is re-authorized — see grounding/mnemonik.py.
"""

from __future__ import annotations

ONE_LINER = "Verifiable memory for AI agents — recall it, and prove it."

# How the agent should sound. Fed into LLM generation and used for review.
VOICE = """\
- Confident and precise; we talk about cryptography and provenance, so be exact.
- Builder-to-builder. Concrete over hype. Show the mechanism, not just the promise.
- Credible-neutral on chains/tokens. Explain value, never give financial advice.
- Plainspoken: prefer "you can prove what an agent remembered" over jargon walls.
- Lead with the problem (agents forget / can't be trusted to recall accurately),
  then the proof (signed, anchored, verifiable), then the call to build.
"""

# Hard guardrails. The reviewer/formatter enforces these before publishing.
GUARDRAILS = [
    "No price predictions, no 'to the moon', no financial advice.",
    "No unverifiable claims about partnerships, audits, or metrics.",
    "Every protocol claim must trace to a grounded fact (MCP attestation or facts file).",
    "Disclose that on-chain anchoring (participate mode) may incur cost.",
    "No fabricated quotes, users, or testimonials.",
]

# Canonical hashtags per platform context (kept short; platforms penalize spam).
HASHTAGS = ["#Mnemonik", "#AIagents", "#verifiableAI", "#Solana", "#Arweave"]

# Forbidden marketing phrases (lightweight prose hygiene, mirrors claude-blog).
BANNED_PHRASES = [
    "to the moon",
    "guaranteed returns",
    "financial advice",
    "100x",
    "get rich",
]


def voice_brief() -> str:
    """A compact brief suitable for prompting an LLM writer."""
    return f"Brand one-liner: {ONE_LINER}\n\nVoice:\n{VOICE}\nGuardrails:\n- " + "\n- ".join(
        GUARDRAILS
    )
