#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import getpass
import socket
import shutil
import subprocess
import argparse
from copy import deepcopy
from pathlib import Path

CONFIG_DIR = Path.cwd()
ENV_FILE = CONFIG_DIR / ".env"

# compose file bind-mounts this path:
DOCKER_ENGINE_CONF = CONFIG_DIR / "docker" / "engine.conf.inc"
ENGINE_CONF_TEMPLATE = CONFIG_DIR / "engine.conf.inc"

# UI / prompt helpers
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def prompt(msg, default=None, required=False, is_password=False, allow_blank=False):
    while True:
        if is_password:
            val = getpass.getpass(f"{msg}: ").strip()
        else:
            val = input(f"{msg} [{default}]: ").strip() if default is not None else input(f"{msg}: ").strip()

        if not val:
            if default is not None and default != "":
                return default
            if allow_blank:
                return ""
            if required:
                print("This field is required.")
                continue
            return ""
        return val

def redact_config_for_print(config: dict) -> dict:
    c = deepcopy(config)
    # redact
    if "engine" in c and "agent_psk" in c["engine"]:
        c["engine"]["agent_psk"] = "********"
    if "database" in c and "password" in c["database"]:
        c["database"]["password"] = "********"
    if "admin" in c and "admin_password" in c["admin"]:
        c["admin"]["admin_password"] = "********"
    if "redis" in c and c["redis"].get("redis_password"):
        c["redis"]["redis_password"] = "********"
    # Hide password inside uri if present
    if "database" in c and "uri" in c["database"]:
        c["database"]["uri"] = "<redacted>"
    return c

# docker helpers
def require_docker():
    if shutil.which("docker") is None:
        sys.exit("Docker is required but was not found in PATH. Install Docker Desktop / docker engine first.")

    # verify compose works
    code, out = run_cmd(["docker", "compose", "version"], check=False, capture=True)
    if code != 0:
        print(out)
        sys.exit("Docker Compose is required but not working. Make sure Docker is running and compose is available.")

