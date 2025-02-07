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



class CryptoOutput(BaseModel):
    chosen_coins: list[str] = Field(description="Scalping için seçilen en uygun 3 coinin sembolü")

def choose_coins():
    
    
    coin_data_2 = load_cache()
    
    if isinstance(coin_data_2, str) and "hata" in coin_data_2.lower():
        print(f"\nHata: {coin_data_2}")
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

