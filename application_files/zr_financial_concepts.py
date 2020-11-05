from datetime import datetime

class HistoricalPosition:
    def __init__(self, date, close, adj_close):
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.close = close
        self.adj_close = adj_close

class Beta:
    def __init__(self, months, beta):
        self.months = months
        self.beta = beta

class Investments:
    def __init__(self):
        self.brokerage_accounts = []
        self.crypto = None
        self.treasuries = None
        self.metals = None


class SummaryCollection():
    def __init__(self, description, summaries_list = None):
        self.description = description
        if summaries_list == None:
            self.summaries_list = []
        else:
            self.summaries_list = summaries_list

    def add_summary(self, summary):
        self.summaries_list.append(summary)


class AccountSummary():
    def __init__(self, name, balance):
        self.name = name
        self.balance = float(balance)


class LedgerEntry():
    def __init__(self, date, description, amount):
        self.date = date
        self.description = description
        self.amount = float(amount)


class LedgerAccount():
    def __init__(self, name, institution, account_type):
        self.name = name
        self.institution = institution
        self.account_type = account_type
        self.book_balance = float(0)
        
        self.balance_cell = None
        self.balance_adj_cell = None
        self.amount_col = None

        self.rec_date = datetime.now().date()
        self.bank_balance = float(0)

        self.book_entries = []
        self.book_adjustments = []
        self.bank_adjustments = []

class LedgerAccountCollection():
    def __init__(self, checking_accounts = None, savings_accounts = None, credit_cards = None):
        self.checking_accounts = checking_accounts
        self.savings_accounts = savings_accounts
        self.credit_cards = credit_cards
