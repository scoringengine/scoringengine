import os

import yaml

COMPOSE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")


class TestDockerComposeNetwork:
    def test_network_mtu_is_configurable_with_safe_default(self):
        with open(COMPOSE_PATH) as f:
            compose = yaml.safe_load(f)
        driver_opts = compose["networks"]["default"]["driver_opts"]
        # Defaults to Docker's own 1500 so existing deployments are unchanged
        assert driver_opts["com.docker.network.driver.mtu"] == "${DOCKER_NETWORK_MTU:-1500}"
