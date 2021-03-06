import sqlite3
import numpy
import xlsxwriter
import os
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

import zr_excel as Excel
import zr_financial_instruments as Instruments
import zr_config as Config
import zr_io as Io
import zr_db as Db
import zr_csv as Csv

def get_manual_average_beta(position):

    if position.risk_free == False:

        columns = [
                Csv.CsvColumn(name = "Symbol", is_row_identifier = True),
                Csv.CsvColumn(name = "Beta", data_type = "float")
                ]
        default_rows = [
                [position.symbol, "-9001"]
                ]

        manual_beta_csv = Csv.CsvFile(Config.get_beta("manual_averages"), default_column_list = columns, default_data_rows = default_rows, read_only = True)

        manual_beta = manual_beta_csv.find_by_id(position.symbol)["Beta"]

        if manual_beta == -9001:
            manual_beta = None
        else:
            try:
                manual_beta = float(manual_beta)
            except:
                manual_beta = None

    else:
        manual_beta = float(0)

    position.manual_average_beta = manual_beta

    return(0)


def get_benchmark():
    if Config.get_yahoo("use_yahoo") == "False":
        return(Config.get_beta("benchmark"))
    elif Config.get_yahoo("use_yahoo") == "True":
        return(Config.get_yahoo("benchmark"))

def calc_single_security_beta(symbol, months):
    benchmark = get_benchmark()
    print("Calculating %s month beta for %s against %s" % (str(months), symbol, benchmark))
    if not verify_date_sync(symbol, months):
        Io.error("Date range mismatch for %s & %s" % (symbol, benchmark))
    benchmark_returns = get_security_returns_list(benchmark, months)
    symbol_returns = get_security_returns_list(symbol, months)
    covar = numpy.cov(benchmark_returns, symbol_returns, ddof=1)[0][1]
    benchmark_var = numpy.var(benchmark_returns, ddof=1)
    beta = covar / benchmark_var
### begin debugging toggles ###

#    print("%s months" % months)
#    print(len(benchmark_returns))
#    print(benchmark_returns)
#    print(len(symbol_returns))
#    print(symbol_returns)
#    print(covar)
#    print(benchmark_var)
#    print(beta)

#    if (input("Continue? ").lower()) == "n":
#        exit(0)

### end debugging toggles ###

    return(beta)


#verify the dates retrieved for symbol match those retrieved for benchmark
def verify_date_sync(symbol, months):
    #build db connection
    db_conn = sqlite3.connect(Config.get_path("history_db"))
    db_conn.isolation_level = None
    cursor = db_conn.cursor()

    pull_months = months + 1
    benchmark_dates = []
    symbol_dates = []
    for record in cursor.execute("SELECT date FROM '%s' where adj_close != -9001 ORDER BY date DESC LIMIT %s;" % (symbol, pull_months)).fetchall()[::-1]:
        symbol_dates.append(record[0])
    for record in cursor.execute("SELECT date FROM '%s' where adj_close != -9001 ORDER BY date DESC LIMIT %s;" % (get_benchmark(), pull_months)).fetchall()[::-1]:
        benchmark_dates.append(record[0])
    db_conn.close()
    if benchmark_dates == symbol_dates:
        return(True)
    return(False)


def get_security_returns_list(symbol, months):
    return_list = []
    #build db connection
    db_conn = sqlite3.connect(Config.get_path("history_db"))
    db_conn.isolation_level = None
    cursor = db_conn.cursor()
    #pull one more month than we're calculating return for because we
    #need prior month's closing to calculate return for first month
    pull_months = months + 1
    last = None
    for record in cursor.execute("SELECT %s FROM '%s' where adj_close != -9001 ORDER BY date DESC LIMIT %s;" % ("adj_close", symbol, pull_months)).fetchall()[::-1]:
        if last:
            return_list.append(((record[0] - last) / last) * 100)
        last = record[0]
    db_conn.close()
    return(return_list)


