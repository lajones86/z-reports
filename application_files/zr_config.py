import os
import configparser

import zr_io


def environment(element):
    money_dir = os.path.join(os.environ.get('USERPROFILE'), "Personal\money")
    reports_dir = os.path.join(money_dir, "reports")

    local_environment = {
            "reports_dir" : reports_dir,
            "data_dir" : os.path.join(money_dir, "script_data"),
            "assets_dir" : os.path.join(money_dir, "assets"),
            "cash_flows_dir" : os.path.join(money_dir, "cash_flows"),
            "money_dir" : money_dir
            }
    
    return(local_environment[element])

def get_universal(config_file, query_section, query_key, defaults):
    #make sure the directory structure is there
    if not os.path.isdir(os.path.split(config_file)[0]):
        os.makedirs(os.path.split(config_file)[0])
    #make sure the config file is there
    if not os.path.isfile(config_file):
        with open(config_file, "w") as f:
            f.write("")

    #add the 'default' section if it's not there
    config = configparser.ConfigParser()
    config.read(config_file)
    if not query_section in config.sections():
        config.add_section(query_section)

    #update ini with defaults for missing keys
    #if necessary
    update_config = False
    for default_key in defaults:
        if default_key in config[query_section]:
            defaults[default_key] = config[query_section][default_key]
        else:
            update_config = True
    if update_config:
        config[query_section] = defaults
        with open(config_file, "w") as f:
            config.write(f)
            config.read(config_file)

    return_value = str(config[query_section][query_key]).strip()

    return(return_value)


def get_public(section, key, defaults):
    public_ini = os.path.join(environment("data_dir"), "z_pub.ini")
    value = get_universal(public_ini, section, key, defaults)
    #make sure to return an int if it's supposed to be an int
    if value.isnumeric():
        value = int(value)
    return(value)

def get_path(key):
    defaults = {
            "treasuries" : os.path.join(environment("assets_dir"), "treasuries.html"),
            "securities_info" : os.path.join(environment("data_dir"), "securities_info.csv"),
            "reports_dir" : environment("reports_dir"),
            "history_db" : os.path.join(environment("data_dir"), r"history.db"),
            "electrum_ltc_wallets" : os.path.join(os.environ.get("USERPROFILE"), r"Desktop\Crypto\electrum-ltc_data\wallets"),
            "electrum_btc_wallets" : os.path.join(os.environ.get("APPDATA"), r"Electrum\wallets"),
            "mycrypto_eth_wallets" : os.path.join(os.environ.get("APPDATA"), r"MyCrypto\Local Storage\leveldb"),
            "metals_csv" : os.path.join(environment("assets_dir"), "metals.csv"),
            "ex_rates_dir" : os.path.join(environment("data_dir"), r"ex_rates"),
            "accounts_csv" : os.path.join(environment("cash_flows_dir"), r"accounts.csv"),
            "money_dir" : environment("money_dir"),
            "ledger_archive_dir" : os.path.join(environment("cash_flows_dir"), r"archive"),
            }

    return(get_public("paths", key, defaults))


def get_sqlite(key):
    defaults = {
            "history_rebuild_days" : 35,
            }

    return(get_public("sqlite", key, defaults))


def get_ledger(key):
    defaults = {
            "archive_months" : 12,
            }

    return(get_public("ledger", key, defaults))


def get_beta(key):
    defaults = {
            "benchmark" : "SPY",
            "min_years" : 1,
            "max_years" : 3,
            "subyear_interval" : 4,
            "manual_averages" : os.path.join(environment("data_dir"), r"manual_average_beta.csv"),
            }

    return(get_public("beta", key, defaults))


def get_api_key(key):
    defaults = {
            "metals-api" : "",
            "iexcloud" : ""
            }
    return(get_public("api_keys", key, defaults))


def get_yahoo(key):
    defaults = {
            "use_yahoo" : "False",
            "download_dir" : os.path.join(environment("data_dir"), "yahoo"),
            "benchmark" : "^GSPC",
            }
    return(get_public("yahoo", key, defaults))

if __name__ == "__main__":
    zr_io.message("This module is not designed to be run on its own.")
    exit(0)