def run_cmd(cmd, check=True, capture=False):
    """
    Runs a command and returns (returncode, output_str).
    """
    try:
        if capture:
            res = subprocess.run(cmd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return res.returncode, res.stdout
        else:
            res = subprocess.run(cmd, check=check)
            return res.returncode, ""
    except subprocess.CalledProcessError as e:
        out = ""
        if hasattr(e, "stdout") and e.stdout:
            out = e.stdout
        return e.returncode, out


def docker_compose_up(services):
    print(f"→ Starting services: {', '.join(services)}")
    code, out = run_cmd(["docker", "compose", "up", "-d", *services], check=False, capture=True)
    if code != 0:
        print(out)
        sys.exit("Failed to start required docker services.")


def docker_compose_down_volumes():
    # only used on failure paths when we want a clean rollback
    run_cmd(["docker", "compose", "down", "-v"], check=False, capture=True)


def wait_for_tcp_inside_network(host, port, timeout_s=90):
    """
    Waits for host:port to become reachable from inside the compose network,
    by running a small python connect check inside the bootstrap container.
    Uses connect_ex() to avoid multi-line try/except syntax issues.
    """
    start = time.time()
    last_out = ""
    port = int(port)

    while time.time() - start < timeout_s:
        py = (
            "import socket,sys;"
            f"h={host!r};p={port};"
            "s=socket.socket();s.settimeout(2);"
            "rc=s.connect_ex((h,p));"
            "print(rc);"
            "sys.exit(0 if rc==0 else 1)"
        )
        cmd = ["docker", "compose", "run", "--rm", "bootstrap", "python3", "-c", py]
        code, out = run_cmd(cmd, check=False, capture=True)
        if code == 0:
            return True, ""
        last_out = out.strip()
        time.sleep(2)

    return False, last_out or f"Timed out waiting for {host}:{port}"


def test_db_uri_inside_docker(db_uri, timeout_s=60):
    """
    Validates DB credentials by connecting and running SELECT 1.
    Runs inside bootstrap container.
    Failures raise and exit non-zero.
    """
    start = time.time()
    last = ""
    while time.time() - start < timeout_s:
        py = (
            "import sys;"
            "from sqlalchemy import create_engine, text;"
            f"uri={db_uri!r};"
            "eng=create_engine(uri, pool_pre_ping=True);"
            "conn=eng.connect();"
            "conn.execute(text('SELECT 1'));"
            "conn.close();"
            "print('db ok');"
        )
        cmd = ["docker", "compose", "run", "--rm", "bootstrap", "python3", "-c", py]
        code, out = run_cmd(cmd, check=False, capture=True)
        if code == 0:
            return True, ""
        last = out.strip()
        time.sleep(2)
    return False, last


def test_redis_inside_docker(host, port, password=""):
    py = (
        "import redis;"
        f"host={host!r};port=int({port!r});pw={password!r};"
        "r=redis.Redis(host=host, port=port, password=(pw or None), socket_connect_timeout=2);"
        "r.ping();"
        "print('redis ok');"
    )
    cmd = ["docker", "compose", "run", "--rm", "bootstrap", "python3", "-c", py]
    code, out = run_cmd(cmd, check=False, capture=True)
    return code == 0, out.strip()


def run_bootstrap_once():
    """
    Runs the bootstrap service and waits for it to complete successfully.
    """
    print("→ Running bootstrap (schema init / seed)...")
    code, out = run_cmd(["docker", "compose", "up", "--no-deps", "--abort-on-container-exit", "bootstrap"],
                        check=False, capture=True)
    if code != 0:
        print(out)
        return False, out.strip()
    return True, ""


# config collection
def get_engine_settings(advanced=False):
    print("\nEngine Settings")

    settings = {}

    if advanced:
        override = prompt("Override Agent PSK?", "n", required=True).strip().lower()
        if override in ("y", "yes"):
            settings["agent_psk"] = prompt(
                "Agent PSK",
                "",
                required=True,
                is_password=True
            )

    return settings


def get_db_config():
    print("\n[1/4] Database Configuration")
    
    host = prompt("Database host", "mysql", required=True)
    port = prompt("Database port", "3306", required=True)
    name = prompt("Database name", "scoring_engine", required=True)
    user = prompt("Database user", "se_user", required=True)
    pw = prompt("Database password", "CHANGEME", required=True, is_password=True)

    uri = f"mysql://{user}:{pw}@{host}:{port}/{name}?charset=utf8mb4"
    return {
        "type": "mysql",
        "host": host,
        "port": port,
        "name": name,
        "user": user,
        "password": pw,
        "uri": uri,
    }


def get_redis_config():
    print("\n[2/4] Redis Configuration")
    redis_host = prompt("Redis host", "redis", required=True)
    redis_port = prompt("Redis port", "6379", required=True)
    redis_pw = prompt("Redis password (leave blank if none)", "", allow_blank=True)
    return {
        "cache_type": "redis",
        "redis_host": redis_host,
        "redis_port": redis_port,
        "redis_password": redis_pw,
    }


def get_competition_info():
    print("\n[3/4] Competition Info")
    name = prompt("Competition name", default=None, required=True)
    interval = prompt("Scoring interval (seconds)", "300", required=True)
    return {"competition_name": name, "scoring_interval": interval}


def get_admin_info():
    print("\n[4/4] Admin Account Setup")
    username = prompt("Admin username", "admin", required=True)
    pw = getpass.getpass("Admin password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if pw != pw2:
        print("Passwords do not match.")
        return get_admin_info()
    return {"admin_username": username, "admin_password": pw}


def confirm_summary(config):
    print("\nSetup Summary (secrets redacted):")
    print(json.dumps(redact_config_for_print(config), indent=4))
    confirm = input("Confirm and run automated setup? (y/n): ").lower()
    return confirm.startswith("y")

# non-interactive config 
def env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return v if v is not None and v != "" else default


def get_config_noninteractive():
    db_host = env("SE_DB_HOST", "mysql")
    db_port = env("SE_DB_PORT", "3306")
    db_name = env("SE_DB_NAME", "scoring_engine")
    db_user = env("SE_DB_USER", "se_user")
    db_pw = env("SE_DB_PASSWORD", "CHANGEME")
    db_uri = f"mysql://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

    redis_host = env("SE_REDIS_HOST", "redis")
    redis_port = env("SE_REDIS_PORT", "6379")
    redis_pw = env("SE_REDIS_PASSWORD", "")

    comp_name = env("SE_COMP_NAME", "Integration Test")
    scoring_interval = env("SE_SCORING_INTERVAL", "300")

    admin_user = env("SE_ADMIN_USER", "admin")
    admin_pw = env("SE_ADMIN_PASSWORD", "admin")

    cfg = {"deployment_mode": "docker"}
    cfg["engine"] = {}  
    cfg["database"] = {
        "type": "mysql",
        "host": db_host,
        "port": db_port,
        "name": db_name,
        "user": db_user,
        "password": db_pw,
        "uri": db_uri,
    }
    cfg["redis"] = {
        "cache_type": "redis",
        "redis_host": redis_host,
        "redis_port": redis_port,
        "redis_password": redis_pw,
    }
    cfg["competition"] = {"competition_name": comp_name, "scoring_interval": scoring_interval}
    cfg["admin"] = {"admin_username": admin_user, "admin_password": admin_pw}
    return cfg

# file writers
def write_env(config):
    with open(ENV_FILE, "w") as f:
        f.write(f"DB_URI={config['database']['uri']}\n")
        f.write(f"REDIS_HOST={config['redis']['redis_host']}\n")
        f.write(f"REDIS_PORT={config['redis']['redis_port']}\n")
        if config["redis"]["redis_password"]:
            f.write(f"REDIS_PASSWORD={config['redis']['redis_password']}\n")
        f.write(f"COMP_NAME={config['competition']['competition_name']}\n")
        f.write(f"ADMIN_USER={config['admin']['admin_username']}\n")
    print(f"Created {ENV_FILE}")


def _set_ini_value(text: str, key: str, value: str) -> str:
    """
    Replace `key = ...` (or `#key = ...`) with `key = value`.
    If key doesn't exist anywhere, append it under [OPTIONS].
    """
    # replace an active setting line
    pat_active = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=\s*.*$")
    if pat_active.search(text):
        return pat_active.sub(f"{key} = {value}", text)

    # replace a commented example line by uncommenting it
    pat_commented = re.compile(rf"(?m)^\s*#\s*{re.escape(key)}\s*=\s*.*$")
    if pat_commented.search(text):
        return pat_commented.sub(f"{key} = {value}", text)

    # otherwise, append right after [OPTIONS]
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        if line.strip() == "[OPTIONS]":
            lines.insert(i + 1, f"{key} = {value}\n")
            return "".join(lines)

    # fallback: append at end
    return text + f"\n{key} = {value}\n"


def write_engine_conf(config, out_path: Path):
    if not ENGINE_CONF_TEMPLATE.exists():
        raise FileNotFoundError(f"Template file not found: {ENGINE_CONF_TEMPLATE}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # start from the repo’s canonical config template
    text = ENGINE_CONF_TEMPLATE.read_text()

    # always patch DB + redis based on installer inputs
    text = _set_ini_value(text, "db_uri", config["database"]["uri"])
    text = _set_ini_value(text, "redis_host", config["redis"]["redis_host"])
    text = _set_ini_value(text, "redis_port", str(config["redis"]["redis_port"]))
    text = _set_ini_value(text, "redis_password", config["redis"].get("redis_password", ""))

    # only patch agent_psk if it was explicitly provided (advanced mode later)
    if config.get("engine") and "agent_psk" in config["engine"]:
        text = _set_ini_value(text, "agent_psk", config["engine"]["agent_psk"])

    out_path.write_text(text)
    print(f"Created {out_path}")


def safe_cleanup():
    # delete config artifacts
    try:
        if DOCKER_ENGINE_CONF.exists():
            DOCKER_ENGINE_CONF.unlink()
        if ENV_FILE.exists():
            ENV_FILE.unlink()
    except Exception:
        pass
    # tear down containers + volumes
    docker_compose_down_volumes()
    print("Rollback complete.")

def parse_args():
    p = argparse.ArgumentParser(description="Scoring Engine Setup Wizard")
    p.add_argument("--non-interactive", action="store_true", help="Read inputs from env vars and write config files only.")
    p.add_argument("--no-run", action="store_true", help="Write config files only; do not start docker or bootstrap.")
    return p.parse_args()

# main flow 
def main():
    
    args = parse_args()

    # non-interactive mode for testing
    if args.non_interactive:
        config = get_config_noninteractive()

        # write files and exit
        DOCKER_ENGINE_CONF.parent.mkdir(parents=True, exist_ok=True)
        write_engine_conf(config, DOCKER_ENGINE_CONF)
        write_env(config)

        print("\nNon-interactive mode complete (generated config files only).")
        print(f" - {DOCKER_ENGINE_CONF}")
        print(f" - {ENV_FILE}")
        return


    clear()
    print(
        """
Welcome to the Scoring Engine Setup Wizard
-------------------------------------------------------
This interactive installer will:
  - guide you through required configuration values
  - generate docker/engine.conf.inc for the Scorig Engine
Press Enter to accept the default values shown in brackets.
"""
    )

    # docker dependency checks up front
    require_docker()

    config = {"deployment_mode": "docker"}
    config["engine"] = get_engine_settings()
    config["database"] = get_db_config()
    config["redis"] = get_redis_config()
    config["competition"] = get_competition_info()
    config["admin"] = get_admin_info()

    if not confirm_summary(config):
        print("Setup cancelled. No files were generated.")
        return

    # write config first (compose bind-mount requires it for bootstrap container)
    # if validation fails, delete these files as rollback
    try:
        DOCKER_ENGINE_CONF.parent.mkdir(parents=True, exist_ok=True)
        write_engine_conf(config, DOCKER_ENGINE_CONF)
        write_env(config)
    except Exception as e:
        sys.exit(f"Failed to write configuration files: {e}")

    # start deps automatically
    docker_compose_up(["mysql", "redis"])

    # wait for services to be reachable inside the Docker network
    print("→ Waiting for MySQL to be reachable inside Docker network...")
    ok, err = wait_for_tcp_inside_network(config["database"]["host"], config["database"]["port"], timeout_s=120)
    if not ok:
        print(f"MySQL not reachable: {err}")
        rollback = input("Rollback (delete config + docker compose down -v)? (y/n): ").lower().startswith("y")
        if rollback:
            safe_cleanup()
        sys.exit("Exiting setup.")

    print("→ Waiting for Redis to be reachable inside Docker network...")
    ok, err = wait_for_tcp_inside_network(config["redis"]["redis_host"], config["redis"]["redis_port"], timeout_s=120)
    if not ok:
        print(f"Redis not reachable: {err}")
        rollback = input("Rollback (delete config + docker compose down -v)? (y/n): ").lower().startswith("y")
        if rollback:
            safe_cleanup()
        sys.exit("Exiting setup.")

    # validate credentials (real checks inside docker)
    print("→ Validating database credentials...")
    db_ok, db_err = test_db_uri_inside_docker(config["database"]["uri"], timeout_s=90)
    if not db_ok:
        print("\nDatabase credential test failed.")
        print(db_err)
        rollback = input("Rollback (delete config + docker compose down -v)? (y/n): ").lower().startswith("y")
        if rollback:
            safe_cleanup()
        sys.exit("Exiting setup.")

    print("→ Validating redis connectivity...")
    r_ok, r_err = test_redis_inside_docker(
        config["redis"]["redis_host"],
        config["redis"]["redis_port"],
        config["redis"].get("redis_password", "")
    )
    if not r_ok:
        print("\nRedis test failed.")
        print(r_err)
        rollback = input("Rollback (delete config + docker compose down -v)? (y/n): ").lower().startswith("y")
        if rollback:
            safe_cleanup()
        sys.exit("Exiting setup.")

    # run bootstrap to initialize schema + seed
    boot_ok, boot_err = run_bootstrap_once()
    if not boot_ok:
        print("\nBootstrap failed (schema init / seed).")
        print(boot_err)
        rollback = input("Rollback (delete config + docker compose down -v)? (y/n): ").lower().startswith("y")
        if rollback:
            safe_cleanup()
        sys.exit("Exiting setup.")

    print("\nSetup complete!")
    print(f"Generated configuration file for Docker mounts:\n - {DOCKER_ENGINE_CONF}")
    print("\nStart the full stack:")
    print("  docker compose up -d")
    print("\n(If already running) check status:")
    print("  docker compose ps")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup aborted by user.")