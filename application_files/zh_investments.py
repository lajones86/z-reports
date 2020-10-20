import zm_physical as Physical
import zm_treasuries as Treasuries
import zm_fidelity as Fidelity

import zr_financial_concepts as Concepts
import zr_excel as Excel
import zr_config as Config


import xlsxwriter
import os

def process_brokerage_account(brokerage_account):
    print("Processing brokerage account %s" % brokerage_account.name)
    total_equity = float(0)
    for position in brokerage_account.positions:
        total_equity += position.equity
    total_equity += brokerage_account.cash_position
    return(Concepts.AccountSummary(brokerage_account.name, total_equity))


def process_commodities(commodities_list):
    print("Processing commodities.")
    tracking_commodities = []
    for commodity in commodities_list:
        try:
            #tracking commodities will have a symbol to track
            commodity.symbol
            tracking_commodities.append(Concepts.AccountSummary(commodity.description, commodity.emulated_stock.equity))
        except AttributeError:
            pass
    return(tracking_commodities)


def process_treasuries():
    print("Processing treasury bonds.")
    total_value = float(0)
    for bond in Treasuries.get_treasuries():
        total_value += bond.value
    return(Concepts.AccountSummary("Treasury Bonds", total_value))



def compile_investments():
    print("Aggregating investments.")

    brokerage_accounts = Concepts.SummaryCollection("Brokerage Accounts")

    commodities = Concepts.SummaryCollection("Commodities")

    other = Concepts.SummaryCollection("Other")

    brokerage_accounts.add_summary(process_brokerage_account(Fidelity.get_account()))

    for commodity in process_commodities(Physical.get_positions()):
        commodities.add_summary(commodity)

    other.add_summary(process_treasuries())

    return[brokerage_accounts, commodities, other]


def write_worksheet(xl_workbook, investments):
    #excel formatting
    xl_header = xl_workbook.add_format({"bold" : True, "underline" : True, "center_across" : True})
    xl_symbol = xl_workbook.add_format({"bold" : True, "italic" : True})
    xl_normal = xl_workbook.add_format({})
    xl_changeme = xl_workbook.add_format({"bg_color" : "orange"})
    xl_changeme_too = xl_workbook.add_format({"bg_color" : "yellow"})

    xl_worksheet = xl_workbook.add_worksheet("Investments")

    section_headers = ["Asset", "Equity", "Weight"]
    xl_row = 0
    xl_col = 0

    total_label = len(section_headers) + 1
    total_cell = total_label + 1
    subtotal_cells = []

    for investment in investments:
        xl_worksheet.merge_range("A%s:%s%s" % (str(xl_row + 1), Excel.get_letter(len(section_headers) - 1), str(xl_row + 1)), investment.description, xl_header)
        xl_row += 1

        for header in section_headers:
            xl_worksheet.write(xl_row, xl_col, header, xl_header)
            xl_col += 1

        xl_col = 0
        xl_row += 1
        start_row = xl_row + 1
        for summary in investment.summaries_list:
            for header in section_headers:
                if header == "Asset":
                    xl_worksheet.write(xl_row, xl_col, summary.name, xl_symbol)
                elif header == "Equity":
                    xl_worksheet.write(xl_row, xl_col, summary.balance, xl_normal)
                elif header == "Weight":
                    xl_worksheet.write_formula(xl_row, xl_col, "=%s%s/%s%s" %
                            (Excel.get_letter(xl_col - 1), xl_row + 1, Excel.get_letter(total_cell), 1))
                xl_col += 1
            xl_col = 0
            xl_row += 1

        end_row = xl_row

        xl_worksheet.write(xl_row, 0, "Total", xl_symbol)
        for header in section_headers[1::]:
            xl_col += 1
            xl_worksheet.write_formula(xl_row, xl_col, "=SUM(%s%s:%s%s)" %
                    (Excel.get_letter(xl_col), start_row, Excel.get_letter(xl_col), end_row))
            if header == "Equity":
                subtotal_cells.append([xl_col, end_row + 1])

        xl_row += 2
        xl_col = 0

    xl_worksheet.write(0, total_label, "Total", xl_symbol)
    total_formula = "%s%s" % (Excel.get_letter(subtotal_cells[0][0]), subtotal_cells[0][1])
    for cell in subtotal_cells[1::]:
        total_formula += "+%s%s" % (Excel.get_letter(cell[0]), cell[1])
    xl_worksheet.write_formula(0, total_cell, "=%s" % total_formula)
        

def main():
    investments = compile_investments()
    xl_wb_path = os.path.join(Config.get_path("reports_dir"), "Z-Report-Investments.xlsx")
    xl_workbook = xlsxwriter.Workbook(xl_wb_path)
    write_worksheet(xl_workbook, investments)
    Excel.save_workbook(xl_workbook, xl_wb_path)


if __name__ == "__main__":
    main()
