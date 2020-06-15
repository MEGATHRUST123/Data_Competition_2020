import pandas as pd
import numpy as np
import re
from datetime import date, datetime, time, timedelta

# read data
data = pd.read_csv('order_brush_order.csv')

# Simple Data Cleaning 
data['orderid'] = data['orderid'].astype(str)
data['shopid'] = data['shopid'].astype(str)
data['event_time'] = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in data['event_time']]
data['end_time'] = [x + timedelta(hours=1) for x in data['event_time']]

# samples
try_shops = ['10159']
list_shops = list(set(data['shopid']))

# order brushing
output = []

for i, shops in enumerate(try_shops):
    print(f'shop: {i} - {shops}')  
    dff = data[(data['shopid']==shops)]
    dff = dff.sort_values('event_time')  
    shop_summary = []
    dt_list = list(set(dff['event_time']))
    dt_list.sort()
    for dt in dt_list:
        e = dt + timedelta(hours=1) # add an hour to the event start time
        dfff = dff[(dff['event_time']>=dt) & (dff['event_time']<=e)] # filter 
        cr = dfff.orderid.nunique()/dfff.userid.nunique() # concentration rate
        if cr >= 3: #concentration rate >=3 - shop has order brushing
            temp = dfff.groupby(['userid']).orderid.nunique().reset_index(name='ord_cnt') # users and total number of orders by thr customer
            temp_dict=[]
            for i, row in temp.iterrows():
                temp_dict.append({'userid':row['userid'],'cnt':row['ord_cnt']}) #append their details to temp_dict
                
            summary = {'event':dt.strftime('%Y-%m-%d %H:%M:%S'), #shop level information
                       'orders':dfff.orderid.nunique(),
                       'users':dfff.userid.nunique(),
                       'user_list':temp_dict,
                       'cr':cr}
            
            shop_summary.append(summary)
        
    shop_df = pd.DataFrame(shop_summary) #create a dataframe 
        
    if len(shop_df) == 0:
        output.append(pd.DataFrame({'shopid':shops,'userid':[0]})) #shops with no order brushing
    else:
        temp = []
        for i in list(range(len(shop_df))):
            temp.append(pd.DataFrame(shop_df['user_list'][i]))
        temp = pd.concat(temp, axis=0)
        total_orders = shop_df['orders'].sum() # total orders for the shop
        cust_brush = temp.groupby('userid').cnt.mean().reset_index(name='ord') # orders by customers during brushing period
        cust_brush['op'] = cust_brush['ord']/total_orders # order proportion
        cust_brush['shopid'] = shops
        top_user = cust_brush.nlargest(1, 'op', keep='all') # top suspicious user
        top_user = top_user.sort_values('user') # sort the values 
        temp_user = top_user.groupby('shopid').apply(lambda row: '&'.join(row['userid'])).reset_index(name='userid') #concatenate userid
        output.append(temp_user)

#all shops
alldf = pd.concat(output,axis=0)
alldf.columns

# output
alldf.to_csv('C:/Users/kelly/OneDrive/Desktop/Python Code/competition/submission_v6.csv', index=False)