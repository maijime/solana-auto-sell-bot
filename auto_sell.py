# Description: This script will automatically sell tokens that have increased in price by at least x%.
import requests
from loguru import logger
import json
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solders.keypair import Keypair
import sys
from configparser import ConfigParser
import base58, logging,time, re, os,sys, json
from raydium.Raydium import *
import birdeye


def get_assets_by_owner(RPC_URL, wallet_address):
    logger.info("Checking Wallet for New Tokens")
    payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": wallet_address,
            "page": 1,  # Starts at 1
            "limit": 1000,
            "displayOptions": {
                "showFungible": True
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(RPC_URL, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        if "result" in data:
            assets = data["result"]["items"]
            spl_tokens = []
            for asset in assets:
                interface_type = asset.get("interface", "")
                if interface_type == "V1_NFT":
                    continue  # Skip NFT assets
                token_info = asset.get("token_info", {})
                balance = token_info.get("balance", None)
                if balance and float(balance) > 0:
                    spl_tokens.append({
                        "id": asset["id"],
                        "symbol": token_info.get("symbol", ""),
                        "balance": balance,
                        "token_info": token_info
                    })
            for token in spl_tokens:
                logger.info("Token ID: {}", token["id"])
                logger.info("Symbol: {}", token["symbol"])
                logger.info("Balance: {}", token["balance"])
                logger.info("Metadata: {}", token["token_info"])
        else:
            logger.error("No result found in response")
    else:
        logger.error("Error: {}, {}", response.status_code, response.text)


    logger.info(f"Current SPL Tokens {spl_tokens}")
    return spl_tokens


def write_wallet_tokens(tokens):
    # clear wallet_tokens.json if no SPL tokens are detected
    if not tokens:
        with open("data/wallet_tokens.json", "w") as file:
            file.write("[]")
        logger.info("Wallet tokens JSON file cleared")
        return

    # Load existing data from the JSON file
    try:
        with open("data/wallet_tokens.json", "r") as file:
            existing_tokens = json.load(file)
    except FileNotFoundError:
        existing_tokens = []

    # Filter out existing tokens and add new tokens using list comprehensions
    new_tokens = [
        {
            "symbol": token.get("token_info", {}).get("symbol", ""),
            "token_id": token.get("id", ""),
            "balance": token.get("token_info", {}).get("balance", ""),
            "initial_price": birdeye.get_price(token.get("id", {}))
        }
        for token in tokens
        if not any(existing_token.get("token_id") == token.get("id") for existing_token in existing_tokens)
    ]

    # Append new tokens to the existing data
    existing_tokens.extend(new_tokens)

    # Write the updated data back to the JSON file
    with open("data/wallet_tokens.json", "w") as file:
        json.dump(existing_tokens, file, indent=4)

def detect_price_change(percent_gained, percent_lost, json_file):
    price_change_tokens = []

    # Load existing data from the JSON file
    try:
        with open(json_file, "r") as file:
            existing_tokens = json.load(file)
    except FileNotFoundError:
        existing_tokens = []

    for token in existing_tokens:
        current_price = birdeye.get_price(token["token_id"])
        initial_price = float(token["initial_price"])
        # Log the initial and current prices
        logger.info(f"Initial price for {token['symbol']}: {initial_price}")
        logger.info(f"Current price for {token['symbol']}: {current_price}")
        price_change = (current_price - initial_price) / initial_price
        # Log the price change percentage
        logger.info(f"Price change for {token['symbol']}: {price_change * 100:.2f}%")
        if price_change > percent_gained / 100 or price_change < -percent_lost / 100:  # Check if the price has increased by at least percent_gained% or decreased by at least percent_lost%
            price_change_tokens.append(token)
    return price_change_tokens


def remove_token_from_json(token_id):
    json_file = "data/wallet_tokens.json"

    try:
        # Load existing data from the JSON file
        with open(json_file, "r") as file:
            existing_tokens = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, there's nothing to remove
        return

    # Filter out the token to be removed
    updated_tokens = [token for token in existing_tokens if token.get("token_id") != token_id]

    # Write the updated data back to the JSON file
    with open(json_file, "w") as file:
        json.dump(updated_tokens, file, indent=4)


def main():

    # Load Configs
    config = ConfigParser()
    config.read(os.path.join(sys.path[0], 'data', 'config.ini'))

    # Infura settings - register at infura and get your mainnet url.
    RPC_HTTPS_URL = config.get("DEFAULT", "SOLANA_RPC_URL")
    # Wallet Address
    wallet_address = config.get("DEFAULT", "WALLET_ADDRESS")
    # Wallets private key
    private_key = config.get("DEFAULT", "PRIVATE_KEY")
    # Percentage change to sell
    percent_gained = int(config.get("DEFAULT", "PERCENT_GAINED"))
    percent_lost = int(config.get("DEFAULT", "PERCENT_LOST"))

    ctx = Client(RPC_HTTPS_URL, commitment=Commitment("confirmed"), timeout=30,blockhash_cache=True)

    try:
        # Try to parse the string into a list of integers
        private_key_list = json.loads(private_key)
        # Convert the list of integers into bytes
        private_key_bytes = bytes(private_key_list)
    except json.JSONDecodeError:
        # If parsing fails, assume the key is in base58 format
        # payer = Keypair.from_bytes(base58.b58decode(private_key))
        private_key_bytes = base58.b58decode(private_key)

    # Use the bytes to create the keypair
    payer = Keypair.from_bytes(private_key_bytes)

    while True:
        spl_tokens = get_assets_by_owner(RPC_URL=RPC_HTTPS_URL, wallet_address=wallet_address)
        write_wallet_tokens(spl_tokens)

        # Detect and process tokens that have increased in price by at least x%
        price_change_tokens = detect_price_change(percent_gained, percent_lost, "data/wallet_tokens.json")
        for token in price_change_tokens:
            logger.info(f"Detected token with price increase: {token}. Selling now.")
            try:
                raydium_swap(ctx=ctx, payer=payer, desired_token_address=token['token_id'])
                remove_token_from_json(token_id=token['token_id'])
            except Exception as e:
                logger.warning(f"Issue encountered during sell {e}")
                raise

        # Pause for some time before the next iteration
        time.sleep(1)  # 1 second

if __name__ == "__main__":
    main()
