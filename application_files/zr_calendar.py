from datetime import datetime
from dateutil.relativedelta import relativedelta

import sys

#butcher's algorithm
def calc_easter(year):
    year = int(year)
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = ("%02d" % int(f // 31))
    day = ("%02d" % int(f % 31 + 1))
    return("%s-%s-%s" % (str(year), str(month), str(day)))

def calc_thanksgiving(year):
    year = int(year)
    thursday_count = 0
    date = "%s-11-01" % str(year)
    date = datetime.strptime(date, "%Y-%m-%d")
    while thursday_count < 4:
        if date.strftime("%A") == "Thursday":
            thursday_count += 1
        if thursday_count != 4:
            date = date + relativedelta(days = 1)
    return(date.strftime("%Y-%m-%d"))

def is_trading_day(date):
    day_name = date.strftime("%A")
    if day_name == "Saturday" or day_name == "Sunday":
        return(False)
    #new year's day
    if date.month == 1 and date.day == 1:
        return(False)
    #good friday
    if date.month == 3 or date.month == 4:
        easter = calc_easter(date.year)
        if day_name == "Friday":
            sunday = date + relativedelta(days = 2)
            sunday = sunday.strftime("%Y-%m-%d")
            if sunday == easter:
                return(False)

    #memorial day
    #last monday of may
    if date.month == 5 and day_name == "Monday":
        date = date + relativedelta(days = 1)
        while date.strftime("%A") != "Monday":
            date = date + relativedelta(days = 1)
        if date.month == 6:
            return(False)

    #labor day
    #first monday of september
    if date.month == 9 and date.day == 1 and day_name == "Monday":
        return(False)

    #thanksgiving
    if date.month == 11:
        thanksgiving = calc_thanksgiving(date.year)
        this_date = date.strftime("%Y-%m-%d")
        if this_date == thanksgiving:
            return(False)
    
    return(True)

#make sure the provided date is a trading day
#get the previous open market day if it's not
#return None if the next open market day is
#after the current date
def get_trading_date(date):
    date = datetime.strptime(date, "%Y-%m-%d")
    while not is_trading_day(date):
        date = date - relativedelta(days = 1)
    return(date.strftime("%Y-%m-%d"))