def get_symbol_max(symbol):
    db_conn = sqlite3.connect(Config.get_path("history_db"))
    db_conn.isolation_level = None
    cursor = db_conn.cursor()

    symbol_dates = []
    for record in (cursor.execute("SELECT * FROM '%s' where adj_close != -9001;" % (str(symbol))).fetchall()):
        symbol_dates.append(record[0])
    db_conn.close()

    current_date = datetime.now()
    if current_date.day == 1:
        current_date = current_date - relativedelta(months = 1)
    last_date = current_date.replace(day = 1).strftime("%Y-%m-%d")

    if symbol_dates[-1] != last_date:
        Io.error("Last date for %s should be %s but is %s" % (symbol, last_date, symbol_dates[-1]))

    usable_dates = []

    for date in symbol_dates[::-1]:
        if date == last_date:
            usable_dates.append(date)
            last_date = (datetime.strptime(last_date, "%Y-%m-%d") - relativedelta(months = 1)).strftime("%Y-%m-%d")
        else:
            break
    
    if len(usable_dates) == 0 or len(usable_dates) == 1:
        Io.error("No usable date range for %s" % symbol)

    return(len(usable_dates))


def load_portfolio_betas(positions):
    sub_year_interval_months = Config.get_beta("subyear_interval")
    max_beta_years = Config.get_beta("max_years")
    #build db connection
    db_conn = sqlite3.connect(Config.get_path("history_db"))
    db_conn.isolation_level = None
    cursor = db_conn.cursor()

    #make sure we've got enough benchmark records to do the full desired span
    benchmark_max = max_beta_years * 12
    benchmark_count = (cursor.execute("SELECT COUNT(*) FROM '%s' where adj_close != -9001;" % (str(get_benchmark()))).fetchall()[0][0])
    #adjusting counts by 1 here to make sure we can go back a month before
    #the start of the beta period to get full return information
    if benchmark_count < (benchmark_max + 1):
        benchmark_max = (benchmark_count - 1)
        print("Benchmark records insufficient for desired beta span. Setting maximum months to %s" % str(benchmark_max))

    for position in positions:
        print("Processing %s" % str(position.symbol))
        get_manual_average_beta(position)
        if not position.risk_free == True:
            #make sure we've got enough records for the symbol to match the benchmark/desired span
            symbol_max = benchmark_max
            symbol_count = (cursor.execute("SELECT COUNT(*) FROM '%s' where adj_close != -9001;" % (str(position.symbol))).fetchall()[0][0])
            #adjusting counts by 1 as when checking benchmark
            if symbol_count < (symbol_max + 1):
                symbol_max = (symbol_count - 1)
                print("Symbol records insufficient for desired beta span. Setting maximum months to %s for symbol." % symbol_max)

            true_symbol_max = get_symbol_max(position.symbol)
            if true_symbol_max < (symbol_max + 1):
                symbol_max = (true_symbol_max - 1)
                print("Symbol records insufficient for desired beta span. Setting maximum months to %s for symbol." % symbol_max)

            if symbol_max >= 2:

                #check here for our sub-year breakdown
                #we're assuming max_beta_years has been set to at least one
                #if not, you're just trying to break things
                for months in range(1, 12):
                    if months > symbol_max:
                        break
                    else:
                        if sub_year_interval_months:
                            if not months % sub_year_interval_months:
                                position.add_beta(months, calc_single_security_beta(str(position.symbol), months))

                #switch to breakdown by year
                for year in range(Config.get_beta("min_years"), max_beta_years + 1):
                    months = year * 12
                    if months > symbol_max:
                        break
                    else:
                        position.add_beta(months, calc_single_security_beta(str(position.symbol), months))

                #make sure to hit max-length beta if there weren't enough records
                #to go as long as we wanted on this position
                max_done = False
                #if we have less than a year of data for the symbol
                #we check the sub-year interval to make sure it's been done
                if symbol_max < 12:
                    if sub_year_interval_months:
                        if not symbol_max % sub_year_interval_months:
                            max_done = True

                #if it's at least a year, we check to see if it got
                #hit during the year-by-year breakdown
                else:
                    if not symbol_max % 12:
                        max_done = True
                if not max_done:
                    position.add_beta(symbol_max, calc_single_security_beta(str(position.symbol), symbol_max))

            else:
                print("Insufficient history to calculate beta.")
            

    db_conn.close()
    return(0)

