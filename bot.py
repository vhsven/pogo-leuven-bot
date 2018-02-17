#TODO alert system

import os
import threading
import time
import telepot

from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultVenue, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from geopy.geocoders import GoogleV3

from loader import load_pogo_data
from spawns import Spawns
from raids import Raids

geolocator = GoogleV3(api_key=os.environ["POGOLEUVENAPIKEY"])
bot = telepot.Bot(os.environ["POGOLEUVENBOTKEY"])
answerer = telepot.helper.Answerer(bot)
team_names = ['Blank', 'Mystic', 'Valor', 'Instinct']
default_response = [
    InlineQueryResultArticle(id='no-result0', title="Supported commands:", input_message_content=InputTextMessageContent(message_text="-")),
    InlineQueryResultArticle(id='no-result1', title="raidboss <pkmn>", input_message_content=InputTextMessageContent(message_text="-")),
    InlineQueryResultArticle(id='no-result2', title="raidlvl <minlvl>", input_message_content=InputTextMessageContent(message_text="-")),
    InlineQueryResultArticle(id='no-result3', title="spawn <pkmn>", input_message_content=InputTextMessageContent(message_text="-")),
    #InlineQueryResultArticle(id='no-result4', title="...", input_message_content=InputTextMessageContent(message_text="-"))
]

def get_error_response(msg):
    return [
        InlineQueryResultArticle(id='error-0', title="Error:", input_message_content=InputTextMessageContent(message_text="-")),
        InlineQueryResultArticle(id='error-1', title=msg, input_message_content=InputTextMessageContent(message_text=msg))
    ]

def on_inline_query(msg):

    def format_timedelta(td):
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        hours, minutes, seconds = int(hours), int(minutes), int(seconds)
        return f'{hours:02}:{minutes:02}:{int(seconds):02}'

    def get_spawns(data, my_loc, query):
        spawns = Spawns(data['pokemons'], my_loc)
        results = spawns.find(query, max=10)
        print(f'Found {len(results.index)} spawns for "{query}"')
        # print(results.columns)
        # 0 'eid'
        # 1 'disappear_time',
        # 2 'latitude',
        # 3 'longitude',
        # 4 'pokemon_id',
        # 5 'pokemon_name',
        # 6 'remaining',
        # 7 'dist'

        return [InlineQueryResultVenue(
            id=str(row[0]),
            latitude=row[2],
            longitude=row[3],
            title=f'{row[5].capitalize()} ({row[7]}m | {format_timedelta(row[6])})',
            address=geolocator.reverse((row[2], row[3]),exactly_one=True).address
        ) for row in results.itertuples()]

    def get_raids_by_level(data, my_loc, min_level):
        raids = Raids(data['gyms'], my_loc)
        bosses = raids.find_level(min_level, max=10)
        return [InlineQueryResultVenue(
            id=str(row[0]),
            latitude=row[3],
            longitude=row[4],
            title=f'[{team_names[row[12]]}] {row[14].capitalize()} Raid ({row[16]}m | {format_timedelta(row[15])})',
            address=geolocator.reverse((row[3], row[4]),exactly_one=True).address,
        ) for row in bosses.itertuples()]

    def get_raids_by_boss(data, my_loc, query):
        raids = Raids(data['gyms'], my_loc)
        bosses = raids.find_boss2(query, max=10)
        
        #print(bosses.columns)
        #  0 'index'
        #  1 'cp', 
        #  2 'gym_points', 
        #  3 'latitude', 
        #  4 'longitude', 
        #  5 'lvl', 
        #  6 'm1', 
        #  7 'm2', 
        #  8 'pid',
        #  9 't1', 
        # 10 't2', 
        # 11 't3', 
        # 12 'team_id', 
        # 13 'ts', 
        # 14 'pokemon_name', 
        # 15 'remaining'
        # 16 'dist', 

        return [InlineQueryResultVenue(
            id=str(row[0]),
            latitude=row[3],
            longitude=row[4],
            #thumb_url=f'http://assets.pokemon.com/assets/cms2/img/pokedex/detail/{row[8]:03}.png',
            title=f'[{team_names[row[12]]}] {row[14].capitalize()} Raid ({row[16]}m | {format_timedelta(row[15])})',
            address=geolocator.reverse((row[3], row[4]),exactly_one=True).address,
        ) for row in bosses.itertuples()]

    def compute():
        _, _, query_string = telepot.glance(msg, flavor='inline_query')
        user = msg['from']['username']
        location = msg.get('location')
        print('[%s] @%s: %s @ %s' % (threading.current_thread().name, user, query_string, location))
        my_loc = (50.8789942, 4.7003497) if location is None else (location['latitude'], location['longitude'])
        
        parts = query_string.split(sep=' ')

        if len(parts) == 2:
            if parts[0] == 'raidboss' and len(parts[1]) > 2:
                data = load_pogo_data()
                return get_raids_by_boss(data, my_loc, parts[1])
            if parts[0] == 'raidlvl' and parts[1].isdigit():
                data = load_pogo_data()
                return get_raids_by_level(data, my_loc, int(parts[1]))
            if parts[0] == 'spawn' and len(parts[1]) > 2:
                data = load_pogo_data()
                return get_spawns(data, my_loc, parts[1])
        
        return default_response

    def compute_wrapper():
        try:
            result = compute()
            #print(result)
            return result
        except BaseException as err:
            return get_error_response(str(err))

    answerer.answer(msg, compute_wrapper)

def on_chosen_inline_result(msg):
    result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
    print('Chosen Inline Result:', result_id, from_id, query_string)

MessageLoop(bot, {
    'inline_query': on_inline_query, 
    'chosen_inline_result': on_chosen_inline_result
}).run_as_thread()

print('Listening ...')

while True:
    time.sleep(10)