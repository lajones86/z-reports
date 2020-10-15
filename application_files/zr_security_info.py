import os

import zr_io
import zr_csv

def get_symbol(symbol, element, default_type = None):

    #for securities_info.csv source
    column_list = [
            zr_csv.CsvColumn("Symbol", is_row_identifier = True),
            zr_csv.CsvColumn("Industry"),
            zr_csv.CsvColumn("Purpose")
            ]
    default_data = [[symbol, "Unknown", "Unknown"]]

    #create data structure if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "csv_data")
    csv_source = "securities_info.csv"

    if not os.path.isdir(data_dir):
        print("Creating .csv data directory at %s" % data_dir)
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, csv_source)

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
