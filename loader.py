import requests

def load_pogo_data():
    params = {
        'mid': 0,
        'w': 4.46,
        'e': 5.03,
        'n': 51.05,
        's': 50.70,
        'gid': 0
    }
    reply = requests.get('https://d.fzi.ch/m.php', params=params)
    return reply.json()