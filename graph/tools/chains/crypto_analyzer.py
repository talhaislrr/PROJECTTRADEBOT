import pandas as pd
import numpy as np
import requests
import ta
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CryptoAnalyzer:
    def __init__(self):
        self.base_url = 'https://api.binance.com/api/v3'
        
    def get_data(self, symbol, interval='1h', limit=100):
        """
        Fetches cryptocurrency data from Binance
        
        Parameters:
        - symbol: str, e.g., 'BTC', 'ETH', 'BNB'
        - interval: str, e.g., '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
        - limit: int, max 1000 candles
        
        Returns:
        - DataFrame: timestamp, open, high, low, close, volume and technical indicators
        """
        try:
            url = f'{self.base_url}/klines'
            params = {
                'symbol': f'{symbol}USDT',
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 
                                           'volume', 'close_time', 'quote_volume', 'trades_count',
                                           'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df = self.calculate_indicators(df)
            
            cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                   'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
                   'BB_upper', 'BB_middle', 'BB_lower', 'Stoch_RSI', 'VWAP']
            
            return df[cols]
            
        except Exception as e:
            print(f"Error fetching data ({symbol}): {e}")
            return None

    def calculate_indicators(self, df):
        """Calculates technical indicators"""
        try:
            # RSI
            df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Hist'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'])
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_middle'] = bollinger.bollinger_mavg()
            df['BB_lower'] = bollinger.bollinger_lband()
            
            # Stochastic RSI
            stoch = ta.momentum.StochRSIIndicator(df['close'])
            df['Stoch_RSI'] = stoch.stochrsi()
            
            # VWAP
            df['VWAP'] = ta.volume.VolumeWeightedAveragePrice(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume']
            ).volume_weighted_average_price()
            
            return df
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return None


if __name__ == "__main__":
    analyzer = CryptoAnalyzer()
    data = analyzer.get_data("BERA", "15m", 100)
    print(data)
