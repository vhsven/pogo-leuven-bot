import numpy as np
import pandas as pd
import pytz
from geopy.distance import vincenty
from consts import POKE_NAMES

class Raids:
    def __init__(self, gyms, coords):
        self.df = Raids._parse_raids(gyms)
        self.update_dist(coords)

    @staticmethod
    def _parse_raids(gyms):
        df_gyms = pd.DataFrame.from_dict(gyms)
        df_gyms.set_index('gym_id', inplace=True)
        df_gyms.drop_duplicates(inplace=True)
        for column in ['lvl', 'pid', 'm1', 'm2', 'cp', 't1', 't2', 't3']:
            df_gyms[column] = df_gyms[column] if column in df_gyms else np.nan
        df_gyms['pokemon_name'] = df_gyms.pid.apply(lambda id: POKE_NAMES[int(id)] if not np.isnan(id) else '')
        df_gyms['remaining'] = pd.Timedelta('nan')
        df_gyms.fillna(-1, inplace=True)
        df_gyms.ts = pd.to_datetime(df_gyms.ts, unit='s')
        df_gyms.ts = df_gyms.ts.dt.tz_localize('UTC').dt.tz_convert('Europe/Brussels')
        
        return Raids._parse_raids_from_gyms(df_gyms)
        

    @staticmethod
    def _parse_raids_from_gyms(df_gyms):
        df_raids = df_gyms[df_gyms.lvl >= 0]
        df_raids.lvl = df_raids.lvl.astype(int)
        df_raids.pid = df_raids.pid.astype(int)
        df_raids.m1 = df_raids.m1.astype(int)
        df_raids.m2 = df_raids.m2.astype(int)
        df_raids.cp = df_raids.cp.astype(int)
        df_raids.t1 = pd.to_datetime(df_raids.t1, unit='s')
        df_raids.t1 = df_raids.t1.dt.tz_localize('UTC').dt.tz_convert('Europe/Brussels')
        df_raids.t2 = pd.to_datetime(df_raids.t2, unit='s')
        df_raids.t2 = df_raids.t2.dt.tz_localize('UTC').dt.tz_convert('Europe/Brussels')
        df_raids.t3 = pd.to_datetime(df_raids.t3, unit='s')
        df_raids.t3 = df_raids.t3.dt.tz_localize('UTC').dt.tz_convert('Europe/Brussels')
        return df_raids

    def update_dist(self, coords):
        dist = self.df.apply(lambda r: int(vincenty(coords, (r.latitude, r.longitude)).m), axis=1)
        if not dist.empty:
            self.df['dist'] = dist
            self.df.sort_values('dist', inplace=True)

    def find_boss(self, name, max=None):
        selected = self.df[self.df.pokemon_name == name.lower()]
        selected['remaining'] = selected.t3 - pd.datetime.now().astimezone(pytz.timezone('Europe/Brussels'))
        selected = selected[selected.remaining.dt.days >= 0]
        return selected.head(max) if max else selected

    def find_boss2(self, name, max=None):
        selected = self.df[self.df.pokemon_name.str.startswith(name.lower())]
        selected['remaining'] = selected.t3 - pd.datetime.now().astimezone(pytz.timezone('Europe/Brussels'))
        selected = selected[selected.remaining.dt.days >= 0]
        return selected.head(max) if max else selected

    def find_level(self, min_level, max=None):
        selected = self.df[self.df.lvl >= min_level]
        selected['remaining'] = selected.t3 - pd.datetime.now().astimezone(pytz.timezone('Europe/Brussels'))
        selected = selected[selected.remaining.dt.days >= 0]
        return selected.head(max) if max else selected