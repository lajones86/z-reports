import zr_io as Io
import zr_config as Config

def is_prod(api_key):
    if api_key.startswith("Tsk"):
        return(False)
    elif api_key.startswith("pk_"):
        return(True)
    elif api_key == "":
        Io.error("No iexcloud API key provided in config.")
    else:
        Io.error("Unknown api key %s" % api_key)

def get_api_key():
    #set iexcloud api variables
    api_key = Config.get_api_key("iexcloud")
    if not is_prod(api_key):
        if not (Io.yes_no("Continue with sandbox iexcloud key?")):
            Io.message("Aborting.")
    return(api_key)

def get_api_request(symbol, date, api_key = None):
    if api_key == None:
        api_key = get_api_key()
    if is_prod(api_key):
        api_host = r"https://cloud.iexapis.com"
    else:
        api_host = r"https://sandbox.iexapis.com"

    api_request = "%s/stable/stock/%s/chart/date/%s?token=%s&chartByDay=True&chartCloseOnly=True" % (api_host, symbol, date.replace("-", ""), api_key)

    return(api_request)
