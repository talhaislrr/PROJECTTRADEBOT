import json
import pandas as pd
import requests
import pandas as pd
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()
CACHE_FILE = 'cache.json'
selected_coins = []  # Global değişken

# Cache dosyasını yükler
def load_cache():
    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Cache yüklenirken hata: {str(e)}")
        return None

# Potansiyel coinleri seçer, ek olarak hacim ve işlem sayısı skorlarıyla trade açma potansiyellerini de değerlendirir
def select_potential_coins():
    global selected_coins
    data = load_cache()
    if data is None:
        print("Cache verisi alınamadı.")
        return
    
    # Sadece USDT çiftlerini al
    df = pd.DataFrame([d for d in data if d.get('symbol', '').endswith('USDT')])
    
    # Sayısal kolonları dönüştür
    numeric_columns = ['volume', 'quoteVolume', 'priceChangePercent', 'lastPrice', 
                       'highPrice', 'lowPrice', 'count', 'priceChange']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Coin sembolünü oluştur
    df['coin'] = df['symbol'].str.replace('USDT', '')
    
    # Potansiyel coinler için filtreleme
    # - Yüksek hacim ve işlem sayısı
    # - En az %5 fiyat değişimi ve en fazla %100
    # - Büyük ve stabil coinler hariç
    mask = (
        (df['volume'] > 1000000) &
        (df['count'] > 10000) &
        (df['lastPrice'] > 0.00001) &
        (abs(df['priceChangePercent']) > 5) &
        (abs(df['priceChangePercent']) < 100) &
        (~df['coin'].isin(['BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'BUSD',
                           'XRP', 'ADA', 'DOGE', 'DOT', 'MATIC', 'SOL', 'AVAX',
                           'SHIB', 'TRX', 'LINK', 'UNI', 'LTC']))
    )
    df_filtered = df.loc[mask].copy()
    
    if df_filtered.empty:
        print("Uygun potansiyel coin bulunamadı.")
        return
    
    # Anlık momentum: fiyat değişikliğinin mutlak değeri
    df_filtered['momentum'] = abs(df_filtered['priceChangePercent'])
    
    # Volatilite: (yüksek - düşük) / düşük * 100
    df_filtered['volatility'] = ((df_filtered['highPrice'] - df_filtered['lowPrice']) / df_filtered['lowPrice'] * 100)
    
    # Ek özellikler: Hacim ve İşlem Sayısı Skorları
    # Hacim skoru: Coin'in hacmini milyon USD'lik birimlere bölüp, maksimum 5 puanla sınırlandırıyoruz
    df_filtered['volume_score'] = df_filtered['volume'].apply(lambda x: min(5, x / 1e6))
    # İşlem sayısı skoru: İşlem sayısını 10K'lık birimlere bölüp, maksimum 5 puanla sınırlıyoruz
    df_filtered['trade_score'] = df_filtered['count'].apply(lambda x: min(5, x / 10000))
    
    # Toplam potansiyel skoru: momentum, volatilite, hacim ve işlem sayısı skorlarının ağırlıklı ortalaması
    # Ağırlıklar: momentum %50, volatilite %30, hacim %10, işlem sayısı %10
    df_filtered['total_score'] = (df_filtered['momentum'] * 0.5 +
                                  df_filtered['volatility'] * 0.3 +
                                  df_filtered['volume_score'] * 0.1 +
                                  df_filtered['trade_score'] * 0.1)
    
    # Skora göre sırala
    df_filtered = df_filtered.sort_values('total_score', ascending=False)
    
    # En iyi 3 coin
    top_coins = df_filtered.head(3)
    coins = df_filtered


    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    class CryptoOutput(BaseModel):
        chosen_coins: list[str] = Field(description="Scalping için seçilen en uygun 3 coinin sembolü. Çıktı: [BTC, ETH, XRP] gibi sonundaki usdt'yi kaldırın")
    structured_llm = llm.with_structured_output(CryptoOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Sen profesyonel bir SCALPING traderısın. Çok kısa vadeli (5-15dk) al-sat yapıyorsun.
        Yukarıdaki piyasa verilerini analiz et ve SCALPING için en uygun 3 coini seç.
        
        Seçim Kriterlerin kendin belirleyebilirsin.
        Tek bir şart var o da seçtiğin coin iş arkadaşına gönderilecek ve o da anlık haber ve teknik analiz yapıp işleme girecek, coini maximum 6 saat içinde işlemden çıkacak şekilde seç.
        
        """),
        ("user", f"{coins}")
    ])

    chain = prompt | structured_llm

    
    result = chain.invoke({
        "coin_data": coins
    })
    selected_coins = result.chosen_coins
    #print("LLM Seçilen Coinler:", selected_coins)
    
    #print("Potansiyeli yüksek coinler:\n")
    #for _, row in top_coins.iterrows():
        #print(f"Coin: {row['coin']} - Fiyat: ${row['lastPrice']:.6f} - Değişim: %{row['priceChangePercent']:.2f} - "
              #f"Volatilite: %{row['volatility']:.2f} - Volume Score: {row['volume_score']:.2f} - "
              #f"Trade Score: {row['trade_score']:.2f} - Toplam Skor: {row['total_score']:.2f}")
    
    return top_coins['coin'].tolist(), selected_coins


if __name__ == "__main__":
    coins, llm_coins = select_potential_coins()
    print("Seçilen Coinler:", llm_coins)
    
   
    
    
    
    
    
    