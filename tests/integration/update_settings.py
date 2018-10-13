import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

# This simply updates the timeouts so that we don't have to wait that long
from mock_config import MockConfig
sys.modules['scoring_engine.config'] = MockConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)), './engine.conf.inc'))

from scoring_engine.db import session
from scoring_engine.models.setting import Setting

round_time_sleep_setting = Setting.get_setting('round_time_sleep')
# Only sleep 3 seconds between rounds
round_time_sleep_setting.value = '3'
session.add(round_time_sleep_setting)

worker_refresh_time_setting = Setting.get_setting('worker_refresh_time')
# Only wait 1 second for polling in progress checks
worker_refresh_time_setting.value = '3'
session.add(worker_refresh_time_setting)

session.commit()
