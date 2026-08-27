from backend.intelligence.authority_policy import (
    AuthorityPolicy,
)


def test_presence_high_confidence_granted():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="PRESENCE",
        confidence=0.95,
        guard_allowed=True,
    )

    assert result.allowed is True
    assert result.reason == "ai_authority_granted"


def test_presence_below_authority_threshold_denied():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="PRESENCE",
        confidence=0.75,
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "authority_confidence_below_threshold"


def test_alert_is_not_ai_authorized():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="ALERT",
        confidence=0.99,
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "intent_not_authorized"


def test_guard_blocked_decision_never_gets_authority():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="PRESENCE",
        confidence=0.99,
        guard_allowed=False,
    )

    assert result.allowed is False
    assert result.reason == "guard_blocked"


def test_unknown_intent_never_gets_authority():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="DESTROY",
        confidence=1.0,
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "intent_not_authorized"


def test_dark_high_confidence_granted():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="DARK",
        confidence=0.90,
        guard_allowed=True,
    )

    assert result.allowed is True
    assert result.reason == "ai_authority_granted"


def test_idle_exact_threshold_granted():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="IDLE",
        confidence=0.85,
        guard_allowed=True,
    )

    assert result.allowed is True
    assert result.reason == "ai_authority_granted"


def test_confidence_just_below_threshold_denied():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="IDLE",
        confidence=0.849,
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "authority_confidence_below_threshold"


def test_invalid_confidence_type_denied_defensively():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="PRESENCE",
        confidence="0.95",
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "invalid_confidence_type"


def test_non_finite_confidence_is_denied_defensively():
    policy = AuthorityPolicy()

    result = policy.evaluate(
        intent="PRESENCE",
        confidence=float("nan"),
        guard_allowed=True,
    )

    assert result.allowed is False
    assert result.reason == "confidence_out_of_range"


def test_invalid_policy_threshold_is_rejected():
    try:
        AuthorityPolicy(minimum_authority_confidence=1.1)
    except ValueError as error:
        assert "between 0 and 1" in str(error)
    else:
        raise AssertionError("Invalid authority threshold was accepted")
