#Usage: CsvFile(path, default_column_list = [], default_data_rows = [], stop_on_write = True, read_only = True)
#defaults to read-only mode with no extraneous data

#turning off read_only and providing default column list and data rows
#will update the target file to contain new defaults
#as well as filling in default values as defined by CsvColumn objects with overwrite_with_default set to true
#while keeping any extraneous data entered by a user (exept that in columns where overwrite_with_default is true)

#you can also provide a CsvColumn in defaults
#named after an existing file column with is_row_identifier set to true
#even with read only, this will enable you to use the find_by_id function


#find_by_id(id) takes an id as an argument and
#returns an entire row as a dict in form { "column name" : "value" ... }
#it is type-sensitive

#find_by_id_strcomp(id) takes an id as an argument and
#converts ids to strings in order to perform comparisons and 
#returns an entire row in the same format as find_by_id(id)

#find_by_dict(dict) takes a dict as an argument
#in the format { "column name" : "value" ... } and
#returns a list of rows
#with the rows in the same format as above

#find_by_dict_strcomp(dict) performs like find_by_dict(dict)
#except all values are converted to strings for comparison

#return_all() returns all rows in the format described above

#columns that do not have headers produce funny results
#but do not affect retrieval of columns that have headers

#see test() function for usage example

import zr_io

import csv
import os
from copy import deepcopy


class CsvColumnMap:
    def __init__(self, provided_columns = []):
        self.columns = []

        for provided_column in provided_columns:
            self.add_column(provided_column)

    def add_column(self, column_to_add):
        if column_to_add.is_row_identifier:
            for existing_column in self.columns:

                if existing_column.is_row_identifier:
                    zr_io.error("Tried to add %s as row identifier, but %s already exists as row identifier." %
                            (column_to_add.name, existing_column.name))

                if existing_column.name == column_to_add.name:
                    zr_io.error("Tried to add %s to column map, but it already exists." % column_to_add.name)

        self.columns.append(column_to_add)

    def remove_column(self, column_to_remove):
        self.columns.remove(column_to_remove)

    def get_column_by_name(self, column_name):
        for column in self.columns:
            if column.name == column_name:
                return(column)
        return(None)

    def get_identifier(self):
        for column in self.columns:
            if column.is_row_identifier:
                return(column)
        return(None)


#valid data types:
#str
#int
#float
#bool
class CsvColumn:
    def __init__(self, name, data_type = "str", is_row_identifier = False, overwrite_with_default = False):
        self.name = name
        self.is_row_identifier = is_row_identifier
        self.default_position = None
        self.file_position = None
        self.data_type = data_type
        self.overwrite_with_default = overwrite_with_default
        self.final_position = None

        if is_row_identifier:
            if name == "":
                zr_io.error("Unnamed column cannot be row identifier.")
            if overwrite_with_default:
                zr_io.error("Cannot have overwrite_with_default set to True for row identifiers.")

        if data_type not in ["str", "int", "float", "bool"]:
            zr_io.error("Unknown data type %s" % data_type)


