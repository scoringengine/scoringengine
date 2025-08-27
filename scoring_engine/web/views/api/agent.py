from flask import request, make_response, abort
from flask_login import current_user, login_required
from sqlalchemy import desc, func, exists
from sqlalchemy.sql.expression import and_
from datetime import datetime, timedelta
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from hashlib import sha256
import json
import os

from scoring_engine.cache import agent_cache as cache
from scoring_engine.db import session
from scoring_engine.models.flag import Flag, Solve, Platform
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.setting import Setting

from . import mod

cache_dict = {}  # TODO - This is a dev hack. Real users should be using the flask-caching cache to store values
AESGCM_NONCE_LENGTH = 12

class BtaPayloadEncryption:
    def __init__(self, psk: str, team_name: str):
        key = BtaPayloadEncryption.generate_key(psk, team_name)
        self.crypto = AESGCM(key)

    def encrypt(self, msg: str | bytes) -> bytes:
        if isinstance(msg, str):
            msg = msg.encode()
        nonce = os.urandom(AESGCM_NONCE_LENGTH)
        return nonce + self.crypto.encrypt(nonce, msg, None)

    def decrypt(self, msg: bytes) -> str:
        nonce, msg = msg[:AESGCM_NONCE_LENGTH], msg[AESGCM_NONCE_LENGTH:]
        return self.crypto.decrypt(nonce, msg, None).decode()

    def dumps(self, payload: dict) -> bytes:
        return self.encrypt(json.dumps(payload))

    def loads(self, payload: bytes) -> dict:
        return json.loads(self.decrypt(payload))

    @staticmethod
    def generate_key(psk: str, team_name: str) -> bytes:
        return sha256((team_name + psk).encode()).digest()


@mod.route("/api/agent/checkin", methods=["POST"])
def agent_checkin_post():
    team_input = request.args.get("t", None)
    if team_input is None:
        abort(400)

    psk = Setting.get_setting("agent_psk").value
    crypter = BtaPayloadEncryption(psk, team_input)
    try:
      data = crypter.loads(request.get_data())
    except InvalidTag:
        # bad decryption
        abort(417)

    if data.get("team", None) != team_input:
        abort(418)

    team_input = data.get("team", None)
    host = data.get("host", None)
    platform = Platform(data.get("plat", None))

    if team_input is None or host is None or platform is None:
        abort(400)

    team = session.query(Team).filter_by(name=team_input).first()

    if team is None or not team.is_blue_team:
        abort(400)

    flags = data.get("flags", [])
    if len(flags) > 0:
        flags = session.query(Flag).filter(
                and_(
                    Flag.id.in_(flags),
                    Flag.dummy == False
                )
            ).all()
        solves = [
            Solve(
                host=host,
                team=team,
                flag=flag,
            )
            for flag in flags
        ]
        session.add_all(solves)

    result = do_checkin(team, host, platform)
    return make_response(crypter.dumps(result), 200, {'Content-Type': 'application/octet-stream'})


def do_checkin(team, host, platform):
    now = datetime.utcnow()
    # show upcoming flags a little bit early so red team can plant them
    # and implants that might stop checking in still get the next set of flags
    early = now + timedelta(minutes=int(Setting.get_setting("agent_show_flag_early_mins").value))
    # get unsolved flags for this team and host and for this time period
    flags = (
        session.query(Flag)
        .filter(
            and_(
                Flag.platform == platform,
                early > Flag.start_time,
                now < Flag.end_time,
            )
        )
        .filter(Flag.id.not_in(session.query(Solve.flag_id).filter(and_(Solve.host == host, Solve.team == team))))
    ).all()

    res = {
        "flags": [f.as_dict() for f in flags],
        "config": {
            "checkin_interval": {
                "secs": int(Setting.get_setting("agent_checkin_interval_sec").value),
                "nanos": 0,
            }
        },
        "timestamp": int(datetime.utcnow().timestamp()),
    }

    res_cache = {
        "config": {
            "checkin_interval": {
                "secs": int(Setting.get_setting("agent_checkin_interval_sec").value),
                "nanos": 0,
            }
        },
        "timestamp": int(datetime.utcnow().timestamp()),
    }

    # TODO - this is a gross dev hack
    cache_type = cache.config["CACHE_TYPE"]
    if cache_type == "null" or cache_type.endswith("NullCache"):
        cache_dict[host] = now
        # print(cache_dict)
    else:
        cache.set(host, res_cache)
        # print(cache.get(host))

    return res
