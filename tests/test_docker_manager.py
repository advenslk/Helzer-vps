from helzer.docker.manager import DockerManager


def test_container_config_has_resource_limits():
    manager = DockerManager(client=None)
    config = manager.build_container_config(
        name="hx_001", image="ubuntu:24.04", cpu_cores=2, ram_mb=4096
    )
    assert config["image"] == "ubuntu:24.04"
    assert config["name"] == "hx_001"
    assert config["mem_limit"] == 4096 * 1024 * 1024
    assert config["nano_cpus"] == 2_000_000_000


def test_disallowed_image_is_rejected():
    manager = DockerManager(client=None)
    try:
        manager.build_container_config(
            name="hx_001", image="malicious/image:latest", cpu_cores=1, ram_mb=512
        )
    except ValueError as exc:
        assert "not allowed" in str(exc).lower()
    else:
        raise AssertionError("disallowed image should fail")
