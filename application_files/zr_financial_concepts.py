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
