from dataclasses import asdict, dataclass


@dataclass
class ShadowMetrics:
    total: int = 0
    agreements: int = 0
    disagreements: int = 0

    guard_accepted: int = 0
    guard_blocked: int = 0

    authority_granted: int = 0
    authority_denied: int = 0

    last_authoritative_intent: str | None = None
    last_shadow_intent: str | None = None
    last_shadow_confidence: float | None = None
    last_agreement: bool | None = None

    last_guard_allowed: bool | None = None
    last_guard_reason: str | None = None

    last_authority_allowed: bool | None = None
    last_authority_reason: str | None = None
    last_decision_source: str = "deterministic"

    def record(
        self,
        authoritative_intent: str,
        shadow_intent: str,
        shadow_confidence: float,
        guard_allowed: bool,
        guard_reason: str,
        authority_allowed: bool = False,
        authority_reason: str = "not_evaluated",
    ) -> None:

        agreement = (
            authoritative_intent
            == shadow_intent
        )

        self.total += 1

        if agreement:
            self.agreements += 1
        else:
            self.disagreements += 1

        if guard_allowed:
            self.guard_accepted += 1
        else:
            self.guard_blocked += 1

        self.last_authoritative_intent = (
            authoritative_intent
        )

        self.last_shadow_intent = (
            shadow_intent
        )

        self.last_shadow_confidence = (
            shadow_confidence
        )

        self.last_agreement = agreement

        self.last_guard_allowed = (
            guard_allowed
        )

        self.last_guard_reason = (
            guard_reason
        )

        if authority_allowed:
            self.authority_granted += 1
        else:
            self.authority_denied += 1

        self.last_authority_allowed = authority_allowed
        self.last_authority_reason = authority_reason
        self.last_decision_source = (
            "ai" if authority_allowed else "deterministic"
        )

    @property
    def agreement_rate(self) -> float:
        if self.total == 0:
            return 0.0

        return round(
            self.agreements
            / self.total
            * 100,
            1,
        )

    @property
    def guard_acceptance_rate(self) -> float:
        if self.total == 0:
            return 0.0

        return round(
            self.guard_accepted
            / self.total
            * 100,
            1,
        )

    @property
    def authority_grant_rate(self) -> float:
        if self.total == 0:
            return 0.0

        return round(
            self.authority_granted
            / self.total
            * 100,
            1,
        )

    def to_dict(self) -> dict:
        data = asdict(self)

        data["agreement_rate"] = (
            self.agreement_rate
        )

        data["guard_acceptance_rate"] = (
            self.guard_acceptance_rate
        )

        data["authority_grant_rate"] = (
            self.authority_grant_rate
        )

        return data
