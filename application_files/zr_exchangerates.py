import zr_config as Config
import zt_html as Html
import zr_io as Io

import os
from datetime import datetime
import urllib
from lxml import html as lxml_html

def get_filepath(symbol):
    destination_dir = Config.get_path("ex_rates_dir")
    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    prepend = str(datetime.now().strftime("%Y-%m-%d"))
    filename = prepend + "-" + symbol + ".htm"
    return(os.path.join(destination_dir, filename))


def download(symbol):
    remote_url = r"https://www.exchangerates.org.uk/commodities/%s-history.html" % symbol.upper()
    local_file = get_filepath(symbol)
    if not os.path.isfile(local_file):
        try:
            urllib.request.urlretrieve(remote_url, local_file)
            return(True)
        except urllib.error.HTTPError:
            Io.error("Failed to download history for %s" % (symbol))


def get_close(symbol, date):
    months = [
            "January", "February", "March", "April", "May",
            "June", "July", "August", "September", "October",
            "November", "December"
            ]
    year = date[:4]
    month = months[int(date[5:7]) - 1]
    day = str(int(date[8:10]))

    row_date = " %s %s %s" % (day, month, year)

    file_path = get_filepath(symbol)
    if not os.path.isfile(file_path):
        download(symbol)

    er_html = lxml_html.parse(file_path)

    table = (Html.get_by_xpath(er_html,
            ".//table[@id='hist']",
            min_results = 1, max_results = 1, description = "History Table"))[0]

    wanted_row = Html.get_by_xpath(table,
            ".//td[contains(text(), '%s')]/.." % row_date,
            min_results = 1, max_results = 1, description = "Row for %s" % date)[0]

    value_cell = Html.get_by_xpath(wanted_row, ".//td",
            min_results = 4, max_results = 4, description = "Cells for row %s" % date)[2]
    
    try:
        return(float(value_cell.text))
    except:
        Io.error("Failed to convert closing value %s for %s on %s to float." % (str(close), symbol, date))



def clean():
    print("Cleaning download dir")
    download_dir = Config.get_path("ex_rates_dir")
    for i in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, i))

if __name__ == "__main__":
    print(get_close("XAG-USD", "2020-10-23"))
