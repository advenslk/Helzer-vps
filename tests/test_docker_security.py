from helzer.docker.manager import DockerManager


def test_container_drops_privileges_and_has_no_privileged_mode():
    cfg = DockerManager(None).build_container_config(name="hx_1", image="ubuntu:24.04", cpu_cores=1, ram_mb=512)
    assert cfg["privileged"] is False
    assert cfg["cap_drop"] == ["ALL"]
