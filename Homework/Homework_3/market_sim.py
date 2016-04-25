#!/usr/bin/python

import sys, argparse, csv, time

import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd

import numpy as np


#Global variables

#Plotting variables

#Functions

def readArguments():
  parser = argparse.ArgumentParser(description='Market Simulator')
  parser.add_argument('-c','--cash', help='Initial cash',required=True)
  parser.add_argument('-o','--ordersfile', help='Orders file name (.csv)',required=True)
  parser.add_argument('-v','--valuesfile', help='Values .csv generated file',required=True)
  args = parser.parse_args()
  
  return (args.cash, args.ordersfile, args.valuesfile)
  
def readOrders(ordersfile):
  ls_orders = np.loadtxt(ordersfile, dtype='i4,i4,i4,S5,S5,i6', delimiter=',', comments="#", skiprows=0)
  return ls_orders

def findSymbols(ordersList):
  ls_rawSymbols = []
  for order in ordersList:
    ls_rawSymbols.append(order[3])
  #Delete duplicated symbols
  ls_symbols = list(set(ls_rawSymbols))
  return ls_symbols

def findDates(ordersList):
  ls_rawDates = []
  for order in ordersList:
    ls_rawDates.append(dt.date(order[0], order[1], order[2]))
  #Delete duplicated symbols
  ls_dates = list(set(ls_rawDates))
  return sorted(ls_dates)

def getData(dt_start, dt_end, ls_symbols):
  #Get data values (only interested in adjusted close)
  dt_timeofday = dt.timedelta(hours=16)
  ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
  c_dataobj = da.DataAccess('Yahoo')
  ls_keys = ['close']
  ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
  d_data = dict(zip(ls_keys, ldf_data))
  return d_data

def getOrdersData(dt_start, dt_end, ls_symbols, ls_orders):
  ldt_timestamps = du.getNYSEdays(dt_start, dt_end)
  d_data = pd.DataFrame(index=ldt_timestamps, columns=ls_symbols)
  d_data = d_data.fillna(0.0)
  
  for order in ls_orders:
    dt_order = dt.date(order[0], order[1], order[2])
    symbol = order[3]
    operation = order[4]
    number = order[5]
    if operation.upper() == 'BUY':
      d_data[symbol].ix[dt_order] += number
    elif operation.upper() == 'SELL':
      d_data[symbol].ix[dt_order] -= number
      
  return d_data  
  
def getCashData(start_cash, d_price, d_operations):
  d_data = d_operations.copy()
  ls_columns = ['Cash']
  
  na_cash_value = []
  na_order_price = np.sum(d_operations.values*d_price['close'], axis=1)
  
  for price in na_order_price:
    if len(na_cash_value) != 0:
      na_cash_value.append(na_cash_value[-1]-price)
    else:
      na_cash_value.append(start_cash-price)
      
  return pd.DataFrame(na_cash_value, index=d_data.index, columns=ls_columns)

def getPortfolioValue(d_price, d_operations):
  #Get stock holdings over time
  df_holdings = d_operations.cumsum(axis=0)
  df_holdings_value = df_holdings*d_price['close'].values
  na_porfolio_value = np.sum(df_holdings_value.values, axis=1)
  
  return pd.DataFrame(na_porfolio_value, index=d_operations.index, columns=['Value'])

def writeToCsv(df_value, filename):
  df_value.to_csv(filename)
  
#Main funcion
def main():
  start_cash, ordersfile, valuesfile = readArguments()
  
  print "Reading "+ordersfile+" file..."
  ls_orders = readOrders(ordersfile)

  print "Finding symbols and dates..."
  ls_symbols = findSymbols(ls_orders)
  ls_dates = findDates(ls_orders)
  dt_start = ls_dates[0]
  dt_end = ls_dates[-1]
  
  print "Fetching data from orders symbols from "+str(dt_start)+" to "+str(dt_end)+"..."
  df_price = getData(dt_start, dt_end, ls_symbols)

  print "Generating operations dataframe..."
  df_orders = getOrdersData(dt_start, dt_end, ls_symbols, ls_orders)
  
  print "Generating cash dataframe..."
  df_cash = getCashData(float(start_cash), df_price, df_orders)
  
  print "Generating overtime portfolio value dataframe..."
  df_portfolio = getPortfolioValue(df_price, df_orders)
  
  print "Calculating portfolio + cash value..."
  df_portfolio['Cash'] = df_cash
  
  na_porfolio_value = np.sum(df_portfolio.values, axis=1)
  
  df_portfolio_value = pd.DataFrame(na_porfolio_value, index=df_orders.index, columns=['FinalValue'])
    
  print "Writing portfolio history to "+valuesfile
  writeToCsv(df_portfolio_value, valuesfile)
  
  
if __name__ == "__main__":
   main()
