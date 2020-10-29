import zr_financial_concepts as Concepts
import zm_fidelity as Fidelity
import zm_treasuries as Treasuries
import zm_crypto as Crypto

import zr_io as Io

def get_brokerages():
    fidelity_account = Fidelity.get_account()
    return([fidelity_account])

def get_investments():
    investments = Concepts.Investments()
    investments.brokerage_accounts = get_brokerages()
    investments.treasuries = Treasuries.get_emulated_stock()
    investments.crypto = Crypto.main()

    return(investments)

def print_investments(investments):
    Io.error("Writing investment output not implemented.")


if __name__ == "__main__":
    investments = get_investments()
    print_investments(investments)
