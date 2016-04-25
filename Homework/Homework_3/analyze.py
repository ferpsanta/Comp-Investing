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
  parser = argparse.ArgumentParser(description='Portfolio report analyzer')
  parser.add_argument('-v','--ordersfile', help='Values file name (.csv)',required=True)
  parser.add_argument('-b','--benchmark', help='benchmark symbol used for graphical comparison',required=True)
  args = parser.parse_args()
  
  return (args.ordersfile, args.benchmark)
  
def readValues(valuesfile):
  na_read = np.loadtxt(valuesfile, dtype='S10,i6', delimiter=',', comments="#", skiprows=1)
  na_values = []
  
  for row in na_read:
    na_values.append(float(row[1]))
    
  na_dt_start = na_read[0][0].split("-")
  na_dt_end = na_read[-1][0].split("-")

  dt_start = dt.datetime(int(na_dt_start[0]),int(na_dt_start[1]),int(na_dt_start[2]))
  dt_end = dt.datetime(int(na_dt_end[0]),int(na_dt_end[1]),int(na_dt_end[2]))
  
  dt_timeofday = dt.timedelta(hours=16)
  ldt_timestamps = du.getNYSEdays(dt_start, dt_end+dt.timedelta(days=1), dt_timeofday)
  
  df_values = pd.DataFrame(na_values, index=ldt_timestamps, columns=['value'])
  
  return df_values

def calculatePerformance(na_portfolio_value):
  #Normalize data 
  na_norm_return = na_portfolio_value / na_portfolio_value[1]

  #Portfolio daily return => ret(t) = (price(t)/price(t-1)) -1
  na_ret = na_norm_return.copy()
  tsu.returnize0(na_ret)

  #Portfolio stadistics
  ##Standard daily deviation
  na_std_ret = np.std(na_ret)
  ##Final return
  na_final_ret = na_norm_return[-1]
  ##Mean portfolio return
  na_mean_ret = np.mean(na_ret)
  ##Average daily return
  na_avg_ret = np.mean(na_ret)
  ##Sharpe Ratio
  na_sharpe_ratio = tsu.get_sharpe_ratio(na_ret)

  return (na_std_ret, na_final_ret, na_mean_ret, na_sharpe_ratio)

def printResults(std_ret, avg_ret, final_ret, sharp_ratio):
  print "Sharpe Ratio: "+str(sharp_ratio)
  print " "
  print "Volatility (stdev of daily returns): "+str(std_ret)
  print " "
  print "Avg. Daily return: "+str(avg_ret)
  print " "
  print "Cumulative return: "+str(final_ret)

def writeToCsv(df_value, filename):
  df_value.to_csv(filename)
  
#Main funcion
def main():
  valuesfile, benchmark = readArguments()
  
  print "Reading "+valuesfile+" file..."
  df_portfolio_value = readValues(valuesfile)
  
  print "Computing porftolio performance:"
  std_ret, final_ret, avg_ret, sharpe_ratio = calculatePerformance(df_portfolio_value['value'].values)
  
  printResults(std_ret, avg_ret, final_ret, sharpe_ratio)
  
if __name__ == "__main__":
   main()