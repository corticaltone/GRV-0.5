'''GRV 0.5 by Tony Hill
GRV (Growth, Return, Value) is a stock selection tool for dividend growth investors. GRV
pulls data from a previously defined universe of stocks and filters them based on critera
for dividend growth, yield (return) and price/earnings (value). Selected stocks can then
be further investigated by the user.'''

from cs50 import SQL
import sys
import csv
import json
from GRVhelpers import *
import os
import sqlalchemy
from sql import *
from sql.aggregate import *
from sql.conditionals import *


class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)
    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)

db = SQL("sqlite:///GRV.db")

# data_refresh reads stock symbols from a list identified by a
#user provided parameter and downloads quote information for them
#AllStocks updated 1/13/2017 from 'http://www.nasdaq.com/screening/company-list.aspx'
#Achievers updated 1/13/2017 from 'http://www.suredividend.com/dividend-achievers-list/'
#Aristocrats updated 1/13/2017 frmo 'http://www.suredividend.com/dividend-aristocrats-list/' '''
def data_refresh(stock_list):
    #Get appropriate list
    '''This section for use in web interface version:
    user_path = "AllStocks.csv"
    avail_lists = {'AllStocks': 'AllStocks.csv',
        'Achievers': 'Achievers.csv',
        'Aristocrats': 'Aristocrats.csv',
        'user_list': user_path
    }
    
    if stock_list in avail_lists:
        list_path = avail_lists[stock_list]
    else:
        #defaults to all stocks
        list_path = 'AllStocks.csv'
        '''
        
    #get list file for command line version
    list_path = stock_list
    
    #parse stock list, download data and store in sql database
    stocks = get_data(list_path)
    download_data(stocks)
    
# get_data parses the designated .csv file and returns a
# list of stock symbols
def get_data(list_file):
    #initialize stock list
    stock_universe = []
    #attempt to read file and return stocks
    try:
        stock_file = open(list_file, 'rU')
        reader = csv.reader(stock_file)
        
        for row in reader:
            stock_universe.append(row[0])
        stock_universe.pop(0)  #remove header
        return stock_universe
    except IOError:
        print ("Error reading file")
        return "CVX"

#download_data fetches current stock data and 
def download_data(stock_symbols):
    #Clear previous data
    db.execute("DELETE FROM Stock_Data")
    #db.execute("VACUUM")
    excluded = 0
    included = 0
    for symbol in stock_symbols:
        stock_dict = (lookup(symbol))
        # attempt to add stock to database
        try:
            db.execute("INSERT INTO Stock_Data (Symbol, Name, Price, Dividend, Yield, EPS, div_growth, PE) VALUES (:share_symbol, :share_name, :share_price, :share_dividend, :share_yield, :share_earnings, :div_growth, :price_earnings)", share_symbol = stock_dict["symbol"], share_name = stock_dict["name"], share_price = stock_dict["price"], share_dividend = stock_dict["dividend"], share_yield = stock_dict["yield"], share_earnings = stock_dict["EPS"], div_growth = stock_dict["div_growth"], price_earnings = stock_dict["PE"])
            included += 1
        except:
            print ("Error updating SQL database for symbol", symbol)
            excluded += 1

    print ("excluded =", excluded, "included =", included)
    return

#data_select chooses stocks from the sql database matching GRV criteria
def data_select(settings_dict):
    selected_stocks = db.execute("SELECT * FROM Stock_Data WHERE EPS > 0 AND\
    div_growth >= :dGrowth AND yield >= :dYield AND PE <= :sPE", dGrowth =\
    settings_dict['dgrowth'], dYield = settings_dict['dyield'], sPE = settings_dict['svalue'])
    s2 = db.execute("SELECT * FROM Stock_Data")
    #return (selected_stocks)
    return (selected_stocks)
    
# csv_export produces a .csv file containing the selected stocks and their data
def csv_export(my_stocks, my_list):
    ftitle = "Stocksfrom"+my_list
    f = open(ftitle, "wt")
    try:
        writer = csv.writer(f)
        # iterate through stocks and write file
        writer.writerow( ('Symbol', 'Name', 'Price', 'Dividend') )
        for row in my_stocks:
            writer.writerow( (row['Symbol'], row['Name'], row['Price'], row['Dividend'] ))
    finally:
        f.close()
    return

# print_stocks prints a table of 
def print_stocks(rows):
    print("Symbol".center(8), "Name".center(40), "Price".center(6), "Dividend".center(10), "Yield".center(7), "Price/Earnings(%)".center(20), "Dividend Growth Rate(%)".center(25))
    for row in rows:
        price = "{:.2f}".format(row['Price'])
        dividend = "{:.2f}".format(row['Dividend'])
        dyield = "{:.2f}".format(row['Yield'])
        PoE = "{:.2f}".format(row['PE'])
        DGR = "{:.2f}".format(row['div_growth'])
        EpS = "{:.2f}".format(row['EPS'])
        
        print(row['Symbol'].center(8), row['Name'].center(40), price.center(6), dividend.center(10), dyield.center(7), PoE.center(20), DGR.center(25))
    return

def main():
    #case 1: specified file
    if len(sys.argv) == 5 and sys.argv[1].endswith('.csv'):
        current_list = sys.argv[1]
        try:
            growth = float(sys.argv[2])
            dyield = float(sys.argv[3])
            pe = float(sys.argv[4])
        except:
            print('Enter program name, CSV format stock list file (optional) growth rate (0.00 to 1.00), yield (0.00 to 1.00) and PE (positive number) separated by spaces')
            print('Example: python GRV.py Aristocrats.csv .08 .03 16')
            sys.exit(1)
        
    #case 2: no specified file
    elif len(sys.argv) == 4 :
            current_list = 'Aristocrats.csv'
            try:
                growth = float(sys.argv[1])*100
                dyield = float(sys.argv[2])*100
                pe = float(sys.argv[3])
            except:
                print('Enter program name, growth rate (0.0 to 1.0), yield (0.0 to 1.0) and PE (positive number) separated by spaces')
                sys.exit(2)
    else:
        #case 3: incorrect number of command line arguments
        print('Enter program name, growth rate (0.00 to 1.00), yield (0.00 to 1.00) and PE (positive number) separated by spaces')
        sys.exit(3)
    if growth > 100 or growth < 0 or dyield > 100 or dyield < 0:
        print('growthrate and yield must be positive decimals <= 1')
        sys.exit(3)

    data_refresh(current_list)
    param_dict = {
      'dgrowth': growth,
      'dyield': dyield,
      'svalue': pe
    }

    filtered_stocks = data_select(param_dict)
    print_stocks(filtered_stocks)
    csv_export(filtered_stocks, current_list)
  
if __name__ == '__main__':
  main()
  
