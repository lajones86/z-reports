import os

import zr_io as Io
import zr_csv
import zr_config

def set_new_info(symbol, element, csv_file):
    print("Uknown %s for %s." % (element, symbol))

    security_categories = csv_file.find_unique_by_column(element)
    security_categories.remove("Unknown")
    security_categories.sort()
    count = 0
    selection_string = ""
    for i in security_categories:
        selection_string += "[%s] %s\t" % (str(count), i)
        count += 1
        if count % 3 == 0:
            selection_string += "\n"
    selection_string = selection_string.rstrip("\n") + ("\n[%s] Enter new %s" % (str(count), element))

    accepted = False
    while accepted != True:
        print("\nSelect %s\n" % element)
        print(selection_string)
        selection = input("\n> ")
        try:
            selection = int(selection)
            if selection == len(security_categories):
                new_cat = input("\nEnter new category: ")
            else:
                new_cat = security_categories[selection]
            accepted = Io.yes_no("Set %s for %s to %s?" % (element, symbol, new_cat))
        except:
            print("\nInvalid selection")
    return(new_cat)


def get_symbol(symbol, element, default_type = None, quickrun = None):

    #for securities_info.csv source
    column_list = [
            zr_csv.CsvColumn("Symbol", is_row_identifier = True),
            zr_csv.CsvColumn("Industry"),
            zr_csv.CsvColumn("Purpose")
            ]
    default_data = [[symbol, "Unknown", "Unknown"]]

    file_path = zr_config.get_path("securities_info")

    csv_file = zr_csv.CsvFile(file_path, default_column_list = column_list,
            default_data_rows = default_data, read_only = True) 

    security_row = csv_file.find_by_id(symbol)

    #prompt for security info if it's unknown
    if quickrun != True:
        write_new_data = False

        for info_element in [["Industry", 1], ["Purpose", 2]]:
            if security_row[info_element[0]] == "Unknown":
                write_new_data = True
                new_value = set_new_info(symbol, info_element[0], csv_file)
                default_data[0][info_element[1]] = new_value

        csv_file = zr_csv.CsvFile(file_path, default_column_list = column_list,
                default_data_rows = default_data, read_only = False,
                stop_on_write = False)

        security_row = csv_file.find_by_id(symbol)

    return(security_row[element])


def get_industry(symbol, quickrun = None):
    return(get_symbol(symbol, "Industry"))


def get_purpose(symbol, quickrun = None):
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
