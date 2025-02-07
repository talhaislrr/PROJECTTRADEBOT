import requests
import json
import time
from datetime import datetime

BINANCE_URL = 'https://api.binance.com/api/v3'
CACHE_FILE = 'cache.json'


def fetch_binance_data():
    url = f"{BINANCE_URL}/ticker/24hr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"{datetime.now()} - Başarılı: {len(data)} adet ticker çekildi.")
            return data
        else:
            print(f"{datetime.now()} - Binance API Hatası: {response.status_code}")
            return None
    except Exception as e:
        print(f"{datetime.now()} - Veri çekme hatası: {str(e)}")
        return None


def update_cache():
    data = fetch_binance_data()
    if data is not None:
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            print(f"{datetime.now()} - Cache güncellendi.")
        except Exception as e:
            print(f"{datetime.now()} - Cache yazma hatası: {str(e)}")
    else:
        print(f"{datetime.now()} - Cache güncellenemedi, veri alınamadı.")


def start_cache_scheduler(interval=180):
    # interval: saniye cinsinden (örneğin 180 saniye = 3 dakika)
    print(f"Cache scheduler başlatıldı. Her {interval} saniyede bir güncellenecek.")
    while True:
        update_cache()
        time.sleep(interval)


if __name__ == '__main__':
    start_cache_scheduler() 