def print_beta_sheet(positions, xl_workbook, sheetname, master_sheet):
    benchmark = get_benchmark()

    #just end this function if the benchmark is the only thing in it
    if len(positions) == 1 and positions[0].symbol == benchmark:
        return(None)

    #get a list of all spans we'll be displaying
    spans = []
    if sheetname == "Beta - Master":
        for position in positions:
            for beta in position.betas:
                if not beta.months in spans:
                    spans.append(beta.months)
    spans.sort()
    spans.reverse()

    #build header listing
    headers = []
    initial_headers = ["Symbol", "Quantity", "Last Price", "Equity"]

    for header in initial_headers:
        if not header in headers:
            headers.append(header)

    for span in spans:
        if not span in headers:
            headers.append(span)

    for header in ["Average Beta", "Weight", "Weighted Beta"]:
        headers.append(header)

    #add the worksheet, row, and col variables
    xl_worksheet = xl_workbook.add_worksheet(sheetname)
    xl_row = 0
    xl_col = 0

    #excel formatting
    xl_header = xl_workbook.add_format({"bold" : True, "underline" : True, "center_across" : True})
    xl_symbol = xl_workbook.add_format({"bold" : True, "italic" : True})
    xl_normal = xl_workbook.add_format({})
    xl_custom_beta = xl_workbook.add_format({"bg_color" : "cyan"})
    xl_changeme = xl_workbook.add_format({"bg_color" : "orange"})
    xl_changeme_too = xl_workbook.add_format({"bg_color" : "yellow"})

    #write headers and get range of beta columns
    #write header dict for BetaSheet object
    header_dict = {}
    header_dict_col = 0
    beta_start = None
    beta_end = None
    for header in headers:
        header_dict[header] = Excel.get_letter(header_dict_col)
        header_dict_col += 1
        output_cell = str(header)
        if output_cell.isnumeric():
            output_cell += " Month Beta (Monthly)"
            if not beta_start:
                beta_start = Excel.get_letter(headers.index(header))
        else:
            if beta_start and not beta_end:
                beta_end = Excel.get_letter(headers.index(header) - 1)
        xl_worksheet.write(xl_row, xl_col, output_cell.replace(" Month", "M").replace(" (Monthly)", ""), xl_header)

        xl_worksheet.set_column(xl_col, xl_col, len(output_cell.replace(" Month", "M").replace(" (Monthly)", "")) * 1.2)

        xl_col += 1

    totals_row = len(positions) + 2

    #set length of symbols row based on longest symbol
    longest_symbol = 6
    for position in positions:
        element_to_check = position.symbol
        if position.emulated == True and position.description != None:
            element_to_check = position.description
        if len(element_to_check) > longest_symbol:
            longest_symbol = len(element_to_check)
    xl_worksheet.set_column(0, 0, longest_symbol * 1.2)

    #write positions to sheet and do math
    #write symbol dictionary for BetaSheet object
    symbol_dict = {"Totals" : totals_row + 1}
    for position in positions:
        xl_row += 1
        symbol_dict[position.symbol] = xl_row + 1

        if position.emulated == True and position.description != None:
            current_symbol = position.description
        else:
            current_symbol = position.symbol

        xl_worksheet.write(xl_row, headers.index("Symbol"), current_symbol, xl_symbol)

        #calculate equity
        xl_worksheet.write_formula(
            xl_row, headers.index("Equity"), "=%s%s*%s%s" %
                (
                    Excel.get_letter(headers.index("Quantity")), str(xl_row + 1),
                    Excel.get_letter(headers.index("Last Price")), str(xl_row + 1)
                )
            )

        #write quantity and
        #last price and
        #fill out beta cells and
        #calculate average beta if this is the master sheet
        #otherwise pull relevant data from the master sheet
        if sheetname == "Beta - Master":
            for b in position.betas:
                xl_worksheet.write(xl_row, headers.index(b.months), b.beta)

            xl_worksheet.write(xl_row, headers.index("Quantity"), position.quantity, xl_changeme)

            xl_worksheet.write(xl_row, headers.index("Last Price"), position.last_price, xl_changeme)

            if position.manual_average_beta == None:
                xl_worksheet.write_formula(
                    xl_row, headers.index("Average Beta"), "=AVERAGE(%s%s:%s%s)" %
                        (
                            beta_start, str(xl_row + 1), beta_end, str(xl_row + 1)
                        ),
                        xl_changeme
                )

            else:
                xl_worksheet.write(xl_row, headers.index("Average Beta"), position.manual_average_beta, xl_custom_beta)

        else:
            xl_worksheet.write_formula(
                xl_row, headers.index("Quantity"), "='%s'!%s%s" %
                (
                    master_sheet.sheetname,
                    master_sheet.header_dict["Quantity"],
                    master_sheet.symbol_dict[str(position.symbol)]
                ),
                xl_changeme_too
            )

            xl_worksheet.write_formula(
                xl_row, headers.index("Last Price"), "='%s'!%s%s" %
                (
                    master_sheet.sheetname,
                    master_sheet.header_dict["Last Price"],
                    master_sheet.symbol_dict[str(position.symbol)]
                ),
                xl_changeme_too
            )

            xl_worksheet.write_formula(
                xl_row, headers.index("Average Beta"), "='%s'!%s%s" %
                (
                    master_sheet.sheetname,
                    master_sheet.header_dict["Average Beta"],
                    master_sheet.symbol_dict[str(position.symbol)]
                )
            )


        #calculate weight
        xl_worksheet.write_formula(
            xl_row, headers.index("Weight"), "=%s%s/$%s$%s" %
                (
                    Excel.get_letter(headers.index("Equity")), str(xl_row + 1),
                    Excel.get_letter(headers.index("Equity")), str(totals_row + 1)
                )
        )

        #calculate weighted beta
        xl_worksheet.write_formula(
            xl_row, headers.index("Weighted Beta"), "=%s%s*%s%s" %
            (
                Excel.get_letter(headers.index("Weight")), str(xl_row + 1),
                Excel.get_letter(headers.index("Average Beta")), str(xl_row + 1)
            )
        )


    #write totals row
    xl_worksheet.write(totals_row, headers.index("Symbol"), "Totals", xl_symbol)

    #total equity
    xl_worksheet.write_formula(
        totals_row, headers.index("Equity"), "=SUM(%s1:%s%s)" %
        (
            Excel.get_letter(headers.index("Equity")),
            Excel.get_letter(headers.index("Equity")), totals_row
        )
    )

    #total beta
    xl_worksheet.write_formula(
        totals_row, headers.index("Weighted Beta"), "=SUM(%s1:%s%s)" %
        (
            Excel.get_letter(headers.index("Weighted Beta")),
            Excel.get_letter(headers.index("Weighted Beta")), totals_row
        )
    )

    return(Excel.BetaSheet(sheetname, header_dict, symbol_dict))


