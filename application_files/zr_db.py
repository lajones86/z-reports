import sqlite3
from datetime import datetime
import os
import urllib.request

import zr_financial_concepts as Concepts
import zr_config
import zr_io
import zr_csv

#strip decimals from timestamp number
def fix_timestamp(timestamp):
    timestamp_fixed = ""
    for char in str(timestamp):
        if char != "." and char != "\n":
            timestamp_fixed += char
        else:
            break
    return(int(timestamp_fixed))


#yahoo finanace close data is adjusted for splits
def download_yahoo_hist(symbol):
    #capitalize symbol
    symbol = symbol.upper()

    print("Downloading Yahoo! Finance history for %s" % symbol)

    #get current date and time as timestamp for date range
    #and build the url accordingly
    now_timestamp = datetime.timestamp(datetime.now())
    pull_years = zr_config.get_sqlite("history_pull_years")
    start_timestamp = now_timestamp - (31556926 * pull_years)

    #form csv url and download
    yf_csv = r"https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1mo&events=history" % (symbol, fix_timestamp(start_timestamp), fix_timestamp(now_timestamp))
    local_csv = os.path.join(zr_config.get_path("history"), "%s.csv" % symbol)
    try:
        urllib.request.urlretrieve(yf_csv, local_csv)
    except:
        zr_io.error("Could not download symbol %s from yahoo." % symbol)
    return(0)


#return a list of historical dates and close prices
#as HistoricalPosition objects
#return only entries from the first of their month
def get_monthly_info_from_csv(symbol):
    return_list = []

    csv_columns = [
            zr_csv.CsvColumn(name = "Date"),
            zr_csv.CsvColumn(name = "Close", data_type = "float"),
            zr_csv.CsvColumn(name = "Adj Close", data_type = "float")
            ]

    csv_path = os.path.join(zr_config.get_path("history"), "%s.csv" % symbol)
    csv_file = zr_csv.CsvFile(csv_path, default_column_list = csv_columns)
    for row in csv_file.return_all():
        new_record = Concepts.HistoricalPosition(row["Date"], row["Close"], row["Adj Close"])
        if new_record.date.day == 1:
            #don't add it if today is the day because it may not have closed yet
            if new_record.date.day == datetime.now().day and new_record.date.month == datetime.now().month and new_record.date.year == datetime.now().year:
                pass
            #not sure when yahoo started throwing these weird null rows into the mix
            elif "null" in str(new_record.close) or "null" in str(new_record.adj_close):
                zr_io.fatal("Null value in row %s" % str(new_record.date))
            else:
                return_list.append(new_record)
    return(return_list)


def today_string():
    return("%s-%s-%s" % (str(datetime.today().year), str(datetime.today().strftime("%m")), str(datetime.today().strftime("%d"))))


def rebuilt_today(cursor):
    cursor.execute("INSERT OR REPLACE INTO zmaint(zaction, zvalue) VALUES ('rebuild', '%s');" % today_string())


#instead of rebuilding, we'll just drop these and they'll get added as they're checked
def db_purge(cursor, rebuild_time, tables_to_rebuild):
    purged = False
    if zr_io.yes_no("It has been %s since your last database rebuild. Historical price adjustments may not be accurate. Purge now?" % rebuild_time):
        print("Rebuilding")
        for table in tables_to_rebuild:
            cursor.execute("DROP TABLE '%s';" % table)
        rebuilt_today(cursor)
        purged = True
    return(purged)


def db_clean(cursor):
    print("Checking database integrity.")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    is_maint_table = False
    #clean empty tables and note existence of zmaint table
    tables_to_rebuild = []
    for table in tables:
        if table[0] == "zmaint":
            is_maint_table = True
        else:
            count = cursor.execute("SELECT COUNT(*) FROM '%s'" % str(table[0])).fetchall()[0][0]
            if int(count) == 0:
                print("Dropping empty table %s" % table[0])
                cursor.execute("DROP TABLE '%s'" % table[0])
            else:
                tables_to_rebuild.append(table[0])


    if not is_maint_table:
        cursor.execute("CREATE TABLE 'zmaint' (zaction TEXT PRIMARY KEY, zvalue TEXT)")

    if len(tables) == 0:
        rebuilt_today(cursor)
        return(tables)
    elif len(tables) == 1:
        if is_maint_table:
            rebuilt_today(cursor)
            return(tables)

    last_rebuild = cursor.execute("SELECT zvalue FROM zmaint WHERE zaction='rebuild';").fetchall()
    rebuild_time = None
    if len(last_rebuild) == 0:
        rebuild_time = "infinity"
    else:
        last_rebuild = datetime.strptime(last_rebuild[0][0], "%Y-%m-%d")
        today = datetime.strptime(today_string(), "%Y-%m-%d")
        rebuild_span = int((today - last_rebuild).days)
        rebuild_limit = int(zr_config.get_sqlite("history_rebuild_days"))
        if rebuild_span >= rebuild_limit:
            rebuild_time = "%s Days" % rebuild_span
    if rebuild_time:
        if db_purge(cursor, rebuild_time, tables_to_rebuild):
            tables = []
    return(tables)



def sync_sqlite(positions):
    history_path = zr_config.get_sqlite("history")
    if not os.path.isdir(os.path.split(history_path)[0]):
        os.makedirs(os.path.split(history_path)[0])
    db_conn = sqlite3.connect(history_path)
    db_conn.isolation_level = None
    cursor = db_conn.cursor()
    tables = db_clean(cursor)
    sync_sqlite_postclean(positions, cursor, tables)
    db_conn.close()
    return(0)


def sync_sqlite_postclean(positions, cursor, tables):
    #this is where we figure out what we have and what we need for a given symbol
    for position in positions:
        position_in_db = False
        for table in tables:
            if table[0] == position.symbol:
                position_in_db = True
                break

        #for new positions
        if not position_in_db:
            print("Tracking new position in database: %s " % str(position.symbol))
            cursor.execute("CREATE TABLE '%s'(date text UNIQUE, close real, adj_close real)" % str(position.symbol))

        #figure out where to start data pull for existing positions
        else:
            print("Checking table %s for updates" % str(position.symbol))
            last_symbol_date = cursor.execute("SELECT MAX(date) FROM '%s'" % str(position.symbol)).fetchall()[0][0]
            start_time = str(datetime.timestamp(datetime.strptime(last_symbol_date.strip(), "%Y-%m-%d %H:%M:%S")))
        
        if download_yahoo_hist(position.symbol) != 0:
            return(1)


        #this is where we parse whatever csv we've ended up with into the database
        monthly_info = get_monthly_info_from_csv(position.symbol)
        if len(monthly_info) != 0:
            for record in monthly_info:
                record_count = (cursor.execute("SELECT COUNT(*) FROM '%s' WHERE date='%s';" % (str(position.symbol), str(record.date))).fetchall()[0][0])
                if record_count == 0:
                    print("Adding %s record: %s on %s" % (str(position.symbol), str(record.close), str(record.date)))
                    cursor.execute("INSERT INTO '%s' VALUES ('%s','%s', '%s')" % (str(position.symbol), str(record.date), str(record.close), str(record.adj_close)))
                else:
                    if record_count != 1:
                        zr_io.error("Multiple entries detected for %s on %s. Data integrity compromised." % (str(position.symbol), str(record.date)))

    return(0)

def test():
    sync_sqlite([])

if __name__ == "__main__":
    test()
