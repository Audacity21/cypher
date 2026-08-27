import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityResult:
    allowed: bool
    reason: str


class AuthorityPolicy:
    """
    Controls whether a guarded AI decision is permitted to become authoritative.

    This policy is intentionally stricter than IntelligenceGuard.

    IntelligenceGuard:
        "Is this AI output structurally and semantically acceptable?"

    AuthorityPolicy:
        "Even if acceptable, is AI actually permitted to control this intent?"
    """

    ALLOWED_AI_INTENTS = {
        "PRESENCE",
        "IDLE",
        "DARK",
    }

    def __init__(self, minimum_authority_confidence: float = 0.85):
        if (
            isinstance(minimum_authority_confidence, bool)
            or not isinstance(minimum_authority_confidence, (int, float))
            or not math.isfinite(minimum_authority_confidence)
            or not 0.0 <= minimum_authority_confidence <= 1.0
        ):
            raise ValueError(
                "minimum_authority_confidence must be a number between 0 and 1"
            )
        self.minimum_authority_confidence = minimum_authority_confidence

    def evaluate(
        self,
        *,
        intent: str,
        confidence: float,
        guard_allowed: bool,
    ) -> AuthorityResult:
        """
        Evaluate whether an AI decision may receive limited authority.

        Expected call order:

            LLM
             ↓
            schema validation
             ↓
            IntelligenceGuard
             ↓
            AuthorityPolicy
             ↓
            authoritative decision OR deterministic fallback
        """

        if not guard_allowed:
            return AuthorityResult(
                allowed=False,
                reason="guard_blocked",
            )

        if intent not in self.ALLOWED_AI_INTENTS:
            return AuthorityResult(
                allowed=False,
                reason="intent_not_authorized",
            )

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
        ):
            return AuthorityResult(
                allowed=False,
                reason="invalid_confidence_type",
            )

        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            return AuthorityResult(
                allowed=False,
                reason="confidence_out_of_range",
            )

        if confidence < self.minimum_authority_confidence:
            return AuthorityResult(
                allowed=False,
                reason="authority_confidence_below_threshold",
            )

        return AuthorityResult(
            allowed=True,
            reason="ai_authority_granted",
        )
