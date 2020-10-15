import zm_fidelity as Fidelity
import zm_physical as Physical
import zk_beta
import zr_db

def main():
    all_positions = []

    fidelity_account = Fidelity.get_account()
    physical_commodities = Physical.get_positions()

    for position in fidelity_account.positions:
        all_positions.append(position)

    for position in physical_commodities:
        all_positions.append(position)

    zr_db.sync_sqlite(all_positions)

    zk_beta.load_portfolio_betas(all_positions)

    zk_beta.print_xlsx(all_positions)

    exit(0)

if __name__ == "__main__":
    main()
