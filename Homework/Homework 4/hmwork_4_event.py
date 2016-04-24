import pandas as pd
import numpy as np
import math
import csv
import copy
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep
# Global vars
dataobj = da.DataAccess('Yahoo')
 
#Initial portfolio data here
dt_start = dt.datetime(2008, 1, 1)
dt_end = dt.datetime(2009, 12, 31)

# Functions
def find_events(symbols, data, price_dropdown):
    #We are only interested in the actual close
    df_actual_close = data['actual_close']
   
    print "Finding Events..."

    # Creating an empty dataframe
    df_events = copy.deepcopy(df_actual_close)
    df_events = df_events * np.NAN

    # Time stamps for the event range
    ldt_timestamps = df_actual_close.index

    for s_sym in symbols:
        for i in range(1, len(ldt_timestamps)):
            # Event is found is the price drops below 'price_dropdown'
            f_price_today = df_actual_close[s_sym].ix[ldt_timestamps[i]]
            f_price_yest = df_actual_close[s_sym].ix[ldt_timestamps[i - 1]]

            if f_price_today < price_dropdown and f_price_yest >= price_dropdown:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1

    return df_events

def get_data(startdate, enddate, symbols):
    
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))
   
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # Sanityze data
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    return d_data

def create_event_profile (events, data, profile_name):
    print "Creating event profile..."
    return ep.eventprofiler(events, data, i_lookback=20, i_lookforward=20,
                s_filename=profile_name+'_profile.pdf', b_market_neutral=True,
                b_errorbars=True, s_market_sym='SPY')

def generate_orders(df_events):
    ls_orders=[]
    ls_dates = df_events.index

    for symbol in df_events:
        for date in ls_dates:
            if df_events[symbol][date] == 1:
                ls_orders.append([date.strftime('%Y, %m, %d'), "BUY", symbol, "100"])
                
                # Manages out of time range sells
                aux_pos_index = ls_dates.get_loc(date)+5
                if aux_pos_index <= len(ls_dates):
                    date_sell = ls_dates[aux_pos_index]
                else:
                    date_sell = ls_dates[-1]
                    
                ls_orders.append([date_sell.strftime('%Y, %m, %d'), "SELL", symbol, "100"])
                
    return ls_orders

def write_orders(ls_list_name, ls_orders):
    print "Generatings "+ls_list_name+"_orders.csv ..."
    with open(ls_list_name+"_orders.csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(ls_orders)
    
#Main function
def main():
    p_dropdown_price = 5.0
    
    ls_list_name = 'sp5002012'
    print "Getting data from "+ls_list_name+" symbols..."
    #Get symbols list
    ls_symbols = dataobj.get_symbols_from_list(ls_list_name)
    #Add market to symbols list
    ls_symbols.append('SPY')
    #Fetch symbols data
    d_data_2012 = get_data(dt_start, dt_end, ls_symbols)
    
    #Find events and create a event profile
    df_events_2012 = find_events(ls_symbols, d_data_2012, p_dropdown_price)
    df_event_profile_2012 = create_event_profile(df_events_2012, d_data_2012, str(p_dropdown_price)+'_'+ls_list_name) 

    ls_orders = generate_orders(df_events_2012)

    write_orders(ls_list_name, ls_orders)
    
if __name__ == '__main__':
    main()
