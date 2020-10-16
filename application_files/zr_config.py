import os
import configparser

import zr_io


def environment(element):
    money_dir = os.path.join(os.environ.get('USERPROFILE'), "Personal\money")
    reports_dir = os.path.join(money_dir, "reports")

    local_environment = {
            "reports_dir" : reports_dir,
            "data_dir" : os.path.join(money_dir, "script_data"),
            "reports_csv_dir" : os.path.join(reports_dir, "z_csv"),
            "investments_dir" : os.path.join(money_dir, "investments"),
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
            "history" : os.path.join(environment("data_dir"), "history"),
            "treasuries" : os.path.join(environment("investments_dir"), "treasuries.html"),
            "physical_commodities" : os.path.join(environment("investments_dir"), "physical_commodities.csv"),
            "securities_info" : os.path.join(environment("data_dir"), "securities_info.csv")
            }

    return(get_public("paths", key, defaults))


def get_sqlite(key):
    defaults = {
            "history" : os.path.join(environment("data_dir"), r"history\^00000-history.db"),
            "history_rebuild_days" : 28,
            "history_pull_years" : 10,
            }

    return(get_public("sqlite", key, defaults))


def get_beta(key):
    defaults = {
            "benchmark" : "^GSPC",
            "min_years" : 1,
            "max_years" : 3,
            "subyear_interval" : 4,
            # adj_close is adjusted for dividends
            #"close_price_col" : "close",
            "close_price_col" : "adj_close",
            "csv_out" : os.path.join(environment("reports_csv_dir"), "beta.csv"),
            "xlsx_out" : os.path.join(environment("reports_dir"), "Z-Report-Beta.xlsx"),
            }

    return(get_public("beta", key, defaults))

if __name__ == "__main__":
    zr_io.message("This module is not designed to be run on its own.")
    exit(0)
