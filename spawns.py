import pandas as pd
import pytz
from geopy.distance import vincenty
from consts import POKE_NAMES

class Spawns:
    def __init__(self, spawns, coords):
        self.df = Spawns._parse_spawns(spawns)
        self.update_dist(coords)

    @staticmethod
    def _parse_spawns(spawns):
        df = pd.DataFrame.from_dict(spawns)
        df.set_index('eid', inplace=True)
        df.drop_duplicates(inplace=True)
        df.disappear_time = pd.to_datetime(df.disappear_time, unit='s')
        df.disappear_time = df.disappear_time.dt.tz_localize('UTC').dt.tz_convert('Europe/Brussels')
        df['pokemon_name'] = df.pokemon_id.apply(lambda id: POKE_NAMES[id])
        df['remaining'] = pd.Timedelta('nan')
        return df

    def update_dist(self, coords):
        self.df['dist'] = self.df.apply(lambda r: int(vincenty(coords, (r.latitude, r.longitude)).m), axis=1)
        self.df.sort_values('dist', inplace=True)

    def find(self, name, max=None):
        selected = self.df[self.df.pokemon_name.str.startswith(name.lower())]
        selected['remaining'] = selected.disappear_time - pd.datetime.now().astimezone(pytz.timezone('Europe/Brussels'))
        selected = selected[selected.remaining.dt.days >= 0]
        return selected.head(max) if max else selected