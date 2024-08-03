1. Install Python
If you haven't installed Python yet, download and install it from the official Python website.
2. Create a Virtual Environment
Open your terminal or command prompt and navigate to your project directory. Then, run the following commands:
bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

3. Install Required Libraries
With the virtual environment activated, install the necessary libraries:

pip install python-binance pandas matplotlib python-telegram-bot

4. Get Your Telegram Bot Token
Go to Telegram and search for the user @BotFather.
Start a chat and use the command /newbot to create a new bot.
Follow the instructions to name your bot and get the bot token.
5. Update Your Script with the Token
In both versions of your script, replace the placeholder YOUR_TELEGRAM_BOT_TOKEN with the token you received from BotFather.
6. Run Your Script
After setting everything up, you can run your script:
