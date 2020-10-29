import zr_config as Config
import zr_io as Io
import zr_financial_instruments as Instruments

import os
import re
import ast
import requests
from time import sleep

def get_balance(coin_type, address):
    print("Checking %s address %s" % (coin_type, address))
    api_request = r"https://api.blockcypher.com/v1/%s/main/addrs/%s/balance" % (coin_type, address)
    response = requests.get(api_request)
    status = str(response.status_code)
    if status.startswith("2"):
        output = response.json()
        base = output["balance"]
        if coin_type in ["ltc", "btc"]:
            return(base / 100000000)
        elif coin_type == "eth":
            return(base / 1000000000000000000)
        else:
            return(base)
    else:
        Io.error("Api request %s returned %s error" % (api_request, status))

def get_used_electrum_addresses(wallet_dir, leading_id):
    address_list = []
    for wallet in os.listdir(wallet_dir):
        if not wallet.endswith(".swp") and not wallet.endswith(".un~"):
            with open(os.path.join(wallet_dir, wallet), "r", encoding = "ISO-8859-1") as f:
                addresses = False
                for line in f:
                    if addresses == False:
                        if line.strip() == "\"addr_history\": {":
                            addresses = True
                    else:
                        if line.strip() == "},":
                            break
                        else:
                            line = line.strip().strip("\",")
                            if line.startswith(leading_id) and not line.endswith("[]"):
                                address_list.append(line.rstrip("\": ["))
    return(address_list)

def get_mycrypto_addresses(mycrypto_dir):
    addresses = []
    addresses_re = re.compile("\{\"recentAddresses.*?}")
    for i in os.listdir(mycrypto_dir):
        if i.endswith(".log"):
            with open(os.path.join(mycrypto_dir, i), "r", encoding = "ISO-8859-2") as f:
                for line in f:
                    for address_field in addresses_re.findall(line):
                        address_field = address_field.replace("{\"recentAddresses\":", "").replace("}", "").strip()
                        new_addresses = ast.literal_eval(address_field)
                        for new_address in new_addresses:
                            new_address = new_address.strip()
                            if not new_address in addresses:
                                addresses.append(new_address)
    return(addresses)


def main():
    ltc = Instruments.CryptoCurrency("ltc", get_used_electrum_addresses(Config.get_path("electrum_ltc_wallets"), "ltc"))
    btc = Instruments.CryptoCurrency("btc", get_used_electrum_addresses(Config.get_path("electrum_btc_wallets"), "bc"))
    eth = Instruments.CryptoCurrency("eth", get_mycrypto_addresses(Config.get_path("mycrypto_eth_wallets")))

    crypto_list = [ltc, btc, eth]

    for crypto in crypto_list:
        for address in crypto.addresses:
            crypto.add_balance(get_balance(crypto.currency, address))
            sleep(.5)

    return(crypto_list)

if __name__ == "__main__":
    main()
