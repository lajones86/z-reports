from os.path import isfile

import zr_csv as Csv
import zr_config as Config
import zr_io as Io

def get_sum():
    misc_sum = float(0)
    misc_path = Config.get_path("misc_assets_csv")
    if not isfile(misc_path):
        with open(misc_path, "w") as f:
            f.write("Description,Serial No.,Estimated Value,Notes")
    default_column_map = [
            Csv.CsvColumn(name = "Description", data_type = "str", is_row_identifier = True),
            Csv.CsvColumn(name = "Serial No.", data_type = "str"),
            Csv.CsvColumn(name = "Estimated Value", data_type = "float"),
            Csv.CsvColumn(name = "Notes", data_type = "str")
            ]
    default_data_rows = []
    csv_file = Csv.CsvFile(misc_path, default_column_map, default_data_rows, read_only = True)
    for i in csv_file.return_all():
        try:
            value = float(i["Estimated Value"])
            misc_sum += value
        except ValueError:
            Io.nostop("Error parsing %s as float number in %s" % (str(value), misc_path))
    return(misc_sum)


if __name__ == "__main__":
    print(get_sum())
