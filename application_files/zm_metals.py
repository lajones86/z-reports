import zr_config as Config
import zr_csv as Csv
import zr_io as Io
import zr_financial_instruments as Instruments
import zr_metals_api as MetalsApi
import zr_api as Api
import zr_yahoo as Yahoo

def main():
    columns = [
            Csv.CsvColumn("Symbol", is_row_identifier = True),
            Csv.CsvColumn("Description"),
            Csv.CsvColumn("Quantity", data_type = "float"),
            Csv.CsvColumn("Multiplier", data_type = "float")
            ]

    default_data = [
            ["XAG-USD", "Silver, Troy Ounce", 0, .9],
            ["XAU-USD", "Gold, Troy Ounce", 0, .9]
            ]

    metals_csv = Csv.CsvFile(Config.get_path("metals_csv"), default_column_list = columns, default_data_rows = default_data, stop_on_write = False, read_only = False)

    metals = []
    symbol_string = ""
    for metal in metals_csv.return_all():
        if metal["Quantity"] > 0:
            metals.append(metal)
            symbol_string += (metal["Symbol"]).replace("-USD", "") + ","
    symbol_string = symbol_string.rstrip(",")

    live_prices_request = MetalsApi.get_live_request(symbol_string)
    live_prices = Api.make_api_request(live_prices_request, stop_on_err = False)

    if live_prices != None:
        if live_prices["success"] == False:
            print("Falling back to Yahoo futures for live metal prices.")
            live_prices = None

    return_metals = []

    for metal in metals:
        if live_prices != None:
            last_price = float(1 / float(live_prices["rates"][metal["Symbol"].replace("-USD", "")]))
        else:
            if metal["Symbol"] == "XAG-USD":
                symbol = "SI=F"
            else:
                Io.error("Unknown metal symbol %s" % metal["Symbol"])
            last_price = Yahoo.get_live_price(symbol)
        new_metal = Instruments.Metal(metal["Symbol"], metal["Description"], metal["Quantity"], metal["Multiplier"], last_price = last_price)
        return_metals.append(new_metal)
    return(return_metals)

if __name__ == "__main__":
    main()
