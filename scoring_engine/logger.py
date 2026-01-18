import logging

logger = logging.getLogger('scoring_engine')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

db_logger = logging.getLogger('scoring_engine.db')
db_logger.setLevel(logging.INFO)
db_logger.addHandler(handler)