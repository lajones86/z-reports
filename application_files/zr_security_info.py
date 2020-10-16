import os

import zr_io
import zr_csv
import zr_config

def get_symbol(symbol, element, default_type = None):

    #for securities_info.csv source
    column_list = [
            zr_csv.CsvColumn("Symbol", is_row_identifier = True),
            zr_csv.CsvColumn("Industry"),
            zr_csv.CsvColumn("Purpose")
            ]
    default_data = [[symbol, "Unknown", "Unknown"]]

    file_path = zr_config.get_path("securities_info")

    csv_file = zr_csv.CsvFile(file_path, default_column_list = column_list,
            default_data_rows = default_data, read_only = False,
            stop_on_write = False) 

    security_row = csv_file.find_by_id(symbol)

    return(security_row[element])


def get_industry(symbol):
    return(get_symbol(symbol, "Industry"))


def get_purpose(symbol):
    return(get_symbol(symbol, "Purpose"))


def test():
    symbol = input("Enter symbol: ")
    print(symbol)
    print(get_industry(symbol))
    print(get_purpose(symbol))
    try:
        for bond in get_bond_list():
            print(bond.symbol, bond.description)
    except:
        print("Bonds not present")


if __name__ == "__main__":
    test()
