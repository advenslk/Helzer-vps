import pytest

from helzer.services.vps_service import VPSService, VPSSpec


def test_validate_name_and_limits():
    service = VPSService(None, None, None)
    with pytest.raises(ValueError):
        service.validate_spec(VPSSpec("", 1, 512, 10))
    with pytest.raises(ValueError):
        service.validate_spec(VPSSpec("ok", 33, 512, 10))


def test_allowed_images_are_exposed():
    assert "ubuntu:24.04" in VPSService.ALLOWED_IMAGES
    assert "malicious:latest" not in VPSService.ALLOWED_IMAGES
