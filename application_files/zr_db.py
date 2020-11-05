import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os
import requests

import zr_financial_concepts as Concepts
import zr_financial_instruments as Instruments
import zr_config as Config
import zr_io as Io
import zr_calendar as Calendar
import zr_yahoo as Yahoo
import zr_iexcloud as Iexcloud
import zr_api as Api
import zr_metals_api as MetalsApi
import zr_exchangerates as ExchangeRates

def purge(cursor):
    tables_to_keep = ["zmaintenance", "start_dates"]
    #see if old data needs purged
    today = datetime.now()
    today = today.strftime("%Y-%m-%d")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    maintenance_table_exists = False
    for table in tables:
        if table[0] == "zmaintenance":
            maintenance_table_exists = True
    purged = False
    if not maintenance_table_exists:
        purged = True
        cursor.execute("CREATE TABLE 'zmaintenance' (zid TEXT PRIMARY KEY, zvalue TEXT);")
    else:
        last_purge = cursor.execute("SELECT zvalue FROM 'zmaintenance' WHERE zid='last_purge';").fetchall()
        time_since = None
        if len(last_purge) == 0:
            time_since = "Infinity"
        else:
            last_purge = datetime.strptime(last_purge[0][0], "%Y-%m-%d")
            time_since = int((datetime.now() - last_purge).days)
            if time_since < int(Config.get_sqlite("history_rebuild_days")):
                time_since = None
        if time_since:
            if Io.yes_no("It has been %s days since your last purge. Purge now?" % str(time_since)):
                purged = True
                for table in tables:
                    table = table[0]
                    if table not in tables_to_keep:
                        cursor.execute("DROP TABLE '%s';" % table)

    if purged == True:
        print("Inserting purge date: %s" % today)
        cursor.execute("INSERT OR REPLACE INTO zmaintenance(zid, zvalue) VALUES ('last_purge', '%s');" % today)
    return(None)


def get_history_db_cursor(skip_purge_check = None):
    #connect to history db
    db_path = Config.get_path("history_db")
    db_conn = sqlite3.connect(db_path)
    db_conn.isolation_level = None
    cursor = db_conn.cursor()
    
    if skip_purge_check != True:
        purge(cursor)

    return(cursor)


def get_start_date(symbol):
    history_db = get_history_db_cursor(skip_purge_check = True)
    history_db.execute("CREATE TABLE IF NOT EXISTS 'start_dates' (symbol TEXT PRIMARY KEY, date TEXT);")
    date = history_db.execute("SELECT date FROM 'start_dates' WHERE symbol = '%s'" % symbol).fetchall()
    if len(date) == 0:
        return(None)
    elif len(date) == 1:
        return(date[0][0])


def set_start_date(symbol, date):
    history_db = get_history_db_cursor(skip_purge_check = True)
    history_db.execute("CREATE TABLE IF NOT EXISTS 'start_dates' (symbol TEXT PRIMARY KEY, date TEXT);")
    cursor.execute("INSERT OR REPLACE INTO start_dates(symbol, date) VALUES ('symbol', '%s');" % date)
    return(0)


def get_dates_list():
    dates = []
    now = datetime.now()
    #don't use this month's data if it's the first
    if now.day == 1:
        dates_end = now - relativedelta(months = 1)
    else:
        dates_end = now

    dates_end = dates_end.replace(day = 1)
    total_dates_count = (Config.get_beta("max_years") * 12) + 1
    #build the dates list
    date_to_add = dates_end
    while len(dates) < total_dates_count:
        formatted_date = date_to_add.strftime("%Y-%m-%d")
        dates.append(formatted_date)
        date_to_add = date_to_add - relativedelta(months = 1)

    adjusted_dates = []
    for date in dates:
        if Config.get_yahoo("use_yahoo") == "False":
            date = Calendar.get_trading_date(date)
        adjusted_dates.append(date)
    return(adjusted_dates[::-1])

def get_missing_dates(history_db, symbol, dates):
    missing_dates = dates[:]
    tables = history_db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    table_exists = False
    for table in tables:
        if table[0] == symbol:
            table_exists = True
            break

    if not table_exists:
        history_db.execute("CREATE TABLE '%s' (date TEXT PRIMARY KEY, adj_close REAL);" % symbol)
    else:
        for existing_history in history_db.execute("SELECT date FROM '%s';" % symbol):
            if existing_history[0] in missing_dates:
                missing_dates.remove(existing_history[0])

    return(missing_dates)


def sync_stock_history(positions):
    iexcloud_api_key = Iexcloud.get_api_key()

    dates = get_dates_list()
    history_db = get_history_db_cursor()

    for position in positions:
        print("Processing database entries for %s" % position.symbol)
        missing_dates = get_missing_dates(history_db, position.symbol, dates)
        for date in missing_dates:
            if Config.get_yahoo("use_yahoo") == "False":
                symbol = position.symbol
                api_request = Iexcloud.get_api_request(symbol, date, api_key = iexcloud_api_key)
                response = Api.make_api_request(api_request)
            elif Config.get_yahoo("use_yahoo") == "True":
                response = Yahoo.request(position.symbol, date)
            if len(response) > 1:
                Io.error("Expected 1 result from request %s, got %s" % (api_request, str(len(response))))
            elif len(response) == 0:
                #we set the close to -9001 so we don't keep making api calls for dates before the symbol existed
                print("No data for %s on %s" % (position.symbol, date))
                adj_close = -9001
            else:
                adj_close = (response[0])["close"]
            print("Adding record for %s on %s: %s" % (position.symbol, date, adj_close))
            history_db.execute("INSERT INTO '%s' VALUES ('%s','%s')" % (position.symbol, date, adj_close))


def sync_metals_history(metals):
    dates = get_dates_list()
    history_db = get_history_db_cursor()

    #aggregate missing dates across metals to minimize api calls
    for metal in metals:
        missing_dates = get_missing_dates(history_db, metal.symbol, dates)
        if len(missing_dates) > 0:
            ExchangeRates.download(metal.symbol)
        for date in missing_dates:
            close = ExchangeRates.get_close(metal.symbol, date)
            print("Adding record for %s on %s: %s" % (metal.symbol, date, close))
            history_db.execute("INSERT INTO '%s' VALUES ('%s','%s')" % (metal.symbol, date, close))
    ExchangeRates.clean()
    return(0)


def sync_history(positions, positions_type):
    #sync benchmark
    if Config.get_yahoo("use_yahoo") == "False":
        benchmark_symbol = Config.get_beta("benchmark")
    elif Config.get_yahoo("use_yahoo") == "True":
        benchmark_symbol = Config.get_yahoo("benchmark")
    sync_stock_history([Instruments.StockPosition(benchmark_symbol, 0)])

    if positions_type == "stock_shares":
        sync_stock_history(positions)

    elif positions_type == "crypto":
        if Config.get_yahoo("use_yahoo") == "True":
            sync_stock_history(positions)

    elif positions_type == "metals":
        sync_metals_history(positions)

    if Config.get_yahoo("use_yahoo") == "True":
        Yahoo.clean()
    return(0)

if __name__ == "__main__":
    sync_history([Instruments.StockPosition("SPYD", 1), Instruments.StockPosition("SPYG", 1)], "stock_shares")
