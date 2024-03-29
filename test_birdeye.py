# test_birdeye.py

import birdeye

def test_birdeye(token_addresses):
    for token_address in token_addresses:
        token_info = birdeye.get_token_info(token_address)
        print(f"Token info: {token_info}")

        price = birdeye.get_price(token_address)
        print(f"Price for {token_address}: {price}")

        # symbol = birdeye.get_symbol(token_address)
        # print(f"Symbol for {token_address}: {symbol}")
#  change the toeke address 2xt4ZC4WUxEABSRzvY4ZhFfLj5F8sQnS5bXRC7KPtnfo, BUYHuU5x3D5Nznha8S5jyySTsBjHwWTsx8xxDmoNLA2V, 5vf7zJfYN9S5imiBUzfTASRS1M9P7kez2ynFddrxdT4R, DErcTXtQBPYEsxq7x9K1V9JjEeMa6E1LToTMYBtzbafs
token_addresses = [
    "2xt4ZC4WUxEABSRzvY4ZhFfLj5F8sQnS5bXRC7KPtnfo",
    "BUYHuU5x3D5Nznha8S5jyySTsBjHwWTsx8xxDmoNLA2V",
    "5vf7zJfYN9S5imiBUzfTASRS1M9P7kez2ynFddrxdT4R",
    "DErcTXtQBPYEsxq7x9K1V9JjEeMa6E1LToTMYBtzbafs",
    "25HwajZbusQvso1XWA1T41Cd5LVVxHsv91P3Ahq3pcTK"]
test_birdeye(token_addresses)