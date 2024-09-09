from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
import time

app = Flask(__name__)

USERNAME = 'unique-crl6d'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'}

# Кэширование данных
cache = {
    'stats': None,
    'stats_time': None,
    'games': None,
    'games_time': None
}

CACHE_TIMEOUT = timedelta(minutes=10)  # Время жизни кэша

def get_chess_stats(username):
    now = datetime.now()
    if cache['stats'] and cache['stats_time'] > now - CACHE_TIMEOUT:
        return cache['stats']
    
    url = f"https://api.chess.com/pub/player/{username}/stats"
    response = requests.get(url, headers=headers)
    print(f"Статус код для статистики: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        cache['stats'] = data
        cache['stats_time'] = now
        print(f"Статистика игрока: {data}")
        return data
    else:
        print("Ошибка при получении статистики")
        return None

def get_daily_games(username):
    now = datetime.now()
    if cache['games'] and cache['games_time'] > now - CACHE_TIMEOUT:
        return cache['games']
    
    today_date = now.strftime('%Y-%m-%d')
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(url, headers=headers)
    print(f"Статус код для архивов игр: {response.status_code}")
    
    if response.status_code == 200:
        archives = response.json().get('archives', [])
        games_today = []
        
        for archive_url in archives:
            games_response = requests.get(archive_url, headers=headers)
            if games_response.status_code == 200:
                games = games_response.json().get('games', [])
                print(f"Игры из архива {archive_url}: {games}")
                for game in games:
                    game_date = datetime.fromtimestamp(game['end_time']).strftime('%Y-%m-%d')
                    print(f"Дата игры: {game_date}, Сегодняшняя дата: {today_date}")
                    if game_date == today_date:
                        games_today.append(game)
        
        print(f"Игры за сегодня: {games_today}")
        cache['games'] = games_today
        cache['games_time'] = now
        return games_today
    else:
        print("Ошибка при получении архивов игр")
        return []

@app.route('/')
def index():
    print("Главная страница загружается...")
    
    stats = get_chess_stats(USERNAME)
    games = get_daily_games(USERNAME)

    if stats:
        rapid_rating = stats.get('chess_rapid', {}).get('last', {}).get('rating', 'N/A')
        blitz_rating = stats.get('chess_blitz', {}).get('last', {}).get('rating', 'N/A')
        bullet_rating = stats.get('chess_bullet', {}).get('last', {}).get('rating', 'N/A')
    else:
        rapid_rating = blitz_rating = bullet_rating = 'N/A'

    wins = sum(1 for game in games if (game['white']['username'] == USERNAME and game['white']['result'] == 'win') or
               (game['black']['username'] == USERNAME and game['black']['result'] == 'win'))
    losses = sum(1 for game in games if (game['white']['username'] == USERNAME and game['white']['result'] == 'loss') or
                 (game['black']['username'] == USERNAME and game['black']['result'] == 'loss'))
    draws = sum(1 for game in games if (game['white']['username'] == USERNAME and game['white']['result'] == 'draw') or
                (game['black']['username'] == USERNAME and game['black']['result'] == 'draw'))

    total_games = len(games)
    winrate = round((wins / total_games * 100), 1) if total_games > 0 else 0

    color = "green" if winrate >= 50 else "red"

    return render_template('index.html', 
                           rapid_rating=rapid_rating, 
                           blitz_rating=blitz_rating,
                           bullet_rating=bullet_rating, 
                           winrate=winrate, 
                           total_games=total_games, 
                           color=color)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)