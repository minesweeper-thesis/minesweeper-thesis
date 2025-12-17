from datetime import datetime

from backend.services.multi.constants import COUNTDOWN_DELAY, START_DELAY


def calc_round_start_times():
    countdown_to = datetime.now() + COUNTDOWN_DELAY
    start_at = countdown_to + START_DELAY
    return countdown_to, start_at
