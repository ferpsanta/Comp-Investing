import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

import datetime as dt
import time
import matplotlib.pyplot as plt
import pandas as pd

import numpy as np

#Global variables
risk_free_rate = 0.00
allocation_step = 0.10
legal_allocation = 1.00
#Plotting variables
plotResults = False
plotPath = ""
plotComparison = True
plotBenchmarks = ["$SPX"]

#Initial portfolio data here
ls_symbols = ["C", "GS", "IBM", "HNZ", "GOOG", "HNZ"]
ls_symbolsAllocation = np.array([0.40, 0.30, 0.00, 0.10, 0.10, 0.10])
dt_start = dt.datetime(2010, 1, 1)
dt_end = dt.datetime(2010, 12, 31)
    
# Functions

def simulate(startdate, enddate, symbols, allocation, plot):
    #Get data values (only interested in close ftm)
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
    c_dataobj = da.DataAccess('Yahoo')
    ls_keys = ['close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    #Normalize data
    na_price = d_data['close'].values
    na_norm_price = na_price / na_price[0,:]
    
    #Weight normalized values with portfolio allocation
    na_normAllocated_price = na_norm_price.copy() * allocation

    #Cumulative daily portfolio value (normalized)
    na_cumulative_price = np.sum(na_normAllocated_price, axis=1)
    
    #Portfolio daily return => ret(t) = (price(t)/price(t-1)) -1
    na_ret = na_cumulative_price.copy()
    tsu.returnize0(na_ret)

    #Portfolio stadistics
    ##Standard daily deviation
    na_std_ret = np.std(na_ret)
    ##Final return
    na_final_ret = na_cumulative_price[-1]
    ##Mean portfolio return
    na_mean_ret = np.mean(na_ret)
    ##Average daily return
    na_avg_ret = np.mean(na_ret)
    ##Sharpe Ratio
    na_sharpe_ratio = tsu.get_sharpe_ratio(na_ret)

    if plot:
        plotNormalized(ldt_timestamps, na_cumulative_price)
        
    return (na_std_ret, na_final_ret, na_mean_ret, na_sharpe_ratio)

def isAllocationLegal(allocation):
    if np.sum(allocation) == legal_allocation:
        return True
    else:
        return False

def recursiveSharpeOptimization(index, start, end, symbols, allocation):
    allocation_range = np.arange(0, legal_allocation+allocation_step, allocation_step)
    maxSharpe = 0.0
    optAllocation = []
    for i in allocation_range:
        allocation[0][index] = i
        if isAllocationLegal(allocation):
            std_ret, final_ret, mean_ret, sharpe_ratio = simulate(start, end, symbols, allocation, False)
            if sharpe_ratio > maxSharpe:
                maxSharpe = sharpe_ratio
                optAllocation = allocation.copy()
        else:
            if index < len(symbols)-1:
                rec_sharpe, rec_alloc = recursiveSharpeOptimization((index+1), start, end, symbols, allocation)
                if rec_sharpe > maxSharpe:
                    maxSharpe = rec_sharpe
                    optAllocation = rec_alloc.copy()
                    
    return (maxSharpe, optAllocation)

def optimize(start, end, symbols):
    opt_allocation = np.zeros((1,len(ls_symbols)))
    maxSharpe, opt_allocation = recursiveSharpeOptimization(0, start, end, symbols, opt_allocation)
    return maxSharpe, opt_allocation

def printResults(std_ret, avg_ret, sharp_ratio, final_ret):
    print "Sharpe Ratio: "+str(sharp_ratio)
    print "Volatility (stdev of daily returns): "+str(std_ret)
    print "Avg. Daily return: "+str(avg_ret)
    print "Cumulative return: "+str(final_ret)

def plotNormalized(timestamp, returns):
    plt.clf()
    plt.ylabel('Normalized Close')
    plt.xlabel('Date')
    #BenchMark data fetching
    if plotComparison:
        c_dataobj = da.DataAccess('Yahoo')
        ls_keys = ['close']
        ldf_data = c_dataobj.get_data(timestamp, plotBenchmarks, ls_keys)
        d_data = dict(zip(ls_keys, ldf_data))
        bm_price = d_data['close'].values
        bm_normalized_price = bm_price/bm_price[0,:]
        plt.plot(timestamp, bm_normalized_price)
        
    plotBenchmarks.append("Portfolio")
    plt.plot(timestamp, returns)
    plt.legend(plotBenchmarks) 
    plt.savefig('normalizedclose.pdf', format='pdf')
   
                                      
#Main function
def main():
    print "Optimizing portfolio using sharpe ratio as reference..."
    start_time = time.time()
    maxSharpe, opt_allocation = optimize(dt_start, dt_end, ls_symbols)
    elapsed_time = time.time() - start_time
    print "Done! ("+str(elapsed_time)+" seconds)"
    print "Optimal Portfolio allocations: "
    print ls_symbols
    print opt_allocation
    print "Calculating portfolio stadistics..."
    start_time = time.time()
    std_ret, final_ret, mean_ret, sharpe_ratio = simulate(dt_start, dt_end, ls_symbols, opt_allocation, True)
    elapsed_time = time.time() - start_time       
    print "Done! ("+str(elapsed_time)+" seconds)"
    print "Porfolio output: "
    printResults(std_ret, mean_ret, sharpe_ratio, final_ret)
    
if __name__ == "__main__":
    main()
