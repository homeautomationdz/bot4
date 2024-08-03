import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelextrema
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import io  # Import io for in-memory file handling
from binance.client import Client  # Import Binance Client
import config8  # Import the configuration file

def fetch_binance_data(symbol, timeframe='1m', limit=100):
    client = Client(config8.api_key, config8.api_secret)  # Use the API key and secret from config8.py
    try:
        klines = client.get_historical_klines(symbol, timeframe, limit=limit)
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                              'close_time', 'quote_asset_volume', 'number_of_trades',
                                              'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data['close'] = pd.to_numeric(data['close'], errors='coerce')  # Convert 'close' to numeric
        data['volume'] = pd.to_numeric(data['volume'], errors='coerce')  # Convert 'volume' to numeric
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
    crossovers = data[data['crossover'] == 1]  # Short-term VWMA crosses above long-term VWMA
    crossdowns = data[data['crossover'] == -1]  # Short-term VWMA crosses below long-term VWMA
    
    return crossovers, crossdowns

def plot_vwma(data, crossovers, crossdowns, symbol, timeframe):
    plt.figure(figsize=(12, 6))
    plt.plot(data['timestamp'], data['close'], label='Close Price')
    plt.plot(data['timestamp'], data['vwma_short'], label='Short-term VWMA', linestyle='--', color='orange')
    plt.plot(data['timestamp'], data['vwma_long'], label='Long-term VWMA', linestyle='--', color='purple')
    plt.scatter(crossovers['timestamp'], crossovers['close'], color='green', label='Crossover Points', marker='x')
    plt.scatter(crossdowns['timestamp'], crossdowns['close'], color='red', label='Crossdown Points', marker='o')
    plt.xlabel('Timestamp')
    plt.ylabel('Price')
    plt.legend()
    plt.title(f'VWMA Crossover and Crossdown Detection for {symbol} ({timeframe})')  # Updated title

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)  # Move to the beginning of the BytesIO buffer
    plt.close()  # Close the figure to free up memory
    return buf  # Return the buffer

async def send_image_to_telegram(image_buffer, token, chat_id):
    bot = Bot(token=token)
    try:
        await bot.send_photo(chat_id=chat_id, photo=image_buffer)
    except TelegramError as e:
        print(f"Error sending image to Telegram: {e}")

async def process_symbol(symbol, timeframe, short_period, long_period, token, chat_id):
    data = fetch_binance_data(symbol, timeframe)
    if data.empty:
        print(f"No data fetched for {symbol}.")
        return

    crossovers, crossdowns = detect_vwma_cross(data, short_period, long_period)
    if not crossovers.empty or not crossdowns.empty:
        plot = plot_vwma(data, crossovers, crossdowns, symbol, timeframe)
        await send_image_to_telegram(plot, token, chat_id)

async def main():
    symbols = config8.SELECTED_SYMBOLS  # Get symbols from config8.py
    timeframe = '1m'
    
    short_period = 20
    long_period = 50

    tasks = [process_symbol(symbol, timeframe, short_period, long_period, config8.bot_token, config8.chat_id) for symbol in symbols]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
