import zr_csv as Csv
import zr_config as Config
import zr_io as Io
import zr_financial_concepts as Concepts
import zr_excel as Excel
import zm_ledger as ReadLedger

from dateutil.relativedelta import relativedelta
from datetime import datetime
import os
import xlsxwriter
import shutil

def get_tabs(accounts):
    tabs = []
    institutions = []
    asset_lists = [accounts.checking_accounts, accounts.savings_accounts]

    for asset_list in asset_lists:
        for account in asset_list:
            institution = account.institution
            if not institution in institutions:
                institutions.append(institution)

    for institution in institutions:
        inst_accounts = []
        for asset_list in asset_lists:
            for account in asset_list:
                if account.institution == institution and account.account_type != "Credit Card":
                    inst_accounts.append(account)
        if len(inst_accounts) > 0:
            tabs.append(Excel.LedgerTab(inst_accounts[0].institution, inst_accounts))

    tabs.append(Excel.LedgerTab("Credit Cards", accounts.credit_cards))

    return(tabs)


def get_accounts_by_type(csv_file, account_type):
    return_list = []
    for account in csv_file.find_by_dict({"Account Type" : account_type}):
        new_account = Concepts.LedgerAccount(account["Account Name"], account["Institution"], account["Account Type"])
        ReadLedger.load_ledger_entries(new_account)
        return_list.append(new_account)
    return(return_list)


def get_accounts():
    columns = [
            Csv.CsvColumn(name = "Account Name", is_row_identifier = True),
            Csv.CsvColumn(name = "Institution"),
            Csv.CsvColumn(name = "Account Type")
            ]

    accounts_csv_path = Config.get_path("accounts_csv")
    Csv.write_empty(accounts_csv_path, columns)

    accounts_csv = Csv.CsvFile(accounts_csv_path, default_column_list = columns, default_data_rows = [])

    if len(accounts_csv.return_all()) == 0:
        Io.error("%s does not contain any accounts!" % accounts_csv_path)

    checking_accounts = get_accounts_by_type(accounts_csv, "Checking")
    savings_accounts = get_accounts_by_type(accounts_csv, "Savings")
    credit_cards = get_accounts_by_type(accounts_csv, "Credit Card")

    return(Concepts.LedgerAccountCollection(checking_accounts = checking_accounts, savings_accounts = savings_accounts, credit_cards = credit_cards))


def get_tab_type(tab):
    if len(tab.savings) > 0 or len(tab.checking) > 0:
        return("asset")
    elif len(tab.credit_cards) > 0:
        return("liability")

