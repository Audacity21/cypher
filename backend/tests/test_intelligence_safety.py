from backend.intelligence.intelligence_engine import IntelligenceDecision
from backend.intelligence.intelligence_guard import IntelligenceGuard


guard = IntelligenceGuard(
    minimum_confidence=0.70
)


def run_test(
    name: str,
    decision: IntelligenceDecision,
    expected_allowed: bool,
    expected_reason: str,
):
    result = guard.evaluate(decision)

    passed = (
        result.allowed == expected_allowed
        and result.reason == expected_reason
    )

    print()
    print("=" * 60)
    print(f"TEST: {name}")
    print("=" * 60)

    print("DECISION:")
    print(
        {
            "intent": decision.intent,
            "reason": decision.reason,
            "confidence": decision.confidence,
        }
    )

    print()
    print("GUARD:")
    print(
        {
            "allowed": result.allowed,
            "reason": result.reason,
        }
    )

    print()
    print(
        "RESULT:",
        "PASS" if passed else "FAIL",
    )

    assert passed, (
        f"{name} failed. "
        f"Expected allowed={expected_allowed}, "
        f"reason={expected_reason}, "
        f"got allowed={result.allowed}, "
        f"reason={result.reason}"
    )


# ============================================================
# TEST 1
# UNKNOWN / HOSTILE INTENT
# ============================================================

run_test(
    name="Unknown intent is blocked",

    decision=IntelligenceDecision(
        intent="DESTROY",
        reason="Attempting an unsupported action.",
        confidence=1.0,
    ),

    expected_allowed=False,
    expected_reason="unknown_intent",
)


# ============================================================
# TEST 2
# LOW CONFIDENCE
# ============================================================

run_test(
    name="Low confidence is blocked",

    decision=IntelligenceDecision(
        intent="PRESENCE",
        reason="Something may be nearby.",
        confidence=0.25,
    ),

    expected_allowed=False,
    expected_reason="confidence_below_threshold",
)


# ============================================================
# TEST 3
# OUT-OF-RANGE CONFIDENCE
# ============================================================

run_test(
    name="Invalid confidence is blocked",

    decision=IntelligenceDecision(
        intent="DARK",
        reason="Environment became dark.",
        confidence=4.2,
    ),

    expected_allowed=False,
    expected_reason="confidence_out_of_range",
)


# ============================================================
# TEST 4
# MISSING REASON
# ============================================================

run_test(
    name="Missing reason is blocked",

    decision=IntelligenceDecision(
        intent="IDLE",
        reason="",
        confidence=0.95,
    ),

    expected_allowed=False,
    expected_reason="missing_reason",
)


# ============================================================
# TEST 5
# VALID HIGH-CONFIDENCE DECISION
# ============================================================

run_test(
    name="Valid decision is accepted",

    decision=IntelligenceDecision(
        intent="PRESENCE",
        reason="An object entered interaction range.",
        confidence=0.95,
    ),

    expected_allowed=True,
    expected_reason="accepted",
)


print()
print("=" * 60)
print("ALL INTELLIGENCE GUARD TESTS PASSED")
print("=" * 60)