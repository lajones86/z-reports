import string

#special thanks to keith jones for this function
def get_letter(index):
    index += 1
    result = ""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    index_temp = index - 1
    while index_temp >= 26:
            result = alphabet[(index_temp%26)] + result
            index_temp /= 26
            index_temp = math.floor(index_temp)
            index_temp -= 1
    result = alphabet[index_temp] + result
    return(result)


class BetaSheet:
    def __init__(self, sheetname, header_dict, symbol_dict):
        self.sheetname = sheetname
        self.header_dict = header_dict
        self.symbol_dict = symbol_dict
