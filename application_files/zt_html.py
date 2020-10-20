import re
import zr_io

#object for tracking variables for the treasury.gov website
class SiteTreasuryBond():
    def __init__(self, variable_line):
        re_name = re.compile("name=\".*?\"")
        re_value = re.compile("value=\".*?\"")
        self.name = re_name.search(variable_line).group(0).replace("name=", "").replace("\"", "")
        self.value = re_value.search(variable_line).group(0).replace("value=", "").replace("\"", "")


def get_by_xpath(root_element, xpath, min_results = None, max_results = None, description = None):

    if description == None:
        description = ""

    return_collection = root_element.xpath(xpath)

    if min_results:
        min_results = int(min_results)
        if len(return_collection) < min_results:
            zr_io.error("%s Error: expected at least %s results, got %s" %
                    (description, str(min_results), str(len(return_collection))))
    if max_results:
        max_results = int(max_results)
        if len(return_collection) > max_results:
            zr_io.error("%s Error: expected no more than %s results, got %s" %
                    (description, str(max_results), str(len(return_collection))))

    return(return_collection)


def map_table_from_thead(thead_element, desired_headers_contain = None):

    if desired_headers_contain == None:
        desired_headers_contain = []

    th_collection = get_by_xpath(thead_element, ".//th",
            min_results = 1, description = "Table mapping")

    table_map = {}
    col_counter = 0

    for th in th_collection:
        consolidated_text = ""
        for th_text in get_by_xpath(th, ".//*[text()]"):
            consolidated_text += str(th_text.text).strip()

        if len(desired_headers_contain) == 0:
            table_map[consolidated_text] = col_counter
        else:
            for dh in desired_headers_contain:
                if dh.lower() in consolidated_text.lower():
                    table_map[dh] = col_counter
        col_counter += 1

    return(table_map)
