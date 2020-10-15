import zt_extractor
import zt_html

import zr_financial_instruments as Instruments
import zr_io

from lxml import html as lxml_html

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

        if symbol.endswith("**"):
            print("Skipping core position %s." % symbol)
        else:
            print("Processing %s" % symbol)
            quantity = float((tr[table_map["quantity"]]).text)
            fidelity_account.add_position_by_data(symbol, quantity)

    return(fidelity_account)

if __name__ == "__main__":
    x = get_account()
    total_equity = float(0)
    for position in x.positions:
        print(position.symbol, position.quantity, position.equity)
        total_equity += position.equity
    print(total_equity)
