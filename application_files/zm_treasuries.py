import os
import re
import mechanicalsoup

import zr_config
import zt_html
import zr_financial_instruments as Instruments

def get_treasuries():
    treasuries = []
    treasuries_source = zr_config.get_path("treasuries")

    if not os.path.isfile(treasuries_source):
        print("Treasuries file not found.")

    else:
        print("Processing %s" % treasuries_source)
        re_variables_section = re.compile("\<\!\-\- Hidden Variables \-\-\>.*\<\!\-\- Hidden Variables \-\-\>", re.DOTALL)
        treasuries_file_contents = ""
        with open(treasuries_source, "r") as f:
            for line in f:
                treasuries_file_contents += line
        variables_section = re_variables_section.search(treasuries_file_contents)
        if not variables_section:
            print("Variables section not found in treasuries file.")
        #process treasuries file
        else:
            #get variables from treasuries file
            variables = []
            variables_section = variables_section.group(0)
            re_variable = re.compile("\<input type.*?\>")
            for variable in re_variable.findall(variables_section):
                variables.append(zt_html.SiteTreasuryBond(variable))

            #open treasury site and submit variables
            browser = mechanicalsoup.StatefulBrowser()
            browser.open("https://www.treasurydirect.gov/BC/SBCPrice")
            browser.select_form('form[action="https://www.treasurydirect.gov/BC/SBCPrice"]')
            for variable in variables:
                browser[variable.name] = variable.value
            treasuries_return = browser.submit_selected().text

            #extract bond data returned from treasuries site
            re_bond_data = re.compile("\<td class\=\"lft\".*?\<\/strong\>\<\/td>", re.DOTALL)
            for bond in re_bond_data.findall(treasuries_return):
                treasuries.append(Instruments.TreasuryBond(bond))

    return(treasuries)

if __name__ == "__main__":
    for i in get_treasuries():
        print(i.serial, i.series, i.denomination, i.issue_date, i.next_accrual, i.maturity_date, i.issue_price, i.interest, i.rate, i.value)
