from helzer.core.limits import get_plan, within_plan


def test_free_plan_limits():
    plan = get_plan("free")
    assert within_plan(plan, 1, 512, 10)
    assert not within_plan(plan, 2, 512, 10)
    assert not within_plan(plan, 1, 1024, 10)


def test_unknown_plan_rejected():
    try:
        get_plan("enterprise")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown plan should fail")