def print_overview(xl_workbook, sheetname, beta_sheets):
    categories = []
    for sheet in beta_sheets:
        if not " - " in sheet.sheetname:
            Io("Could not parse sheet name %s" % str(sheet.sheetname))
        category = re.split("-", str(sheet.sheetname))[0]
        category = category.replace("Beta", "").strip()
        if category:
            if not category in categories:
                categories.append(category)

    xl_worksheet = xl_workbook.add_worksheet(sheetname)

    #formatting
    xl_header = xl_workbook.add_format({"bold" : True, "underline" : True, "center_across" : True})
    xl_symbol = xl_workbook.add_format({"bold" : True, "italic" : True})

    starting_col = 0
    for category in categories:
        xl_row = 0
        xl_col = starting_col

        #write category headers
        headers = [category, "Equity", "Beta", "Weight", "Weighted Beta"]
        for header in headers:
            xl_worksheet.write(xl_row, xl_col, header, xl_header)
            if header == category:
                pass
            elif header == "Equity":
                xl_worksheet.set_column(xl_col, xl_col, 12)
            else:
                col_width_base = len(header)
                if col_width_base < 6:
                    col_width_base = 6
                xl_worksheet.set_column(xl_col, xl_col, col_width_base * 1.2)

            xl_col += 1

        xl_row += 1
        xl_col = starting_col

        #write info
        #and set category column width
        longest_category = len(category)
        category_sheets = []
        for sheet in beta_sheets:
            if category in sheet.sheetname:
                category_sheets.append(sheet)
                cat_item_name = (sheet.sheetname).replace("%s Beta - " % category, "")
                if len(cat_item_name) > longest_category:                    
                    longest_category = len(cat_item_name)

        xl_worksheet.set_column(xl_col, xl_col, longest_category * 1.2)

        totals_row = len(category_sheets) + 2

        for sheet in category_sheets:
            name = re.split("-", str(sheet.sheetname))[1].replace("Beta", "").strip()
            xl_worksheet.write(xl_row, headers.index(category) + starting_col, name, xl_symbol)

            #get equity from breakdown sheet
            xl_worksheet.write_formula(
                xl_row, headers.index("Equity") + starting_col, "='%s'!%s%s" %
                (
                    sheet.sheetname,
                    sheet.header_dict["Equity"],
                    sheet.symbol_dict["Totals"]
                )
            )

            #get weighted beta from breakdown sheet
            xl_worksheet.write_formula(
                xl_row, headers.index("Beta") + starting_col, "='%s'!%s%s" %
                (
                    sheet.sheetname,
                    sheet.header_dict["Weighted Beta"],
                    sheet.symbol_dict["Totals"]
                )
            )

            #get the weight for the breakdown element
            xl_worksheet.write_formula(
                xl_row, headers.index("Weight") + starting_col, "=%s%s/$%s$%s" %
                (
                    Excel.get_letter(headers.index("Equity") + starting_col), xl_row + 1,
                    Excel.get_letter(headers.index("Equity") + starting_col), totals_row + 1
                )
            )

            #do the weighted beta calculation
            xl_worksheet.write_formula(
                xl_row, headers.index("Weighted Beta") + starting_col, "=%s%s*%s%s" %
                (
                    Excel.get_letter(headers.index("Weight") + starting_col), xl_row + 1,
                    Excel.get_letter(headers.index("Beta") + starting_col), xl_row + 1
                )
            )

            xl_row += 1

        #write totals row
        xl_worksheet.write(totals_row, headers.index(category) + starting_col, "Totals", xl_symbol)

        #sum equity
        xl_worksheet.write_formula(
            totals_row, headers.index("Equity") + starting_col, "=SUM(%s1:%s%s" %
            (
                Excel.get_letter(headers.index("Equity") + starting_col),
                Excel.get_letter(headers.index("Equity") + starting_col), str(totals_row)
            )
        )

        #sum weighted beta
        xl_worksheet.write_formula(
            totals_row, headers.index("Weighted Beta") + starting_col, "=SUM(%s1:%s%s" %
            (
                Excel.get_letter(headers.index("Weighted Beta") + starting_col),
                Excel.get_letter(headers.index("Weighted Beta") + starting_col), str(totals_row)
            )
        )


        starting_col += len(headers) + 1


