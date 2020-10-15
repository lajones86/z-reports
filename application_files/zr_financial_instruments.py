import re

import zr_financial_concepts as Concepts
import zr_security_info

from yahoo_fin import stock_info as y_stock_info

class StockPosition:
    def __init__(self, symbol, quantity):

        symbol = self.symbol_subst(symbol)

        self.symbol = symbol
        self.quantity = float(quantity)
        self.last_price = float(y_stock_info.get_live_price(symbol))
        self.calc_equity()
        self.industry = str(zr_security_info.get_industry(self.symbol)).title()
        self.purpose = str(zr_security_info.get_purpose(self.symbol)).title()

        self.betas = []

    #convert symbols to be compatible with yahoo finance
    def symbol_subst(self, symbol):
        if symbol == "BRKB":
            symbol = "BRK-B"
        return(symbol)

    def add_quantity(self, increase):
        self.quantity += increase
        self.calc_equity()

    def calc_equity(self):
        self.equity = self.quantity * self.last_price

    def add_beta(self, months, beta):
        for b in self.betas:
            if b.months == months:
                return(1)
        self.betas.append(Concepts.Beta(months, beta))


class BrokerageAccount:
    def __init__(self, name):
        self.name = name
        self.positions = []
        self.listing_date = None
        self.cash_position = None

    def add_position_by_data(self, symbol, quantity):
        updated_existing = False
        for position in self.positions:
            if position.symbol == symbol:
                position.add_quantity(quantity)
                updated_existing = True
                break
        if not updated_existing:
            self.positions.append(StockPosition(symbol, quantity))


class TreasuryBond():
    def __init__(self, site_string):
        re_cell = re.compile("\<td.*?\<\/td\>")
        re_html_tag = re.compile("\<.*?\>")
        cells = []
        for cell in re_cell.findall(site_string):
            for html_tag in re_html_tag.findall(cell):
                cell = cell.replace(html_tag, "")
            cells.append(cell)

        self.serial = cells[0]
        self.series = cells[1]
        self.denomination = float(cells[2].strip("$"))
        self.issue_date = cells[3]
        self.next_accrual = cells[4]
        self.maturity_date = cells[5]
        self.issue_price = float(cells[6].strip("$"))
        self.interest = float(cells[7].strip("$"))
        self.rate = float(cells[8].strip("%"))
        self.value = float(cells[9].strip("$"))
