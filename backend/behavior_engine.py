from backend.action_engine import ActionEngine
from backend.intelligence_engine import IntelligenceDecision


class BehaviorEngine:
    """
    Executes validated semantic intentions.

    IntelligenceEngine:
        What should Cypher intend to do?

    BehaviorEngine:
        Is that intention allowed to become behavior?

    ActionEngine:
        Perform the physical action.
    """

    def __init__(
        self,
        actions: ActionEngine,
    ):
        self.actions = actions

    def handle_decision(
        self,
        decision: IntelligenceDecision,
    ) -> dict | None:

        intent = decision.intent.upper()

        if intent == "NONE":
            return None

        if intent == "IDLE":
            return self.actions.idle()

        if intent == "PRESENCE":
            return self.actions.presence()

        if intent == "DARK":
            return self.actions.dark()

        if intent == "ALERT":
            return self.actions.alert()

        if intent == "SUCCESS":
            return self.actions.success()

        if intent == "THINKING":
            return self.actions.thinking()

        # Defense in depth.
        # Unknown intentions never reach hardware.
        raise ValueError(
            f"Unsupported behavior intent: {intent}"
        )