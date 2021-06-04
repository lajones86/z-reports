import zt_extractor
import zt_html

import zr_financial_instruments as Instruments
import zr_io

from lxml import html as lxml_html
import re

options_formats = ["\-?[A-Z]{1,5}[0-9]{6}[C,P][0-9]{1,7}\.?[0-9]{1,2}?"]


def get_account(download_dirs = None):
    webull_file = zt_extractor.get_extractor_file("webull", download_dirs = download_dirs)

    if not webull_file:
        return(None)

    webull_account = Instruments.BrokerageAccount("Webull Taxable Account")

    print("Aggregating Webull account information")

    webull_html = lxml_html.parse(webull_file)

    #find the main table. should be the only table as of now
    table = (zt_html.get_by_xpath(webull_html,
            "//table", min_results = 1, max_results = 1, description = "Main webull Table"))[0]

    #get the headers from the table
    thead = (zt_html.get_by_xpath(table, ".//thead",
            min_results = 1, max_results = 1,
            description = "Main webull thead"))[0]

    table_map = zt_html.map_table_from_thead(thead, desired_headers_contain = ["symbol", "quantity"])

    #get the position info from the table body
    tbody = (zt_html.get_by_xpath(table, ".//tbody",
            min_results = 1, max_results = 1,
            description = "Main webull tbody"))[0]

    #get the row collection from the table body
    tr_collection = zt_html.get_by_xpath(tbody, ".//tr")

    #get the symbol
    for tr in tr_collection:
        symbol = str((tr[table_map["symbol"]].xpath("string()"))).strip()
        quantity = (tr[table_map["quantity"]].xpath("string()"))

        #filter out options
        if not "$" in symbol:
            quantity = float(quantity)
            webull_account.add_position_by_data(symbol, quantity)

    #get overnight bp for cash position
    overnight_bp_li = zt_html.get_by_xpath(webull_html,
            '//li[contains(string(), "Overnight BP")]',
            min_results = 1, max_results = 1,
            description = "Overnight BP li")[0]

    overnight_bp_spans = zt_html.get_by_xpath(overnight_bp_li,
            "./span", min_results = 2, max_results = 2,
            description = "Overnight BP spans")

    overnight_bp = str(overnight_bp_spans[1].xpath("string()")).strip()

    webull_account.cash_position = float(overnight_bp)

    return(webull_account)

if __name__ == "__main__":
    x = get_account()
    total_equity = float(0)
    for position in x.stock_positions:
        print(position.symbol, position.quantity, position.equity)
        total_equity += position.equity
    total_equity += x.cash_position
    print("Total equity: %s" % (str(total_equity)))
