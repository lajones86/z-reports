import zj_investments as Investments
import zk_beta as Beta
import zr_financial_instruments as Instruments
import zr_db as Db

def main(investments = None):
    all_positions = []

    if investments == None:
        investments = Investments.get_investments()
    else:
        investments = investments

    #do brokerage positions
    brokerage_positions = []

    for brokerage_account in investments.brokerage_accounts:
        for new_position in brokerage_account.stock_positions:
            added_quantity = False
            for existing_position in brokerage_positions:
                if existing_position.symbol == new_position.symbol:
                    existing_position.add_quantity(new_position.quantity)
                    added_quantity = True
                    break
            if not added_quantity:
                brokerage_positions.append(Instruments.StockPosition(new_position.symbol, new_position.quantity, last_price = new_position.last_price))

    Db.sync_history(brokerage_positions, "stock_shares")
    Beta.load_portfolio_betas(brokerage_positions)

    for position in brokerage_positions:
        all_positions.append(position)
    Beta.print_xlsx(all_positions, "-Brokers")

    #get commodities rolled in
    if investments.crypto != None:
        for c in investments.crypto:
            Db.sync_history([c.emulated_stock], "crypto")
            Beta.load_portfolio_betas([c.emulated_stock])
            all_positions.append(c.emulated_stock)

    metals = []
    if investments.metals != None:
        Db.sync_history(investments.metals, "metals")
        for metal in investments.metals:
            metals.append(metal.emulated_stock)
        Beta.load_portfolio_betas(metals)
        for metal in metals:
            all_positions.append(metal)

    Beta.print_xlsx(all_positions, "-Brokers-and-Commodities")

    #include treasury bonds
    if investments.treasuries != None:
        t = investments.treasuries
        all_positions.append(Instruments.StockPosition(t.symbol, t.quantity, emulated = True, risk_free = True, last_price = t.last_price, description = t.description))
        Beta.print_xlsx(all_positions, "-All")

    exit(0)

if __name__ == "__main__":
    main()
