#for dealing with physical commodities
import os

import zr_config
import zr_csv
import zr_financial_instruments as Instruments


def get_positions():
    csv_source = zr_config.get_path("physical_commodities")
    positions = []

    column_list = [
            zr_csv.CsvColumn(name = "Symbol", is_row_identifier = True),
            zr_csv.CsvColumn(name = "Description"),
            zr_csv.CsvColumn(name = "Quantity", data_type = "int"),
            zr_csv.CsvColumn(name = "Multiplier", data_type = "float")
            ]

    default_data_rows = [
            ["GC=F", "Gold, Troy Ounce", 0, .9],
            ["SI=F", "Silver, Troy Ounce", 0, .9]
            ]

    csv_file = zr_csv.CsvFile(csv_source, default_column_list = column_list,
            default_data_rows = default_data_rows, stop_on_write = False,
            read_only = False)

    for commodity in csv_file.return_all():
        if commodity["Quantity"] != 0:
            adjusted_quantity = commodity["Quantity"] * commodity["Multiplier"]
            positions.append(Instruments.StockPosition(commodity["Symbol"], adjusted_quantity))

    return(positions)

if __name__ == "__main__":
    for position in get_positions():
        print(position.symbol, position.quantity, position.last_price, position.equity)

