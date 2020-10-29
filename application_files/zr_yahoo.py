import urllib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os

import zr_config as Config
import zr_io as Io
import zr_csv as Csv
import zr_db as Db
import zr_iexcloud as Iexcloud
import zr_api as Api
import zr_calendar as Calendar

def get_filepath(symbol, prepend = None):
    destination_dir = Config.get_yahoo("download_dir")
    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    if prepend == None:
        prepend = str(datetime.now().strftime("%Y-%m-%d"))
    else:
        prepend = prepend
    destination_file = prepend + "-" + symbol + ".csv"
    destination_path = os.path.join(destination_dir, destination_file)
    return(destination_path)


def get_url_timestamp(date):
    timestamp = datetime.timestamp(datetime.strptime(date, "%Y-%m-%d"))
    fixed_timestamp = ""
    for char in str(timestamp):
        if char != "." and char != "\n":
            fixed_timestamp += char
        else:
            return(fixed_timestamp)


def get_csv_url(symbol, start_date, end_date):
    start_date = get_url_timestamp(start_date)
    end_date = get_url_timestamp(end_date)

    yf_csv = r"https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1mo&events=history" % (symbol, start_date, end_date)
    return(yf_csv)


def download(symbol, start_date, end_date, destination_path = None, is_fix_attempt = None):
    symbol = symbol.upper()

    db_start_date = Db.get_start_date(symbol)
    if db_start_date != None:
        start_date = db_start_date

    if destination_path == None:
        destination_path = get_filepath(symbol)
    else:
        destination_path = destination_path

    csv_url = get_csv_url(symbol, start_date, end_date)
   
    try:
        urllib.request.urlretrieve(csv_url, destination_path)
    except urllib.error.HTTPError:
        if is_fix_attempt != True:
            Io.error("Failed to download history for %s from %s to %s" % (symbol, start_date, end_date))
        else:
            return(False)

    return(True)

def get_adj_close(path, date):
    columns = [
            Csv.CsvColumn(name = "Date"),
            Csv.CsvColumn(name = "Adj Close")
            ]
    csv_file = Csv.CsvFile(path, columns, [])
    entry = csv_file.find_by_dict({"Date" : date})
    if len(entry) == 1:
        return(entry[0]["Adj Close"])
    elif len(entry) == 0:
        return(None)
    else:
        Io.error("Expected 0 or 1 results, got %s for query %s in %s." % (str(len(entry)), str(date), str(path)))

def request(symbol, date):
    csv_path = get_filepath(symbol)
    if os.path.isfile(csv_path):
        adj_close = get_adj_close(csv_path, date)
    else:
        adj_close = "null"

    if adj_close != None:
        if "null" in adj_close:
            csv_path = get_filepath(symbol, prepend = "retry-")
            if download(symbol, date, date, csv_path, is_fix_attempt = True) == False:
                print("Failed to get data from yahoo. Falling back to iexcloud.")
                iexcloud_request = Iexcloud.get_api_request(symbol, date)
                iexcloud_response = Api.make_api_request(iexcloud_request)
                if len(iexcloud_response) == 0:
                    return_empty = True
                elif len(iexcloud_response) == 1:
                    adj_close = str(iexcloud_response[0]["close"])
                    try:
                        if float(adj_close) == 0:
                            return_empty = True
                    except (TypeError, ValueError):
                        if str(adj_close) == "":
                            return_empty = True
            else:
                adj_close = get_adj_close(csv_path, date)
    
    return_empty = False
    if adj_close == None:
        return_empty = True
    elif "null" in adj_close:
        return_empty = True
    else:
        try:
            adj_close = float(adj_close)
        except (TypeError, ValueError):
            Io.error("Unanticipated value %s in adj_close for %s" % (str(adj_close), symbol))
    
    if return_empty == True:
        return([])
    elif return_empty == False:
        return([{"close" : adj_close}])

def clean():
    print("Cleaning download dir")
    download_dir = Config.get_yahoo("download_dir")
    for i in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, i))
