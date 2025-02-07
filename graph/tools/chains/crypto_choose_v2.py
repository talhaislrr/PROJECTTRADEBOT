import requests
import pandas as pd
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from realtime_selector import load_cache
load_dotenv()

load_cache()

class CryptoChooser:
    def __init__(self):
        self.binance_url = 'https://api.binance.com/api/v3'

    def get_tradeable_coins(self):
        """Binance'de işlem gören coinleri analiz eder"""
        try:
            print("\n=== Binance API Verileri ===")
            
            # Binance verilerini al
            url = f'{self.binance_url}/ticker/24hr'
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Binance API Hatası: {response.status_code}")
                return "API hatası: Veriler alınamadı"
                
            data = response.json()
            
            # USDT çiftlerini filtrele
            usdt_pairs = [item for item in data if item['symbol'].endswith('USDT')]
            print(f"\nToplam USDT Çiftleri: {len(usdt_pairs)}")
            
            # DataFrame oluştur
            df = pd.DataFrame(usdt_pairs)
            
            # Veri tiplerini düzelt
            numeric_columns = ['volume', 'quoteVolume', 'priceChangePercent', 'lastPrice', 
                             'highPrice', 'lowPrice', 'count', 'priceChange']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['coin'] = df['symbol'].str.replace('USDT', '')
            
            # Kısa vadeli scalping için filtreleme
            mask = (
                (df['volume'] > 1000000) &      # En az 1M USDT hacim (likidite için)
                (df['count'] > 10000) &         # Yüksek işlem sayısı (spread düşük olsun)
                (df['lastPrice'] > 0.00001) &   # Çok düşük fiyatlı coinleri ele
                (abs(df['priceChangePercent']) > 2) &  # Son 24s'de en az %2 hareket
                # Büyük ve stabil coinleri çıkar
                (~df['coin'].isin(['BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'BUSD', 'XRP', 'ADA', 'DOGE', 'DOT', 'MATIC', 'SOL', 'AVAX', 'SHIB', 'TRX', 'LINK', 'UNI', 'LTC']))
            )
            df_filtered = df.loc[mask].copy()
            
            # Anlık momentum skoru (son fiyat değişimi)
            df_filtered.loc[:, 'momentum_score'] = abs(df_filtered['priceChange'] / df_filtered['lastPrice'] * 100)
            
            # Volatilite skoru (yüksek-düşük farkı)
            df_filtered.loc[:, 'volatility'] = ((df_filtered['highPrice'] - df_filtered['lowPrice']) / df_filtered['lowPrice'] * 100)
            df_filtered.loc[:, 'volatility_score'] = df_filtered['volatility'].rank(pct=True)
            
            # Kısa vadeli volatilite bonusu
            df_filtered.loc[:, 'volatility_bonus'] = df_filtered['volatility'].apply(
                lambda x: 3.0 if x > 5 else     # %5'den fazla spread
                         2.0 if x > 3 else      # %3'den fazla spread
                         1.5 if x > 2 else      # %2'den fazla spread
                         1.0                     # Normal spread
            )
            
            # Hacim skoru (scalping için önemli)
            df_filtered.loc[:, 'volume_score'] = df_filtered['volume'].apply(lambda x: min(3.0, max(0.5, (x / 5000000))))
            
            # İşlem sayısı skoru (spread için önemli)
            df_filtered.loc[:, 'trade_score'] = df_filtered['count'].apply(lambda x: min(2.0, max(0.5, (x / 20000))))
            
            # Anlık trend skoru
            df_filtered.loc[:, 'trend_score'] = df_filtered['priceChangePercent'].apply(
                lambda x: 2.0 if abs(x) > 3 else     # Son 1s'de %3'den fazla hareket
                         1.5 if abs(x) > 2 else      # Son 1s'de %2'den fazla hareket
                         1.0 if abs(x) > 1 else      # Son 1s'de %1'den fazla hareket
                         0.5                          # Yavaş hareket
            )
            
            # Toplam skor (scalping odaklı)
            df_filtered.loc[:, 'total_score'] = (
                df_filtered['momentum_score'] * 0.35 +          # Anlık momentum %35
                df_filtered['volatility_score'] * df_filtered['volatility_bonus'] * 0.25 +  # Volatilite %25
                df_filtered['volume_score'] * 0.25 +            # Hacim %25 (likidite önemli)
                df_filtered['trade_score'] * 0.15               # İşlem sayısı %15
            )
            
            # Skora göre sırala
            df_filtered = df_filtered.sort_values('total_score', ascending=False)
            
            # En iyi 10 coini seç
            top_coins = df_filtered.head(10)
            
            result = f"En İyi Scalping Fırsatları (10 Coin):\n\n"
            for _, row in top_coins.iterrows():
                result += f"Coin: {row['coin']}\n"
                result += f"Fiyat: ${row['lastPrice']:.6f}\n"
                result += f"Son 1s Değişim: %{row['priceChangePercent']:.2f}\n"
                result += f"Spread: %{row['volatility']:.2f}\n"
                result += f"24s Hacim: {row['volume']:,.2f} USDT\n"
                result += f"İşlem Sayısı: {row['count']:,}\n"
                result += f"Momentum Skoru: {row['momentum_score']:.2f}\n"
                result += f"Volatilite Bonus: {row['volatility_bonus']:.1f}x\n"
                result += f"Toplam Skor: {row['total_score']:.3f}\n"
                result += "-" * 50 + "\n"
            
            return result
            
        except Exception as e:
            print(f"\nHata detayı: {str(e)}")
            return "Coin listesi alınırken hata oluştu"

class CryptoOutput(BaseModel):
    chosen_coins: list[str] = Field(description="Scalping için seçilen en uygun 3 coinin sembolü")

def choose_coins():
    crypto_chooser = CryptoChooser()
    coin_data = crypto_chooser.get_tradeable_coins()
    coin_data_2 = load_cache()
    
    if isinstance(coin_data, str) and "hata" in coin_data.lower():
        print(f"\nHata: {coin_data}")
        return []

    llm = ChatOpenAI(model="gpt-4", temperature=0.7)  # Daha tutarlı seçimler için
    structured_llm = llm.with_structured_output(CryptoOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Sen profesyonel bir SCALPING traderısın. Çok kısa vadeli (5-15dk) al-sat yapıyorsun.
        Yukarıdaki piyasa verilerini analiz et ve SCALPING için en uygun 3 coini seç.
        
        Seçim Kriterlerin:
        1. ANLIK HAREKET (%1-3 arası)
        2. YÜKSEK LİKİDİTE (hızlı giriş/çıkış)
        3. DÜŞÜK SPREAD (al-sat farkı)
        4. YÜKSEK İŞLEM SAYISI
        5. NET TREND (long/short sinyali)
        
        KESİNLİKLE:
        - Sadece son 1 SAATLİK verilere bak
        - Spread %0.5'den düşük olsun
        - İşlem hacmi yüksek olsun
        - Momentum NET olsun (trend belli olsun)
        
        SCALPING KURALLARI:
        - Maksimum 15 DAKİKA pozisyon tut
        - %1-2 kar hedefi koy
        - Stop-loss %0.5-1 olsun
        - Sadece 1m/5m grafiklere bak
        NOT:
        - Seçilen coinler ['BTC', 'ETH', 'XRP'] gibi popüler coinler yerine daha kar potansiyeli yüksek ve 1-2-3-4-5-6 saat içinde işlemden çıkabilecek coinler olsun.
        Verilen coin listesinden, bu kriterlere göre SCALPING için en uygun 3 coini seç."""),
        ("user", "Yukarıdaki coin listesinden, SCALPING için en uygun 3 coini seç.")
    ])

    chain = prompt | structured_llm

    try:
        result = chain.invoke({
            "coin_data": coin_data_2
        })
        
        if not isinstance(result.chosen_coins, list) or len(result.chosen_coins) != 3:
            print("\nHata: Model geçersiz format döndürdü")
            return []
            
        print("\nSeçilen Scalping Coinleri:", result.chosen_coins)
        return result.chosen_coins
        
    except Exception as e:
        print(f"\nCoin seçimi sırasında hata oluştu: {str(e)}")
        return []

if __name__ == "__main__":
    chosen_coins = choose_coins()