def add_ledger_tab(xl_workbook, tab):
    amount_format = xl_workbook.add_format({"num_format" : "#,##0.00" ";(#,##0.00)"})
    date_format = xl_workbook.add_format({"num_format" : "YYYY-MM-DD"})
    xl_section = xl_workbook.add_format({"bold" : True, "underline" : True, "center_across" : True})
    xl_header = xl_workbook.add_format({"italic" : True, "underline" : True, "center_across" : True})
    italic = xl_workbook.add_format({"italic" : True})
    bold = xl_workbook.add_format({"bold" : True})
    bold_italic = xl_workbook.add_format({"bold" : True, "italic" : True})

    sheet_name = tab.name
    xl_worksheet = xl_workbook.add_worksheet(sheet_name)
    section_headers = ["Date", "Description", "Amount"]
    tab_type = get_tab_type(tab)
    xl_col = 0 
    xl_row = 0
    for account_list in [tab.checking, tab.savings, tab.credit_cards]:
        for account in account_list:
            base_xl_col = xl_col
            xl_worksheet.merge_range("%s1:%s1" % (Excel.get_letter(xl_col), Excel.get_letter(xl_col + 2)), account.name, xl_section)
            xl_row += 1
            for header in section_headers:
                xl_worksheet.write(xl_row, xl_col, header, xl_header)
                xl_col += 1

            xl_row += 1
            balance_date = datetime.now().date().replace(day = 1)
            xl_worksheet.write_datetime(xl_row, base_xl_col, balance_date)
            xl_worksheet.write(xl_row, base_xl_col + 1, "Balance")
            xl_worksheet.write(xl_row, base_xl_col + 2, round(account.book_balance, 2))
            account.amount_col = Excel.get_letter(base_xl_col + 2)

            xl_worksheet.set_column(base_xl_col, base_xl_col, 12, date_format)
            xl_worksheet.set_column(base_xl_col + 1, base_xl_col + 1, 25)
            xl_worksheet.set_column(base_xl_col + 2, base_xl_col + 2, 10, amount_format)
            xl_worksheet.set_column(base_xl_col + 3, base_xl_col + 3, 5)

            for book_entry in account.book_entries:
                xl_row += 1
                xl_worksheet.write(xl_row, base_xl_col, book_entry.date)
                xl_worksheet.write(xl_row, base_xl_col + 1, book_entry.description)
                xl_worksheet.write(xl_row, base_xl_col + 2, round(book_entry.amount, 2))

            xl_col += 1
            xl_row = 0

    #fill out math section on right
    base_xl_col = xl_col
    summary_headers = [["Item", 16], ["Balance", 10], ["Adj Pending", 12], ["Adj Balance", 12]]

    tab.summary_start_col = base_xl_col
    tab_type = get_tab_type(tab)

    for header in summary_headers:
        xl_worksheet.write(xl_row, xl_col, header[0], xl_header)
        if header[0] in ["Balance", "Adj Pending", "Adj Balance"]:
            col_format = amount_format
        else:
            col_format = None
        xl_worksheet.set_column(xl_col, xl_col, header[1], col_format)
        xl_col += 1

    xl_col = base_xl_col
    xl_row += 1
    for account_list in [tab.checking, tab.savings, tab.credit_cards]:
        for account in account_list:
            xl_worksheet.write(xl_row, base_xl_col, account.name, italic)

            xl_worksheet.write_formula(xl_row, base_xl_col + 1, "=SUM(%s:%s)" % (account.amount_col, account.amount_col))

            #mark account balance cell info here
            account.balance_cell = "%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row + 1)
            account.balance_adj_cell = "%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row + 1)

            xl_worksheet.write_formula(xl_row, base_xl_col + 3, "=%s+%s" % (account.balance_cell, account.balance_adj_cell))

            xl_row += 1

    #total accounts for tab
    xl_worksheet.write(xl_row, base_xl_col, "%s Total" % tab.name, bold)

    xl_worksheet.write_formula(xl_row, base_xl_col + 1, "=SUM(%s%s:%s%s)" % (
        Excel.get_letter(base_xl_col + 1), str(2),
        Excel.get_letter(base_xl_col + 1), str(xl_row)))

    xl_worksheet.write_formula(xl_row, base_xl_col + 2, "=SUM(%s%s:%s%s)" % (
        Excel.get_letter(base_xl_col + 2), str(2),
        Excel.get_letter(base_xl_col + 2), str(xl_row)))

    xl_worksheet.write_formula(xl_row, base_xl_col + 3, "=SUM(%s%s:%s%s)" % (
        Excel.get_letter(base_xl_col + 3), str(2),
        Excel.get_letter(base_xl_col + 3), str(xl_row)))

    #mark cc total cell info here for cc page
    if tab_type == "liability":
        tab.cc_total_cell = "%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row + 1)
        tab.cc_total_adj_cell = "%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row + 1)

    xl_row += 2
    #credit card section for asset pages
    if tab_type == "asset":
        xl_worksheet.write(xl_row, base_xl_col, "Credit Card Total", italic)
        tab.cc_total_cell = "%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row + 1)
        tab.cc_total_adj_cell = "%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row + 1)
        xl_worksheet.write_formula(xl_row, base_xl_col + 3, "=%s+%s" % (tab.cc_total_cell, tab.cc_total_adj_cell))

    #asset section for credit card page
    elif tab_type == "liability":
        xl_worksheet.write(xl_row, base_xl_col, "Checking Total", italic)
        tab.checking_total_cell = "%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row + 1)
        tab.checking_total_adj_cell = "%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row + 1)
        xl_worksheet.write_formula(xl_row, base_xl_col + 3, "=%s+%s" % (tab.checking_total_cell, tab.checking_total_adj_cell))
        xl_row += 1
        xl_worksheet.write(xl_row, base_xl_col, "Savings Total", italic)
        tab.savings_total_cell = "%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row + 1)
        tab.savings_total_adj_cell = "%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row + 1)
        xl_worksheet.write_formula(xl_row, base_xl_col + 3, "=%s+%s" % (tab.savings_total_cell, tab.savings_total_adj_cell))

    #surplus/deficit
    xl_row += 2
    xl_worksheet.write(xl_row, base_xl_col, "Surplus(Deficit)", bold)
    if tab_type == "asset":
        surplus_formula = "=0"
        for account in tab.checking:
            surplus_formula += "+%s" % account.balance_cell
        surplus_formula += "-%s" % tab.cc_total_cell
        xl_worksheet.write_formula(xl_row, base_xl_col + 1, surplus_formula)
        surplus_formula = "=0"
        for account in tab.checking:
            surplus_formula += "+%s" % account.balance_adj_cell
        surplus_formula += "-%s" % tab.cc_total_adj_cell
        xl_worksheet.write_formula(xl_row, base_xl_col + 2, surplus_formula)
    elif tab_type == "liability":
        surplus_formula = "%s%s-%s" % (Excel.get_letter(base_xl_col + 1), str(xl_row - 2), tab.cc_total_cell)
        xl_worksheet.write_formula(xl_row, base_xl_col + 1, surplus_formula)
        surplus_formula = "%s%s-%s" % (Excel.get_letter(base_xl_col + 2), str(xl_row - 2), tab.cc_total_adj_cell)
        xl_worksheet.write_formula(xl_row, base_xl_col + 2, surplus_formula)
    surplus_adjusted_formula = "=%s%s+%s%s" % (
            Excel.get_letter(base_xl_col + 1), xl_row + 1,
            Excel.get_letter(base_xl_col + 2), xl_row + 1)
    xl_worksheet.write_formula(xl_row, base_xl_col + 3, surplus_adjusted_formula)

    #plus savings
    xl_row += 1
    xl_worksheet.write(xl_row, base_xl_col, "Plus Savings", bold_italic)
    if tab_type == "asset":
        plus_savings_formula = "=%s%s" % (Excel.get_letter(base_xl_col + 1), xl_row)
        for account in tab.savings:
            plus_savings_formula += "+%s" % account.balance_cell
        xl_worksheet.write_formula(xl_row, base_xl_col + 1, plus_savings_formula)
        plus_savings_formula = "=%s%s" % (Excel.get_letter(base_xl_col + 2), xl_row)
        for account in tab.savings:
            plus_savings_formula += "+%s" % account.balance_adj_cell
        xl_worksheet.write_formula(xl_row, base_xl_col + 2, plus_savings_formula)
    elif tab_type == "liability":
        plus_savings_formula = "=%s%s+%s" % (Excel.get_letter(base_xl_col + 1), xl_row, tab.savings_total_cell)
        xl_worksheet.write_formula(xl_row, base_xl_col + 1, plus_savings_formula)
        plus_savings_formula = "=%s%s+%s" % (Excel.get_letter(base_xl_col + 2), xl_row, tab.savings_total_adj_cell)
        xl_worksheet.write_formula(xl_row, base_xl_col + 2, plus_savings_formula)

    adjusted_total_formula = "=%s%s+%s%s" % (
            Excel.get_letter(base_xl_col + 1), xl_row + 1,
            Excel.get_letter(base_xl_col + 2), xl_row + 1)
    xl_worksheet.write_formula(xl_row, base_xl_col + 3, adjusted_total_formula)

    return(xl_worksheet)


