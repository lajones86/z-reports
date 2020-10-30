import zh_portfolio_beta as PortfolioBeta
import zj_investments as Investments


def main():
    investments = Investments.main()
    PortfolioBeta.main(investments = investments)

if __name__ == "__main__":
    main()
