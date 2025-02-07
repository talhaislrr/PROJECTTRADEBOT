import requests
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        
    def get_news_data(self, coin):
        """NewsAPI'den kripto haberleri getirir"""
        try:
            url = "https://newsapi.org/v2/everything"
            
            # Son 3 gündeki haberler
            three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            params = {
                'q': f'(cryptocurrency OR crypto) AND {coin}',
                'from': three_days_ago,
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.news_api_key,
                'pageSize': 10
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                news_data = []
                for article in articles:
                    if article['title'] and article['description']:  # Boş haberleri filtrele
                        news_data.append({
                            'title': article['title'],
                            'description': article['description'],
                            'source': article['source']['name'],
                            'published_at': article['publishedAt'],
                            'url': article['url']
                        })
                return news_data[:5]  # En alakalı 5 haber
            return []
            
        except Exception as e:
            print(f"Haber getirme hatası ({coin}): {e}")
            return []

    def get_market_data(self, coin):
        """Binance API'den piyasa verilerini getirir"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {
                'symbol': f'{coin}USDT'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            return {
                'current_price': float(data['lastPrice']),
                'price_change_24h': float(data['priceChangePercent']),
                'volume_24h': float(data['volume']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'total_trades': int(data['count'])
            }
            
        except Exception as e:
            print(f"Piyasa verisi getirme hatası ({coin}): {e}")
            return {}

class SentimentOutput(BaseModel):
    coin_name: str = Field(description="Coin adı")
    news_sentiment: str = Field(description="Haberlerden çıkarılan genel duygu (Positive/Neutral/Negative)")
    market_sentiment: str = Field(description="Piyasa metriklerine dayalı duygu analizi (Positive/Neutral/Negative)")
    expert_opinions: str = Field(description="Uzman görüşlerinin özeti")
    short_term_outlook: str = Field(description="24-48 saatlik kısa vadeli fiyat beklentisi")
    confidence_score: float = Field(description="Analiz güven skoru (0-1 arası)")

def analyze_market_sentiment(coins):
    """Seçilen coinler için piyasa duygu analizi yapar"""
    analyzer = NewsAnalyzer()
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    structured_llm = llm.with_structured_output(SentimentOutput)
    
    results = []
    for coin in coins:
        news_data = analyzer.get_news_data(coin)
        market_data = analyzer.get_market_data(coin)
        
        # Market verilerini formatlayalım
        market_info = f"""
        24 Saatlik Piyasa Verileri:
        - Güncel Fiyat: ${market_data.get('current_price', 'N/A')}
        - 24s Değişim: %{market_data.get('price_change_24h', 'N/A')}
        - 24s Hacim: {market_data.get('volume_24h', 'N/A')} USDT
        - 24s En Yüksek: ${market_data.get('high_24h', 'N/A')}
        - 24s En Düşük: ${market_data.get('low_24h', 'N/A')}
        - Toplam İşlem: {market_data.get('total_trades', 'N/A')}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen deneyimli bir kripto piyasası analistisin. 
            {coin} için aşağıdaki verileri analiz et:
            
            Son Haberler:
            {news_data}
            
            {market_info}
            
            Şu bilgileri içeren detaylı bir analiz yap:
            1. Haberlere dayalı genel duygu (positive/neutral/negative)
            2. Piyasa metriklerine dayalı duygu (positive/neutral/negative)
            3. Uzman görüşlerinin özeti (haberlerden çıkarım yap)
            4. 24-48 saatlik fiyat beklentisi
            5. Veri kalitesi ve miktarına dayalı güven skoru"""),
            ("user", "Verilen bilgilere dayanarak kapsamlı bir piyasa analizi yap.")
        ])
        
        chain = prompt | structured_llm
        
        analysis = chain.invoke({
            "coin": coin,
            "news_data": str(news_data),
            "market_info": market_info
        })
        
        results.append(analysis)
        
    return results

if __name__ == "__main__":
    # Test için örnek coinler
    test_coins = ["PEPE", "ETH", "BNB"]
    results = analyze_market_sentiment(test_coins)
    
    for result in results:
        print(f"\n{'='*50}")
        print(f"Coin: {result.coin_name}")
        print(f"Haber Duygu Analizi: {result.news_sentiment}")
        print(f"Piyasa Duygu Analizi: {result.market_sentiment}")
        print(f"Uzman Görüşleri: {result.expert_opinions}")
        print(f"Kısa Vadeli Beklenti: {result.short_term_outlook}")
        print(f"Güven Skoru: {result.confidence_score}")
        print(f"{'='*50}")
