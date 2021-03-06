from pymongo import MongoClient
import requests
import time
import os

mongoClient = os.environ["DB_SOURCE"]
print(f'Mongo Client: {mongoClient}')
client = MongoClient(mongoClient)

recent_stocks_db = client.recentStocks
all_stocks_coll = recent_stocks_db.stocks
stocks = list(all_stocks_coll.find())

historic_stocks_db = client.historicStocks
all_stocks = historic_stocks_db.stocks

# Consulta o serviço e traz as informações, em caso de erro, tenta novamente
def get_information(stockCode):
    try:
        response = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={stockCode}.sa&apikey=YOUR_API_KEY')
        if response.status_code == 200:
            if 'Monthly Time Series' in response.text:
                return response.json()
            elif "Invalid API call" in response.text:
                return 'invalid'
        print("Aguardando 60 seg...")
        time.sleep(60)
        return get_information(stockCode)
    except expression as identifier:
        print("Aguardando 60 seg...")
        time.sleep(60)
        return get_information(stockCode)

# Formata retorno do serviço
def get_historical_information(historical):
    historical_doc = []
    for key, historic in historical.items():
        historic_doc = {
            "date": key,
            "open": float(historic["1. open"]),
            "high": float(historic["2. high"]),
            "low": float(historic["3. low"]),
            "close": float(historic["4. close"]),
            "volume": float(historic["5. volume"])
        }
        historical_doc.append(historic_doc)
    return historical_doc;

stock_error_list = []

# Função responsável por salvar os dados
def function_main(stockCode):
    data = get_information(stockCode)
    if data != "invalid":
        historical = data['Monthly Time Series']
        historical_doc = get_historical_information(historical)
        newStock = {"_id": stockCode, "historical": historical_doc}
        all_stocks.replace_one({'_id': newStock['_id']}, newStock, True)
        print(f'Recuperou o historico de {stockCode}')
    else:
        stock_error_list.append(stockCode)
        print(f'Recuperou o historico de {stockCode} - error')

#################### INICIO ####################
totalAtivos = len(stocks)

print(f'Recuperou todos ativos os {len(stocks)} ativos')

for stock in stocks:
    stockCode = stock['stockCode']
    function_main(stockCode)

totalAtivosComErro = len(stock_error_list)

print(f'Lista dos {totalAtivosComErro} ativos com erro:')
for stockerror in stock_error_list:
    print(f'{stockerror} - error')

client.close()
print()
print(f'Total de ativos com sucesso: {totalAtivos - totalAtivosComErro}')
