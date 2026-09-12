import pytest
from helzer.services.vps_service import VPSSpec, VPSService


def test_validate_spec_rejects_invalid_values():
    service = VPSService(None, None, None)
    with pytest.raises(ValueError):
        service.validate_spec(VPSSpec("x", 0, 512, 10))
    with pytest.raises(ValueError):
        service.validate_spec(VPSSpec("x", 1, 512, 0))


def test_container_name_is_safe_and_bounded():
    assert VPSService.container_name(42, "My Server / Prod") == "hx_42_my-server-prod"
    assert len(VPSService.container_name(1, "x" * 100)) <= 63
