import zm_ucb as Ucb
import zr_financial_concepts as Concepts

def get_liabilities():
    liabilities = Concepts.SummaryCollection("Liabilities")
    liabilities.add_summary(Concepts.AccountSummary("UCB Mortgage", Ucb.get_balance()))
    return(liabilities)


if __name__ == "__main__":
    liabs = get_liabilities()
    print(liabs.description)
    for summary in liabs.summaries_list:
        print(summary.name, summary.balance)
