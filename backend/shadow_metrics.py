from dataclasses import asdict, dataclass


@dataclass
class ShadowMetrics:
    total: int = 0
    agreements: int = 0
    disagreements: int = 0

    last_authoritative_intent: str | None = None
    last_shadow_intent: str | None = None
    last_shadow_confidence: float | None = None
    last_agreement: bool | None = None

    def record(
        self,
        authoritative_intent: str,
        shadow_intent: str,
        shadow_confidence: float,
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

    def to_dict(self) -> dict:
        data = asdict(self)

        data["agreement_rate"] = (
            self.agreement_rate
        )

        return data