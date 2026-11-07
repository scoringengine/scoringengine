"""Worker tool packs: route each check to a worker that has its tools installed.

Heavy tooling (browsers, RDP/X11, database clients) lives in optional worker
images. Each check class declares the pack it needs via ``REQUIRES_PACK``
(default ``core``). The engine sends a check to the queue for that pack:

    core pack   -> "<worker_queue>"            e.g. "main"
    other packs -> "<worker_queue>.<pack>"     e.g. "main.browser"

A worker consumes the queues for the packs installed in its image
(``SCORINGENGINE_WORKER_PACKS``, set per Dockerfile target). The full image
installs every pack, so the default single-worker setup keeps working.
"""

from scoring_engine.config import config

DEFAULT_PACK = "core"
PACKS = ("core", "db", "rdp", "browser", "adcs")


def check_pack(check_class):
    return getattr(check_class, "REQUIRES_PACK", DEFAULT_PACK)


def queue_for(base_queue, pack):
    return base_queue if pack == DEFAULT_PACK else "{0}.{1}".format(base_queue, pack)


def parse_packs(value):
    """'core, db' -> ['core', 'db']. Raises ValueError for unknown packs."""
    packs = [p.strip() for p in str(value).split(",") if p.strip()]
    unknown = [p for p in packs if p not in PACKS]
    if unknown:
        raise ValueError("Unknown worker pack(s) {0}; valid packs: {1}".format(unknown, ", ".join(PACKS)))
    return packs


def worker_queues(base_queue, packs):
    return [queue_for(base_queue, pack) for pack in packs]


def service_queue(service, check_class):
    return queue_for(service.worker_queue, check_pack(check_class))


_pack_by_check_name = None


def pack_by_check_name():
    """{check class name: pack} for every installed check (loaded once)."""
    global _pack_by_check_name
    if _pack_by_check_name is None:
        from scoring_engine.engine.engine import Engine  # lazy: engine imports this module

        _pack_by_check_name = {c.__name__: check_pack(c) for c in Engine.load_check_files(config.checks_location)}
    return _pack_by_check_name


def queue_for_service(service):
    """Queue a service's checks are sent to, from its check_name."""
    return queue_for(service.worker_queue, pack_by_check_name().get(service.check_name, DEFAULT_PACK))
