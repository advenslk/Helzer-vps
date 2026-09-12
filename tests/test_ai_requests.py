from helzer.core.ai_requests import CreateVPSRequest


def test_create_vps_request_parses_resources():
    request = CreateVPSRequest.from_text(
        "create vps for @123 with 24GB ram, 2 cores, 30gb disk"
    )
    assert request.target_user_id == 123
    assert request.ram_mb == 24 * 1024
    assert request.cpu_cores == 2
    assert request.disk_gb == 30


def test_create_vps_request_requires_target_and_resources():
    try:
        CreateVPSRequest.from_text("create vps")
    except ValueError as exc:
        assert "target user" in str(exc).lower()
    else:
        raise AssertionError("missing target should fail")