def add_reconciliations(xl_workbook, tab):
    amount_format = xl_workbook.add_format({"num_format" : "#,##0.00" ";(#,##0.00)"})
    date_format = xl_workbook.add_format({"num_format" : "YYYY-MM-DD"})
    xl_section = xl_workbook.add_format({"bold" : True, "underline" : True, "center_across" : True})
    xl_header = xl_workbook.add_format({"italic" : True, "underline" : True, "center_across" : True})
    italic = xl_workbook.add_format({"italic" : True})
    bold = xl_workbook.add_format({"bold" : True})

    widths = [12, 16, 12, 10, 5, 12, 25, 10, 5, 12, 25, 10]

    for account_list in [tab.checking, tab.savings, tab.credit_cards]:
        for account in account_list:
            sheet_name = account.name + " - Rec"
            xl_worksheet = xl_workbook.add_worksheet(sheet_name)
            xl_worksheet.write(0, 1, "Book Balance", italic)
            xl_worksheet.write_formula(0, 2, "='%s'!%s" % (tab.name, account.balance_cell), amount_format)
            xl_worksheet.write(1, 1, "Book Adjustments", italic)
            xl_worksheet.write_formula(1, 2, "=SUM(H:H)", amount_format)
            xl_worksheet.write(2, 2, "Book Total", bold)
            xl_worksheet.write_formula(2, 3, "C1+C2", amount_format)
            xl_worksheet.write(4, 0, account.rec_date)
            xl_worksheet.write(4, 1, "Bank Balance", italic)
            xl_worksheet.write(4, 2, round(account.bank_balance, 2), amount_format)
            xl_worksheet.write(5, 1, "Bank adjustments", italic)
            xl_worksheet.write_formula(5, 2, "=SUM(L:L)", amount_format)
            xl_worksheet.write(6, 2, "Bank Total", bold)
            xl_worksheet.write_formula(6, 3, "=C5+C6", amount_format)
            xl_worksheet.write_formula
            xl_worksheet.write(7, 2, "Over(Under)", bold)
            xl_worksheet.write(7, 3, "=D7-D3", amount_format)
            xl_worksheet.merge_range("F1:H1", "Book Adjustments", xl_section)
            xl_worksheet.merge_range("J1:L1", "Bank Adjustments", xl_section)
            for starting_col in [5, 9]:
                xl_worksheet.write(1, starting_col, "Date", xl_header)
                xl_worksheet.write(1, starting_col + 1, "Description", xl_header)
                xl_worksheet.write(1, starting_col + 2, "Amount", xl_header)

                if starting_col == 5:
                    adjustments = account.book_adjustments
                elif starting_col == 9:
                    adjustments = account.bank_adjustments

                xl_row = 2
                for adjustment in adjustments:
                    xl_worksheet.write(xl_row, starting_col, adjustment.date)
                    xl_worksheet.write(xl_row, starting_col + 1, adjustment.description)
                    xl_worksheet.write(xl_row, starting_col + 2, round(adjustment.amount, 2))
                    xl_row += 1

            tab.xl_worksheet.write_formula(account.balance_adj_cell, "='%s'!C2" % sheet_name, amount_format)

            xl_col = 0
            for width in widths:
                col_format = None
                if xl_col in [7, 11]:
                    col_format = amount_format
                elif xl_col in [0, 5, 9]:
                    col_format = date_format
                xl_worksheet.set_column(xl_col, xl_col, width, col_format)
                xl_col += 1
    return(None)


