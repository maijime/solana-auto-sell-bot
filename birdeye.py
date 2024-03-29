# birdeye.py

import requests

def get_token_info(token_address):
    url = f"https://public-api.birdeye.so/public/price?address={token_address}"
    headers = {"X-API-KEY": "957cd536c6344fd3a1d3bc2e37674d12"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_price(token_address):
    token_info = get_token_info(token_address)
    if token_info is None:
        return 1
    if not token_info or "data" not in token_info or token_info["data"] is None or "value" not in token_info["data"]:
        return 1
    return token_info["data"]["value"]

# Currently not in birdeye api
# def get_symbol(token_address):
#     token_info = get_token_info(token_address)
#     return token_info["data"].get("symbol", "Unknown symbol")