#store header map in self.column_map
#store data in self.data
class CsvFile:
    def __init__(self, path, default_column_list = [], default_data_rows = [], stop_on_write = True, read_only = True):
        self.read_only = read_only
        if not self.read_only:
            if len(default_column_list) == 0:
                print("Empty default column list. Setting read-only to True.")
                self.read_only = True
            if len(default_data_rows) == 0:
                print("No default data rows provided. Setting read-only to True.")
                self.read_only = True

        #check validity of supplied defaults
        if len(default_data_rows):
            for row in default_data_rows:
                if type(row) != type([]):
                    zr_io.error("Default data row should be a list of list, but contains %s" % (type(row)))
        if len(default_column_list):
            test_column = CsvColumn("test")
            for default_column in default_column_list:
                if type(default_column) != type(test_column):
                    zr_io.error("Default column list should contain CsvColumn objects, but contains %s" % type(default_column))
            del test_column


        default_column_map = CsvColumnMap(default_column_list)

        if not read_only:
            if not default_column_map.get_identifier():
                zr_io.error("No default columns marked as row identifier.")
        col_counter = 0
        for column in default_column_map.columns:
            column.default_position = col_counter
            col_counter += 1

        self.set_types(default_data_rows, default_column_map)

        self.write_file_flag = False
        if os.path.isfile(path):
            file_data_rows = []
            file_data_rows = self.csv_to_list(path)
            file_column_map = self.map_file_columns(file_data_rows, default_column_map)

            #delete the header row now that we've got what we need from it
            if len(file_data_rows):
                del file_data_rows[0]

            self.set_types(file_data_rows, file_column_map)

            col_counter = 0
            for column in file_column_map.columns:
                column.file_position = col_counter
                col_counter += 1

            self.column_map = self.combine_column_maps(default_column_map, file_column_map)
            self.data = self.combine_data_rows(default_data_rows, file_data_rows)

        #if the file doesn't already exist
        else:
            self.column_map = default_column_map
            self.write_file_flag = True
            self.data = default_data_rows

        #finalize/normalize the info we're holding
        col_counter = 0
        for column in self.column_map.columns:
            column.final_position = col_counter
            col_counter += 1


        if self.write_file_flag:
            self.write_file(path, stop_on_write)


    def return_all(self):
        return_list = []
        for row in self.data:
            new_dict = {}
            for column in self.column_map.columns:
                try:
                    new_dict[column.name] = row[column.final_position]
                except IndexError:
                    new_dict[column.name] = ""
            return_list.append(new_dict)
        return(return_list)


    def find_by_id(self, id_to_find, strcomp = False):
        if strcomp == True:
            id_to_find = str(id_to_find)
        id_col = self.column_map.get_identifier()
        return_dict = {}
        for row in self.data:
            row_id_val = row[id_col.final_position]
            if strcomp == True:
                row_id_val = str(row_id_val)
            if row_id_val == id_to_find:
                for column in self.column_map.columns:
                    try:
                        return_dict[column.name] = row[column.final_position]
                    except IndexError:
                        return_dict[column.name] = None
        return(return_dict)


    def find_by_id_strcomp(self, id_to_find):
        return(self.find_by_id(id_to_find, strcomp = True))


    def find_by_dict(self, dict_params, strcomp = False):
        return_list = []
        for row in self.data:
            row_is_match = True
            for key in dict_params.keys():
                param_value = dict_params[key]
                if strcomp == True:
                    param_value = str(param_value)
                key_column = self.column_map.get_column_by_name(key)
                try:
                    row_value = row[key_column.final_position]
                except IndexError:
                    row_is_match = False
                    break
                if strcomp == True:
                    row_value = str(row_value)
                if row_value != param_value:
                    row_is_match = False
                    break
            if row_is_match:
                new_dict = {}
                for column in self.column_map.columns:
                    try:
                        new_dict[column.name] = row[column.final_position]
                    except IndexError:
                        new_dict[column.name] = ""
                return_list.append(new_dict)
        return(return_list)


    def find_by_dict_strcomp(self, dict_params):
        return(self.find_by_dict(dict_params, strcomp = True))


    def write_file(self, path, stop_on_write):
        if self.read_only:
            return(None)

        header_row = []
        for column in self.column_map.columns:
            header_row.append(column.name)
        output_csv_list = [header_row]
        for row in self.data:
            output_csv_list.append(row)

        with open(path, "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerows(output_csv_list)

        print("Wrote to %s" % path)
        if stop_on_write:
            zr_io.message("Verify accuracy of file and run again. This is not an error.")


    def set_types(self, data_rows, column_map):
        for row in data_rows:
            col_counter = 0
            for column in column_map.columns:
                try:
                    if column.data_type == "str":
                        row[col_counter] = str(row[col_counter])
                    elif column.data_type == "int":
                        row[col_counter] = int(row[col_counter])
                    elif column.data_type == "float":
                        row[col_counter] = float(row[col_counter])
                    elif column.data_type == "bool":
                        value_base = str(row[col_counter])
                        if value_base == "True" or value_base == "true" or value_base == "t" or value_base == "1":
                            row[col_counter] = True
                        elif value_base == "False" or value_base == "false" or value_base == "f" or value_base == "0":
                            row[col_counter] = False
                except ValueError:
                    pass
                except IndexError:
                    pass
                col_counter += 1


    def combine_data_rows(self, default_data_rows, file_data_rows_original):
        return_data_rows = []
        file_data_rows = deepcopy(file_data_rows_original)

        #start with default rows
        for default_row in default_data_rows:
            new_row = []
            id_col = self.column_map.get_identifier()
            row_identifier_value = default_row[id_col.default_position]
            #find row from file with matching identifier
            matching_file_row = None
            for file_row in file_data_rows:
                try:
                    if file_row[id_col.file_position] == row_identifier_value:
                        matching_file_row = file_row
                except IndexError:
                    pass

            if not matching_file_row:
                new_row = default_row
                self.write_file_flag = True

            #we have a default row and its matching file row
            #now fill the row based on the column map
            else:
                for column in self.column_map.columns:
                    new_cell_value = None
                    try:
                        if column.file_position != None:
                            new_cell_value = matching_file_row[column.file_position]
                    except IndexError:
                        self.write_file_flag = True
                    try:
                        if column.default_position != None:
                            default_value = default_row[column.default_position]
                    except IndexError:
                        pass
                    if column.overwrite_with_default:
                        if new_cell_value != default_value:
                            self.write_file_flag = True
                            new_cell_value = default_value
                    if new_cell_value == None:
                        new_cell_value = ""
                    new_row.append(new_cell_value)
                file_data_rows.remove(matching_file_row)
            return_data_rows.append(new_row)

        #we've removed all the rows with a matching default
        for file_row in file_data_rows:
            new_row = []
            for column in self.column_map.columns:
                try:
                    new_cell_value = file_row[column.file_position]
                except IndexError:
                    new_cell_value = ""
                new_row.append(new_cell_value)
            return_data_rows.append(new_row)
        return(return_data_rows)


    def combine_column_maps(self, default_column_map, file_column_map_original):
        #make a local copy of the file column map because we'll be modifying it
        file_column_map = deepcopy(file_column_map_original)
        return_column_map = CsvColumnMap()

        #build using default columns first
        for default_column in default_column_map.columns:
            matching_file_column = file_column_map.get_column_by_name(default_column.name)
            if not matching_file_column:
                #if a default column isn't in the file, we need to write
                self.write_file_flag = True
            else:
                #remove the element because we'll be iterating what's left
                file_column_map.remove_column(matching_file_column)
            return_column_map.add_column(default_column)

        #now append any non-default columns
        for file_column in file_column_map.columns:
            return_column_map.add_column(file_column)

        return(return_column_map)


    def column_list_to_map(self, column_list, default_column_map):
        return_column_map = CsvColumnMap()
        for column_name in column_list:
            matching_default = default_column_map.get_column_by_name(column_name)
            if matching_default:
                return_column_map.add_column(matching_default)
            else:
                return_column_map.add_column(CsvColumn(column_name))
        return(return_column_map)


    def map_file_columns(self, csv_contents, default_column_map):
        map_length = self.get_longest_row([csv_contents])
        column_list = []
        for cell in csv_contents[0]:
            column_list.append(cell)
        while len(column_list) < map_length:
            column_list.append("")
        return(self.column_list_to_map(column_list, default_column_map))


    def get_longest_row(self, list_of_csvs):
        max_length = 0
        for csv in list_of_csvs:
            for row in csv:
                temp_row = row[:]
                try:
                    while temp_row[-1] == "":
                        del temp_row[-1]
                #row is empty
                except IndexError:
                    pass
                if len(temp_row) > max_length:
                    max_length = len(temp_row)
        return(max_length)


    #return csv file as a list of lists
    def csv_to_list(self, path):
        return_list = []
        with open(path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                return_list.append(row)
        return(return_list)


def test():
    path = os.path.join(os.environ["USERPROFILE"], r"Desktop\z_test.csv")
    default_column_map = [
            CsvColumn(name = "ID", data_type = "int", is_row_identifier = True),
            CsvColumn(name = "Name"),
            CsvColumn(name = "Meaningful", data_type = "bool"),
            CsvColumn(name = "Decimal", data_type = "float", overwrite_with_default = True),
            CsvColumn(name = "Notes"),
            CsvColumn(name = "Stooge")
        ]

    default_data_rows = [
            [1, "Pi", True, 3.14, "I like rusty spoons.", "Moe"],
            [2, "Euler", True, 2.72, "Hello, Hubert Cumberdale.", "Larry"],
            [3, "Foo", False, 45.22, "I left my bacon at the tennis patch.", "Curly"],
            [4, "Bar", False, 8.12, "My brother, Kenneth, has returned from the Great War.", "Shemp"],
            [5, "Foobar", False, 7.7, "I'm a song from the sixties.", "Joe"]
        ]

    csv_file = CsvFile(path, default_column_map, default_data_rows, stop_on_write = False, read_only = False)

    print(csv_file.find_by_id(1))

    print(csv_file.find_by_id_strcomp("2"))

    for i in csv_file.find_by_dict({"Name" : "Foo", "Meaningful" : False}):
        print(i)

    for i in csv_file.find_by_dict_strcomp({"Name" : "Bar", "Meaningful" : "False"}):
        print(i)

    for i in csv_file.return_all():
        print(i)

    exit(0)

if __name__ == "__main__":
    test()
