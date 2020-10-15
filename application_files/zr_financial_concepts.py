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
