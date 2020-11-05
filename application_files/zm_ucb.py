import zt_extractor as Extractor
import zt_html as Html
import zr_financial_concepts as Concepts
import zr_io as Io

from lxml import html as lxml_html

def get_balance():
    ucb_file = Extractor.get_extractor_file("ucb")

    if not ucb_file:
        return(None)

    ucb_html = lxml_html.parse(ucb_file)

    wanted_dl = Html.get_by_xpath(ucb_html,
            ".//dt[text()='Principal balance']/..",
            min_results = 1, max_results = 1, description = "Balance wrapper")[0]

    balance = Html.get_by_xpath(wanted_dl,
            ".//dd[contains(text(), '$')]",
            min_results = 1, max_results = 1, description = "Balance element")[0]

    balance = str(balance.text).replace(",", "").replace("$", "").strip()

    return(balance)


if __name__ == "__main__":
    print(get_balance())
