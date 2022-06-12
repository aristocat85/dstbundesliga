import datetime

from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from sleeper_wrapper import BaseApi


@dataclass
class NflState:
    week: int
    season_type: str
    season_start_date: datetime.datetime.date
    season: str
    previous_season: str
    leg: int
    league_season: str
    league_create_season: str
    display_week: int


class StateService(BaseApi):
    def __init__(self):
        self._base_state_url = "https://api.sleeper.app/state/{}".format("nfl")

    def get_state(self):
        state_data = cache.get("NflState")
        if not state_data:
            state_data = self._call(self._base_state_url)
            cache.set("NflState", state_data, timeout=60 * 60 * 24)

        return NflState(**state_data)

    def get_season(self):
        return self.get_state().season

    def get_previous_season(self):
        return self.get_state().previous_season

    def get_current_week(self):
        return self.get_state().week