def link_tabs(tabs):
    asset_tabs = []
    for tab in tabs:
        tab_type = get_tab_type(tab)
        if tab_type == "liability":
            cc_tab = tab
        elif tab_type == "asset":
            asset_tabs.append(tab)

    checking_total_formula = "=0"
    checking_adj_formula = "=0"
    savings_total_formula = "=0"
    savings_adj_formula = "=0"
    for tab in asset_tabs:
        tab.xl_worksheet.write_formula(tab.cc_total_cell, "='%s'!%s" % (cc_tab.name, cc_tab.cc_total_cell))
        tab.xl_worksheet.write_formula(tab.cc_total_adj_cell, "='%s'!%s" % (cc_tab.name, cc_tab.cc_total_adj_cell))
        for account in tab.checking:
            checking_total_formula += "+'%s'!%s" % (tab.name, account.balance_cell)
            checking_adj_formula += "+'%s'!%s" % (tab.name, account.balance_adj_cell)
        for account in tab.savings:
            savings_total_formula += "+'%s'!%s" % (tab.name, account.balance_cell)
            savings_adj_formula += "+'%s'!%s" % (tab.name, account.balance_adj_cell)

    cc_tab.xl_worksheet.write_formula(cc_tab.checking_total_cell, checking_total_formula)
    cc_tab.xl_worksheet.write_formula(cc_tab.checking_total_adj_cell, checking_adj_formula)
    cc_tab.xl_worksheet.write_formula(cc_tab.savings_total_cell, savings_total_formula)
    cc_tab.xl_worksheet.write_formula(cc_tab.savings_total_adj_cell, savings_adj_formula)
    return(None)


def write_ledger(accounts, xl_workbook):
    tabs = get_tabs(accounts)

    #add ledger sheets
    for tab in tabs:
        tab.xl_worksheet = add_ledger_tab(xl_workbook, tab)

    #add reconciliations
    for tab in tabs:
        if tab.name != "Credit Cards":
            add_reconciliations(xl_workbook, tab)
        else:
            cc_tab = tab
    add_reconciliations(xl_workbook, cc_tab)

    link_tabs(tabs)

    return(tabs)


def archive_ledger():
    source_path = ReadLedger.get_ledger_path()
    if not os.path.isfile(source_path):
        source_path = ReadLedger.get_ledger_path(prior = True)
        if not os.path.isfile(source_path):
            return(False)
    destination_name = os.path.split(source_path)[1]
    destination_name = os.path.splitext(destination_name)[0] + "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".xlsx"
    destination_path = os.path.join(Config.get_path("ledger_archive_dir"), destination_name)
    moved = False
    while not moved:
        try:
            shutil.move(source_path, destination_path)
            moved = True
        except PermissionError:
            if not Io.yes_no("Failed to archive existing ledger. It might be open. Try again?"):
                Io.error("Aborting.")



def main():
    xl_workbook = xlsxwriter.Workbook(ReadLedger.get_ledger_path())
    ledger_account_collection = get_accounts()
    archive_ledger()
    ledger_tabs = write_ledger(ledger_account_collection, xl_workbook)
    Excel.save_workbook(xl_workbook, ReadLedger.get_ledger_path())


if __name__ == "__main__":
    main()
