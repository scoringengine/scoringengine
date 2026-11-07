import os

DOCKERFILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker", "worker", "Dockerfile")


class TestWorkerDockerfile:
    def test_stale_x_lock_removed_before_xvfb_starts(self):
        with open(DOCKERFILE) as f:
            cmd = [line for line in f if line.startswith("CMD ")][-1]
        assert "rm -f /tmp/.X1-lock /tmp/.X11-unix/X1" in cmd
        assert cmd.index("rm -f /tmp/.X1-lock") < cmd.index("Xvfb :1")
