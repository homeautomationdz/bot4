from binance.client import Client
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# API credentials
api_key = 'b4Cw5Z2a2uToBHunOedHBKabGhdn1pm2MA5PJALWF9nU7XJ6f2GrAKkijY4OdXYe'
api_secret = '1XyFpTQFkac5PJZYXysVSCcGKMkLPcqLzk8BOKWAmTc9kiQyMIK5hdrzbaw4cHXn'

# Telegram bot token and chat ID
bot_token = '7059673705:AAEPdxG0FuVarZLc2fqURr9W3Qb2NPDIc2c'
chat_id = '1434650273'

def fetch_binance_data(symbol, timeframe='1m', limit=100):
    client = Client(api_key, api_secret)
    try:
        klines = client.get_historical_klines(symbol, timeframe, limit=limit)
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data['close'] = data['close'].astype(float)
        data['volume'] = data['volume'].astype(float)
        return data[['timestamp', 'close', 'volume']]
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_vwma(data, period):
    vwma = (data['close'] * data['volume']).rolling(window=period).sum() / data['volume'].rolling(window=period).sum()
    return vwma

def detect_vwma_cross(data, short_period, long_period):
    data['vwma_short'] = calculate_vwma(data, short_period)
    data['vwma_long'] = calculate_vwma(data, long_period)
    
    data['crossover'] = (data['vwma_short'] > data['vwma_long']).astype(int).diff()
    crossovers = data[data['crossover'] == 1]
    crossdowns = data[data['crossover'] == -1]
    
    return crossovers, crossdowns

def plot_vwma(data, crossovers, crossdowns, symbol, filename):
    plt.figure(figsize=(12, 6))
    plt.plot(data['timestamp'], data['close'], label='Close Price')
    plt.plot(data['timestamp'], data['vwma_short'], label='Short-term VWMA', linestyle='--', color='orange')
    plt.plot(data['timestamp'], data['vwma_long'], label='Long-term VWMA', linestyle='--', color='purple')
    plt.scatter(crossovers['timestamp'], crossovers['close'], color='green', label='Crossover Points', marker='x')
    plt.scatter(crossdowns['timestamp'], crossdowns['close'], color='red', label='Crossdown Points', marker='o')
    plt.xlabel('Timestamp')
    plt.ylabel('Price')
    plt.legend()
    plt.title(f'VWMA Crossover and Crossdown Detection for {symbol}')
    plt.savefig(filename)
    plt.close()

async def send_image_to_telegram(filename, token, chat_id):
    bot = Bot(token=token)
    try:
        with open(filename, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo)
    except TelegramError as e:
        print(f"Error sending image to Telegram: {e}")

async def process_symbol(symbol, timeframe, short_period, long_period, token, chat_id):
    data = fetch_binance_data(symbol, timeframe)
    if data.empty:
        print(f"No data fetched for {symbol}.")
        return

    crossovers, crossdowns = detect_vwma_cross(data, short_period, long_period)
    if not crossovers.empty or not crossdowns.empty:
        filename = f'{symbol.replace("/", "_")}_vwma_crossover_crossdown_binance.png'
        plot_vwma(data, crossovers, crossdowns, symbol, filename)
        await send_image_to_telegram(filename, token, chat_id)

async def main():
    symbols = ['BTCUSDT', 'ETHUSDT']
    timeframe = '1m'
    
    short_period = 20
    long_period = 50

    tasks = [process_symbol(symbol, timeframe, short_period, long_period, bot_token, chat_id) for symbol in symbols]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())