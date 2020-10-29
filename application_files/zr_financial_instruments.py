import re

import zr_financial_concepts as Concepts
import zr_config as Config
import zr_security_info

from yahoo_fin import stock_info as y_stock_info

class StockPosition:
    def __init__(self, symbol, quantity, emulated = None, risk_free = None, last_price = None, description = None):

        if emulated == None:
            emulated = False

        self.manual_average_beta = None

        if risk_free == None:
            risk_free = False
        elif risk_free == True:
            self.manual_average_beta = 0

        self.emulated = emulated
        self.risk_free = risk_free
        self.description = description

        self.symbol = None
        self.set_symbol(symbol)

        self.quantity = float(quantity)
        try:
            if last_price == None:
                self.last_price = float(y_stock_info.get_live_price(self.symbol))
            else:
                self.last_price = float(last_price)
        except:
            print(symbol, self.symbol)
            exit()

        self.calc_equity()
        self.industry = str(zr_security_info.get_industry(self.symbol)).title()
        self.purpose = str(zr_security_info.get_purpose(self.symbol)).title()

        self.betas = []

    #convert symbols to be compatible with yahoo finance
    def set_symbol(self, symbol):
        if Config.get_yahoo("use_yahoo") == "True":
            if symbol == "BRKB" or symbol == "BRK.B":
                self.symbol = "BRK-B"

        elif Config.get_yahoo("use_yahoo") == "False":
            if symbol == "BRKB" or symbol == "BRK-B":
                self.symbol = "BRK.B"

        if self.symbol == None:
            self.symbol = symbol

    def add_quantity(self, increase):
        self.quantity += increase
        self.calc_equity()

    def modify_price(self, change):
        self.last_price += float(change)
        self.calc_equity()

    def calc_equity(self):
        self.equity = self.quantity * self.last_price

    def add_beta(self, months, beta):
        for b in self.betas:
            if b.months == months:
                return(1)
        self.betas.append(Concepts.Beta(months, beta))


class TrackingCommodity:
    def __init__(self, symbol, description, quantity, multiplier):
        self.symbol = symbol
        self.description = description
        self.quantity = quantity
        self.multiplier = multiplier

        self.emulated_stock = StockPosition(symbol, (quantity * multiplier), description = description, emulated = True)


class BrokerageAccount:
    def __init__(self, name):
        self.name = name
        self.stock_positions = []
        self.option_positions = []
        self.cash_position = 0

    def add_position_by_data(self, symbol, quantity):
        updated_existing = False
        for position in self.stock_positions:
            if position.symbol == symbol:
                position.add_quantity(quantity)
                updated_existing = True
                break
        if not updated_existing:
            self.stock_positions.append(StockPosition(symbol, quantity))


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


class CryptoCurrency():
    def __init__(self, currency, addresses):
        self.currency = currency
        self.addresses = addresses
        self.balance = float(0)

        if Config.get_yahoo("use_yahoo") == "True":
            stock_symbol = self.currency.upper() + "-USD"

        self.emulated_stock = StockPosition(stock_symbol, self.balance, emulated = True)

    def add_balance(self, change):
        change = float(change)
        self.balance += change
        self.emulated_stock.add_quantity(change)
