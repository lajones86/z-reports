import zt_extractor
import zt_html

import zr_financial_instruments as Instruments
import zr_io

from lxml import html as lxml_html
import re

options_formats = ["\-?[A-Z]{1,5}[0-9]{6}[C,P][0-9]{1,7}\.?[0-9]{1,2}?"]


def get_account(download_dirs = None):
    fidelity_file = zt_extractor.get_extractor_file("fidelity", download_dirs = download_dirs)

    if not fidelity_file:
        return(None)

    fidelity_account = Instruments.BrokerageAccount("Fidelity Taxable Account")

    print("Aggregating Fidelity account information")

    fidelity_html = lxml_html.parse(fidelity_file)

    #find a magicgrid table that contains symbol entries
    table = (zt_html.get_by_xpath(fidelity_html,
            "//table[starts-with(@class, 'magicgrid') and .//div[starts-with(@class, 'symbol')]]",
            min_results = 1, max_results = 1, description = "Main Fidelity Table"))[0]

    #get the headers from the table
    thead = (zt_html.get_by_xpath(table, ".//thead",
            min_results = 1, max_results = 1,
            description = "Main Fidelity thead"))[0]

    table_map = zt_html.map_table_from_thead(thead, desired_headers_contain = ["symbol", "quantity"])

    #get the position info from the table body
    tbody = (zt_html.get_by_xpath(table, ".//tbody",
            min_results = 2, max_results = 2,
            description = "Main fidelity tbody"))[0]

    #get the row collection from the table body
    tr_collection = zt_html.get_by_xpath(tbody, ".//tr[starts-with(@class, 'normal-row')]")

    #get the symbol
    for tr in tr_collection:
        symbol_span = (zt_html.get_by_xpath(tr, ".//span[@class='stock-symbol']",
                min_results = 1, max_results = 1,
                description = "Fidelity table symbol span"))[0]
        symbol = str(symbol_span.text).strip()

        quantity = float((tr[table_map["quantity"]]).text.replace(",", ""))

        if symbol.endswith("**"):
            print("Setting cash position.")
            fidelity_account.cash_position = float(quantity)
        else:
            is_option = False
            for options_format in options_formats:
                if re.match(options_format, symbol):
                    is_option = True
                    break
            if not is_option:
                print("Processing %s" % symbol)
                fidelity_account.add_position_by_data(symbol, quantity)

    #add pending activity to cash position
    print("Adjusting cash position with pending activity")
    pending_activity_div = zt_html.get_by_xpath(fidelity_html,
            "//div[@class='magicgrid--total-pending-activity-link-container']",
            min_results = 0, max_results = 1,
            description = "Pending activity div")
    if len(pending_activity_div) == 1:
        pending_activity_div = pending_activity_div[0]
        pending_activity_value = float((zt_html.get_by_xpath(pending_activity_div,
            ".//span[@class='value']", min_results = 1, max_results = 1,
            description = "Pending activity value")[0].text).strip().replace("$", "").replace(",", ""))
        fidelity_account.cash_position += pending_activity_value

    return(fidelity_account)

if __name__ == "__main__":
    x = get_account()
    total_equity = float(0)
    for position in x.stock_positions:
        print(position.symbol, position.quantity, position.equity)
        total_equity += position.equity
    total_equity += x.cash_position
    print("Total equity: %s" % (str(total_equity)))
