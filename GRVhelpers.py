import csv
import re
import urllib.request
from lxml import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime
#from datetime import timedelta
#from datetime import date

#from flask import redirect, render_template, request, session, url_for
from functools import wraps

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def lookup(symbol):
    """Look up quote for symbol."""

    # reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # reject symbol if it contains comma
    if "," in symbol:
        return None

    # query Yahoo for quote
    # http://stackoverflow.com/a/21351911
    try:
        url = "http://download.finance.yahoo.com/d/quotes.csv?f=snl1dye&s={}".format(symbol)
        webpage = urllib.request.urlopen(url)
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
        row = next(datareader)
    except:
        return None

    # ensure stock exists and has earnings
    try:
        price = float(row[2])
    except:
        price = 0
    try:
        PE = price/float(row[5])
    except:
        PE = 0
        
    #attempt to calculate historical dividend growth rate
    try:
        DGR = div_growth(symbol)
    except: 
        print ("Error finding dividend growth rate for symbol", symbol)
        DGR = 0
        #return None

    # return stock's name price symbol dividend yield dividend growth and EPS
    return {
        "name": row[1],
        "price": price,
        "symbol": row[0].upper(),
        "dividend": row[3],
        "yield": row[4],
        "EPS": row[5],
        "div_growth": DGR,
        "PE": PE
    }
    
        
def div_growth2(symbol):
    return (50)

# div_growth scrapes a stock's dividend growth information from nasdaq.com
def div_growth(symbol):
    # download xml tree for symbol's dividend history page
    url = "http://www.nasdaq.com/symbol/{}/dividend-history".format(symbol)
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, "lxml")
    date_list = soup.findAll(id=re.compile("exdate"))
    div_list = soup.findAll(id=re.compile("CashAmount"))
    first_date = get_scrapedData(str(date_list[0]))
    #first_date = get_scrapedDate(date_list[0])
    #first_date = "02/15/2016"
    first_div = float(get_scrapedData(str(div_list[0])))
    last_date = get_scrapedData(str(date_list[len(date_list)-1]))
    #last_date = "02/01/2012"
    last_div = float(get_scrapedData(str(div_list[len(div_list)-1])[-11:-1]))
    last_dateobj = datetime.strptime(last_date, "%m/%d/%Y")
    first_dateobj = datetime.strptime(first_date, "%m/%d/%Y")
    elapsed_time = first_dateobj - last_dateobj
    # calculate average dividend growth % per year
    dGrowth = 100 * ((first_div - last_div)/last_div) / (elapsed_time.days/365)
    return dGrowth
    
    # find dates and dividend per share
    #dates = tree.xpath('//tr[@span id="quotes_content_left_dividendhistoryGrid_exdate_0"]/text()')
    #divs = tree.xpath('//tr[@span id="quotes_content_left_dividendhistoryGrid_CashAmount_4"]/text()')
    #print(divs, dates)
    return
    
# get_scrapedData extracts the dividend value or date from a dividend span element and returns it as a string
def get_scrapedData(span_text):
    div_bindex = int(span_text.find(">"))+1
    div_endex = int(span_text.find("</"))
    return (span_text[div_bindex:div_endex])
    
# get_scrapedDate extracts the date from a span element and returns it as a string
def get_scrapedDate(span_text):
    date_bindex = -17
    date_endex = -7
    line = str(span_text)
    if line[date_bindex] == ">":
        date_bindex += 1
    return (line[date_bindex:date_endex])

def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)
