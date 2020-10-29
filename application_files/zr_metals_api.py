import zr_config as Config

def get_historical_request(metals, date):
    api_key = Config.get_api_key("metals-api")

    symbols = ""
    for metal in metals:
        symbols += (metal.symbol).replace("-USD", "") + ","
    symbols = symbols.rstrip(",")

    api_request = (r"https://metals-api.com/api/%s?access_key=%s&base=USD&symbols=%s" % (str(date), str(api_key), str(symbols)))

    return(api_request)


def get_live_request(symbol_string):
    api_key = Config.get_api_key("metals-api")
    api_request = (r"https://metals-api.com/api/latest?access_key=%s&base=USD&symbols=%s" % (api_key, symbol_string))
    return(api_request)
