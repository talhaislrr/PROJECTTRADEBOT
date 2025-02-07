from graph.tools.crypto_analyzer import CryptoAnalyzer

if __name__ == "__main__":
    # Tool'u import et


# Tool'u başlat
    analyzer = CryptoAnalyzer()

# Herhangi bir coin için veri al
    btc_data = analyzer.get_data('BTC', interval='1h', limit=100)
    eth_data = analyzer.get_data('ETH', interval='15m', limit=200)
    print(btc_data)
    print(eth_data)
    