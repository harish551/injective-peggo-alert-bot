import os
import requests
import schedule
import time
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
INJ_ADDRESS = os.getenv('INJ_ADDRESS')
INJECTIVE_API_BASE = os.getenv('INJECTIVE_API_BASE')
OPERATOR_ADDRESSES = os.getenv('OPERATOR_ADDRESSES').split(',')

# Initialize the Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_alert(message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    
def fetch_missing_nonces():
    response = requests.get(f"{INJECTIVE_API_BASE}/peggy/v1/missing_nonces")
    if response.status_code == 200:
        data = response.json()
        return data['operator_addresses']
    else:
        raise Exception("Failed to fetch missing nonces")
        
def fetch_global_nonce():
    response = requests.get(f"{INJECTIVE_API_BASE}/peggy/v1/module_state")
    if response.status_code == 200:
        data = response.json()
        return int(data['state']['last_observed_nonce'])
    else:
        raise Exception("Failed to fetch global nonce")

def fetch_address_nonce(address):
    url = f"{INJECTIVE_API_BASE}/peggy/v1/oracle/event/{address}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return int(data['last_claim_event']['ethereum_event_nonce'])
    else:
        raise Exception(f"Failed to fetch nonce for address: {address}")

def check_nonce():
    missing_nonces = fetch_missing_nonces()

    for address in OPERATOR_ADDRESSES:
        if address in missing_nonces:
            send_alert(f"Alert: Operator address {address} is missing nonces")
            return
    
    global_nonce = fetch_global_nonce()
    address_nonce = fetch_address_nonce(INJ_ADDRESS)        
    if address_nonce < global_nonce:
        send_alert(f"Alert: Address nonce {address_nonce} is lagging behind global nonce {global_nonce}")
    else:
        print("Address nonce is up-to-date")

# Schedule the check to run every 10 minutes
schedule.every(10).minutes.do(check_nonce)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(5)
