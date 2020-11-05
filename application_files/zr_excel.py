import zr_io

#special thanks to keith jones for this function
def get_letter(index):
    index += 1
    result = ""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    index_temp = index - 1
    while index_temp >= 26:
            result = alphabet[(index_temp%26)] + result
            index_temp /= 26
            index_temp = math.floor(index_temp)
            index_temp -= 1
    result = alphabet[index_temp] + result
    return(result)


def save_workbook(xl_workbook, xl_wb_path):
    #close and write the workbook
    while True:
        try:
            xl_workbook.close()
            print("\nWorkbook written to %s" % xl_wb_path)
            break
        except:
            if not zr_io.yes_no("Couldn't write Excel file %s. Close it if it's open. Try writing again?" % xl_wb_path):
                break
    return(0)



class BetaSheet:
    def __init__(self, sheetname, header_dict, symbol_dict):
        self.sheetname = sheetname
        self.header_dict = header_dict
        self.symbol_dict = symbol_dict


class LedgerTab():
    def __init__(self, name, accounts):
        self.name = name
        self.checking = []
        self.savings = []
        self.credit_cards = []
        self.xl_worksheet = None
        self.summary_start_col = None
        self.cc_total_cell = None
        self.cc_total_adj_cell = None
        self.checking_total_cell = None
        self.checking_total_adj_cell = None
        self.savings_total_cell = None
        self.savings_total_adj_cell = None

        for account in accounts:
            if account.account_type == "Checking":
                self.checking.append(account)
            elif account.account_type == "Savings":
                self.savings.append(account)
            elif account.account_type == "Credit Card":
                self.credit_cards.append(account)
            else:
                Io.error("Unknown account type %s" % account.account_type)


class InvestmentsTab:
    def __init__(self):
        self.broker_total_cell = None
        self.crypto_total_cell = None
        self.metal_total_cell = None
        self.bond_total_cell = None
