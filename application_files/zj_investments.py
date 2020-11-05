import zr_financial_concepts as Concepts
import zm_fidelity as Fidelity
import zm_treasuries as Treasuries
import zm_crypto as Crypto
import zm_metals as Metals
import zr_io as Io
import zr_excel as Excel
import zr_config as Config

import os
import xlsxwriter

def get_brokerages():
    fidelity_account = Fidelity.get_account()
    return([fidelity_account])

def get_investments():
    investments = Concepts.Investments()
    investments.brokerage_accounts = get_brokerages()
    investments.treasuries = Treasuries.get_emulated_stock()
    investments.crypto = Crypto.main()
    investments.metals = Metals.main()
    return(investments)

def write_worksheet(xl_workbook, investments):

    tab = Excel.InvestmentsTab()
    longest_left = 5

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

    #convert investments to summarycollection objects
    summaries_list = []

    #brokerage accounts
    brokerage_summaries = Concepts.SummaryCollection("Brokerage Accounts")
    for brokerage_account in investments.brokerage_accounts:
        new_brokerage_summary = Concepts.AccountSummary(brokerage_account.name, 0)
        for position in brokerage_account.stock_positions:
            new_brokerage_summary.balance += position.equity
        new_brokerage_summary.balance += brokerage_account.cash_position
        brokerage_summaries.add_summary(new_brokerage_summary)

    summaries_list.append(brokerage_summaries)

    #crypto
    crypto_summaries = Concepts.SummaryCollection("Cryptocurrency")
    for crypto in investments.crypto:
        new_crypto_summary = Concepts.AccountSummary(crypto.description, crypto.emulated_stock.equity)
        crypto_summaries.add_summary(new_crypto_summary)

    summaries_list.append(crypto_summaries)

    #metals
    metal_summaries = Concepts.SummaryCollection("Metals")
    for metal in investments.metals:
        new_metal_summary = Concepts.AccountSummary(metal.description, metal.emulated_stock.equity)
        metal_summaries.add_summary(new_metal_summary)

    summaries_list.append(metal_summaries)

    #bonds
    bond_summaries = Concepts.SummaryCollection("Bonds")
    bond_summaries.add_summary(Concepts.AccountSummary("Treasury Bonds", investments.treasuries.equity))

    summaries_list.append(bond_summaries)

    
    #reassign the variable because i'm shimming new objects into old code
    #it's a little sloppy, but the old code is already debugged
    investments = summaries_list


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
            if len(summary.name) > longest_left:
                longest_left = len(summary.name)
            for header in section_headers:
                if header == "Asset":
                    xl_worksheet.write(xl_row, xl_col, summary.name, xl_symbol)
                elif header == "Equity":
                    xl_worksheet.write(xl_row, xl_col, round(summary.balance, 2), xl_normal)
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

        tab_total_cell = "%s%s" % (Excel.get_letter(xl_col - 1), str(xl_row + 1))
        if investment.description == "Brokerage Accounts":
            tab.broker_total_cell = tab_total_cell
        elif investment.description == "Cryptocurrency":
            tab.crypto_total_cell = tab_total_cell
        elif investment.description == "Metals":
            tab.metal_total_cell = tab_total_cell
        elif investment.description == "Bonds":
            tab.bond_total_cell = tab_total_cell

        xl_row += 2
        xl_col = 0

    xl_worksheet.write(0, total_label, "Total", xl_symbol)
    total_formula = "%s%s" % (Excel.get_letter(subtotal_cells[0][0]), subtotal_cells[0][1])
    for cell in subtotal_cells[1::]:
        total_formula += "+%s%s" % (Excel.get_letter(cell[0]), cell[1])
    xl_worksheet.write_formula(0, total_cell, "=%s" % total_formula)

    xl_worksheet.set_column(0, 0, longest_left)
    xl_worksheet.set_column(1, 1, 12)
    xl_worksheet.set_column(5, 5, 12)

    return(tab)


def main(investments = None):
    if investments == None:
        investments = get_investments()
    xl_wb_path = os.path.join(Config.get_path("reports_dir"), "Investments.xlsx")
    xl_workbook = xlsxwriter.Workbook(xl_wb_path)
    write_worksheet(xl_workbook, investments)
    Excel.save_workbook(xl_workbook, xl_wb_path)
    return(investments)

if __name__ == "__main__":
    main()