def print_xlsx(positions, filename_suffix = None):
    filename = "Beta"
    if filename_suffix:
        filename += filename_suffix
    filename += ".xlsx"
    xl_wb_path = os.path.join(Config.get_path("reports_dir"), filename)

    xl_workbook = xlsxwriter.Workbook(xl_wb_path)
    xl_dir = os.path.split(xl_wb_path)[0]
    if not os.path.isdir(xl_dir):
        os.makedirs(xl_dir)

    industries = []
    purposes = []

    for position in positions:
        industry = str(position.industry).strip().title()
        if not industry in industries:
            industries.append(industry)
        purpose = str(position.purpose).strip().title()
        if not purpose in purposes:
            purposes.append(purpose)

    industries.sort()
    purposes.sort()
    beta_sheets = [print_beta_sheet(positions, xl_workbook, "Beta - Master", None)]


    #track our breakdown sheets and their total beta cells
    #for referencing in the overview sheet
    breakdown_beta_locations = []

    #we have to designate disctinct numerical identifiers for each list
    #in case the lists are the same
    #tends to happen with the default bond script
    categories = [[industries, 0], [purposes, 1]]
    for category in categories:
        for entry in category[0]:
            entry_positions = []
            for position in positions:
                if category[1] == 0:
                    criteria = position.industry
                    sheet_name_base = "Industry"
                elif category[1] == 1:
                    criteria = position.purpose
                    sheet_name_base = "Purpose"

                sheet_name = sheet_name_base + " Beta - %s" % entry

                if criteria.title() == entry.title():
                    entry_positions.append(position)

            
            new_beta_sheet = print_beta_sheet(entry_positions, xl_workbook, sheet_name, beta_sheets[0])
            if new_beta_sheet:
                beta_sheets.append(new_beta_sheet)

    print_overview(xl_workbook, "Beta - Overview", beta_sheets)

    Excel.save_workbook(xl_workbook, xl_wb_path)


def symbol_lookup():
    while True:
        if not Io.yes_no("Run Beta lookup?"):
            return(0)
        symbol = input("Enter symbol: ").upper()
        position = Instruments.StockPosition(symbol, 0, quickrun = True)
        if Db.sync_history([position], "stock_shares") == 0:
            load_portfolio_betas([position])
            beta_sum = 0.00
            if len(position.betas) != 0:
                for b in position.betas[::-1]:
                    print("%s Month Beta (Monthly): %s" % (str(b.months), str(b.beta)))
                    beta_sum += b.beta
                print("Average Monthly Beta: %s" % (str(beta_sum / len(position.betas))))
            else:
                print("Not enough history to calculate beta.")


if __name__ == "__main__":
    symbol_lookup()
