#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: tongdan

"""
import numpy as np 
import pandas as pd
import time
import datetime
import math

#####-----count the code running time-----
start=datetime.datetime.now()

# read EIA raw generation demand data
path = "/Users/tongdan/Desktop/1.work/1.SEM/1.Data/1.EIA_demand_data"

#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2015_Jul_Dec.xlsx'.format(path))
#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2016_Jan_Jun.xlsx'.format(path))
#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2016_Jul_Dec.xlsx'.format(path))
#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2017_Jan_Jun.xlsx'.format(path))
#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2017_Jul_Dec.xlsx'.format(path))
#jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2018_Jan_Jun.xlsx'.format(path))
jul_dec_2015 = pd.read_excel('{}/EIA930_BALANCE_2018_Jul_Dec.xlsx'.format(path))

# change the format of the ''UTC Time at End of Hour‘’ to the datetime format
jul_dec_2015['UTC Time at End of Hour']=jul_dec_2015['UTC Time at End of Hour'].apply(lambda x: time.strptime(x, '%m/%d/%Y %I:%M:%S %p'))
jul_dec_2015['UTC Time at End of Hour']=jul_dec_2015['UTC Time at End of Hour'].apply(lambda x: time.strftime('%Y-%m-%d %H:%M:%S', x))
jul_dec_2015['UTC Time at End of Hour'] = pd.to_datetime(jul_dec_2015['UTC Time at End of Hour'],format='%Y-%m-%d %H:%M:%S')

# count the number of Balancing Authority and clean up the demand data BA-by-BA
BAs=list(set(jul_dec_2015['Balancing Authority']))

#-------bulid a complete dataframe 'jul_dec_2015_m' to fill the raw and corrected generation demand--------
jul_dec_2015_m=pd.DataFrame()

for i in range(len(BAs)):
    #dates_2015_ = pd.date_range('2015-07-01 05:00:00', '2016-01-01 08:00:00', freq='H')
    #dates_2015_ = pd.date_range('2016-01-01 06:00:00', '2016-07-01 07:00:00', freq='H')
    #dates_2015_ = pd.date_range('2016-07-01 05:00:00', '2017-01-01 08:00:00', freq='H')
    #dates_2015_ = pd.date_range('2017-01-01 06:00:00', '2017-07-01 07:00:00', freq='H')
    #dates_2015_ = pd.date_range('2017-07-01 05:00:00', '2018-01-01 08:00:00', freq='H')
    #dates_2015_ = pd.date_range('2018-01-01 06:00:00', '2018-07-01 07:00:00', freq='H')
    dates_2015_ = pd.date_range('2018-07-01 05:00:00', '2019-01-01 08:00:00', freq='H')
    dates_2015 = pd.DataFrame(index=dates_2015_,columns=['Balancing Authority','Demand (MW)','Demand Forecast (MW)'])
    dates_2015['Balancing Authority']=BAs[i]
    jul_dec_2015_m=jul_dec_2015_m.append(dates_2015)
  
# reset the index [BA and UTC time] to mapping with the complete dataframe
jul_dec_2015=jul_dec_2015.reset_index()
jul_dec_2015.set_index(['UTC Time at End of Hour','Balancing Authority'],inplace=True)
jul_dec_2015_m=jul_dec_2015_m.reset_index()
jul_dec_2015_m.set_index(['index','Balancing Authority'],inplace=True)
# mapping the demand and the demand forcast
jul_dec_2015_m['Demand_org (MW)']=jul_dec_2015['Demand (MW)']
jul_dec_2015_m['Demand (MW)']=jul_dec_2015['Demand (MW)']
jul_dec_2015_m['Demand Forecast (MW)']=jul_dec_2015['Demand Forecast (MW)']

##------begin to deal with the jul_dec_2015_m dataframe-------
jul_dec_2015_m=jul_dec_2015_m.reset_index()
jul_dec_2015_m.rename(columns={'index': 'UTC Time at End of Hour'}, inplace = True)

## build up UTC_h, UTC_date, and UTC_time for the following demand correction
jul_dec_2015_m['UTC_h']=jul_dec_2015_m['UTC Time at End of Hour'].apply(lambda x: x.hour)
jul_dec_2015_m['UTC_date']=jul_dec_2015_m['UTC Time at End of Hour'].apply(lambda x: datetime.date(x.year,x.month,x.day))
jul_dec_2015_m['UTC_time']=jul_dec_2015_m['UTC_date'].apply(lambda x: time.mktime(x.timetuple()))
jul_dec_2015_m['Label1']='nan'
## by the order of BAs and UTC_h for the demand data
jul_dec_2015_m=jul_dec_2015_m.sort_values(by = ['Balancing Authority','UTC_h','UTC Time at End of Hour'],axis = 0,ascending = True)

###--------deal with the missing data and abnormal data-------

### first, correct the negative values with demand forecast
sum_neg= sum(1 for x in jul_dec_2015_m['Demand (MW)'] if x < 0) 
if sum_neg > 0:
    print("---There are",sum_neg,"negative values in the file---")
    for ii,i in enumerate(jul_dec_2015_m['Demand (MW)']):
        if i < 0:
            jul_dec_2015_m['Demand (MW)'].iloc[ii] = jul_dec_2015_m['Demand Forecast (MW)'].iloc[ii]
            jul_dec_2015_m['Label1'].iloc[ii]='negative'
else:        
    print("---There are no negative value in the file---")
    
#check again    
sum_neg_off= sum(1 for x in jul_dec_2015_m['Demand (MW)'] if x < 0)
print("---There are",sum_neg_off,"negative value left in the file---")
###----------------------------------------------------------------------

### second, select the demand value==0 but the mean demand larger than 0 for the same hour and same region
### relaced by nan

gb_2015 = jul_dec_2015_m.groupby(['Balancing Authority','UTC_h'])["Demand (MW)"].mean()
gb_2015_mean=gb_2015.reset_index()

#mapping the mean values to the jul_dec_2015_m dataframe
for i in range(len(gb_2015_mean)):
    jul_dec_2015_m.loc[(jul_dec_2015_m['Balancing Authority']==gb_2015_mean['Balancing Authority'][i])&(jul_dec_2015_m['UTC_h']==gb_2015_mean['UTC_h'][i]),'Demand Ave (MW)'] = gb_2015_mean["Demand (MW)"].values[i]

## fill the data
zero_value=np.where((jul_dec_2015_m['Demand Ave (MW)'] > 0) & (jul_dec_2015_m['Demand (MW)'] == 0))
zero_value=(np.array(zero_value,dtype=int)).transpose()
print("---There are",len(zero_value),"zero demand value with mean demand > 0 in the file---")
jul_dec_2015_m['Demand (MW)'].iloc[zero_value] = np.nan
###----------------------------------------------------------------------


### third, filling the missing value data.

# here we fill the missing data with the forecast data first.
nan_val=np.where((pd.isnull(jul_dec_2015_m['Demand (MW)'])) & (pd.notnull(jul_dec_2015_m['Demand Forecast (MW)'])))
nan_val=(np.array(nan_val,dtype=int)).transpose()
print("---There are",len(nan_val),"missing value with demand forecast data in the file---")

for i in range(len(nan_val)):
    #print("missing --", len(nan_val) ,"--", i)
    jul_dec_2015_m['Demand (MW)'].iloc[nan_val[i,0]] = jul_dec_2015_m['Demand Forecast (MW)'].iloc[nan_val[i,0]]
    jul_dec_2015_m['Label1'].iloc[nan_val[i,0]]='missing-demandfore'
    
#check again
nan_val_off = np.where((pd.isnull(jul_dec_2015_m['Demand (MW)'])) & (pd.notnull(jul_dec_2015_m['Demand Forecast (MW)'])))
nan_val_off=(np.array(nan_val_off,dtype=int)).transpose()
print("---There are",len(nan_val_off),"missing value with demand forecast data left in the file---")
###----------------------------------------------------------------------

# here we then fill the missing data with the nearby demand data.
res_miss=np.where((jul_dec_2015_m['Demand Ave (MW)'] >0) & (pd.isnull(jul_dec_2015_m['Demand (MW)'])))
res_miss=(np.array(res_miss,dtype=int)).transpose()
print("---There are",len(res_miss),"missing value with no demand forecast data in the file---")

for i in range(len(res_miss)):
    # different scenarios
    print("missing --", len(res_miss) ,"--", i)
    date_=jul_dec_2015_m['UTC_date'][(jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[res_miss[i,0]])]
    if jul_dec_2015_m['UTC_date'].iloc[res_miss[i,0]] == date_.min() and jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]+1]>0:
        jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]+1]
        jul_dec_2015_m['Label1'].iloc[res_miss[i,0]]='nearest value'
    elif jul_dec_2015_m['UTC_date'].iloc[res_miss[i,0]] == date_.min():
        aa=np.where((jul_dec_2015_m['Demand (MW)'] >0) & (jul_dec_2015_m['Balancing Authority']==jul_dec_2015_m['Balancing Authority'].iloc[res_miss[i,0]]) & (jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[res_miss[i,0]]))
        aa=np.array(aa,dtype=int).min()
        jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[aa]
        jul_dec_2015_m['Label1'].iloc[res_miss[i,0]]='nearest value'
    elif jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]-1]>0:
        jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]-1]
        jul_dec_2015_m['Label1'].iloc[res_miss[i,0]]='nearest value'
    else:       
        bb=np.where((jul_dec_2015_m['Demand (MW)'] >0) & (jul_dec_2015_m['Balancing Authority']==jul_dec_2015_m['Balancing Authority'].iloc[res_miss[i,0]]) & (jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[res_miss[i,0]]))
        bb=(np.array(bb,dtype=int)).transpose()
        # nearest date
        dff=pd.DataFrame(abs(jul_dec_2015_m['UTC_time'].iloc[bb[:,0]]-jul_dec_2015_m['UTC_time'].iloc[res_miss[i,0]]))
        dff1 =min(dff.idxmin())
        tloc=int(np.asarray(np.where(jul_dec_2015_m.index==dff1)))
        jul_dec_2015_m['Demand (MW)'].iloc[res_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[tloc]
        jul_dec_2015_m['Label1'].iloc[res_miss[i,0]]='nearest value'
 
#### --------check---------
miss_off=np.where((jul_dec_2015_m['Demand Ave (MW)'] >0) & (pd.isnull(jul_dec_2015_m['Demand (MW)'])))
miss_off=(np.array(miss_off,dtype=int)).transpose()
print("---There are",len(miss_off),"missing value left with mean demand > 0 in the file---")


### Finally, correct the abnormal values, and judging the standard deviation by lognormal distribution
# also get the mean value for assisting determination
jul_dec_2015_m['adjust']=jul_dec_2015_m['Demand (MW)']/jul_dec_2015_m['Demand Ave (MW)']

zero_value=np.where(jul_dec_2015_m['Demand (MW)'] == 0)
zero_value=(np.array(zero_value,dtype=int)).transpose()
jul_dec_2015_m['Demand (MW)'].iloc[zero_value] = np.nan
# get the log value
jul_dec_2015_m['In_demand']=jul_dec_2015_m['Demand (MW)'].apply(lambda x: math.log(x,math.e))

#group by
gb_1 = jul_dec_2015_m.groupby(['Balancing Authority','UTC_h'])["In_demand"].mean()
gb_in_mean=gb_1.reset_index()

gb_2 = jul_dec_2015_m.groupby(['Balancing Authority','UTC_h'])["In_demand"].std()
gb_in_std=gb_2.reset_index()

abn_def=3; # >=mean+3*std or <=mean-3*std

#mapping the mean values to the jul_dec_2015_m dataframe
for i in range(len(gb_in_mean)):
    jul_dec_2015_m.loc[(jul_dec_2015_m['Balancing Authority']==gb_in_mean['Balancing Authority'][i])&(jul_dec_2015_m['UTC_h']==gb_in_mean['UTC_h'][i]),'In_Demand_low (MW)'] = gb_in_mean["In_demand"].values[i]-abn_def*gb_in_std["In_demand"].values[i]
    jul_dec_2015_m.loc[(jul_dec_2015_m['Balancing Authority']==gb_in_mean['Balancing Authority'][i])&(jul_dec_2015_m['UTC_h']==gb_in_mean['UTC_h'][i]),'In_Demand_up (MW)'] = gb_in_mean["In_demand"].values[i]+abn_def*gb_in_std["In_demand"].values[i]

abn_list=np.where((jul_dec_2015_m['In_demand'] <= jul_dec_2015_m['In_Demand_low (MW)']) | (jul_dec_2015_m['In_demand'] >= jul_dec_2015_m['In_Demand_up (MW)']))
jul_dec_2015_m['Demand (MW)'].iloc[abn_list] = np.nan #replaced by nan

abn_list=(np.array(abn_list,dtype=int)).transpose()
print("---There are",len(abn_list),"abnormal values in the file---")   


# for the abnormal using the nearby data to fill

abn_miss=np.where((jul_dec_2015_m['Demand Ave (MW)'] >0) & (pd.isnull(jul_dec_2015_m['Demand (MW)'])))
abn_miss=(np.array(abn_miss,dtype=int)).transpose()
print("---There are",len(abn_miss),"missing value left to fill in the file---")

for i in range(len(abn_miss)):
    # different scenarios
    print("missing --", len(abn_miss) ,"--", i)
    date_=jul_dec_2015_m['UTC_date'][(jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[abn_miss[i,0]])]
    if jul_dec_2015_m['UTC_date'].iloc[abn_miss[i,0]] == date_.min() and jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]+1]>0:
        jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]+1]
        jul_dec_2015_m['Label1'].iloc[abn_miss[i,0]]='abnomal'
    elif jul_dec_2015_m['UTC_date'].iloc[abn_miss[i,0]] == date_.min():
        aa=np.where((jul_dec_2015_m['Demand (MW)'] >0) & (jul_dec_2015_m['Balancing Authority']==jul_dec_2015_m['Balancing Authority'].iloc[abn_miss[i,0]]) & (jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[abn_miss[i,0]]))
        aa=np.array(aa,dtype=int).min()
        jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[aa]
        jul_dec_2015_m['Label1'].iloc[abn_miss[i,0]]='abnomal'
    elif jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]-1]>0:
        jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]-1]
        jul_dec_2015_m['Label1'].iloc[abn_miss[i,0]]='abnomal'
    else:       
        bb=np.where((jul_dec_2015_m['Demand (MW)'] >0) & (jul_dec_2015_m['Balancing Authority']==jul_dec_2015_m['Balancing Authority'].iloc[abn_miss[i,0]]) & (jul_dec_2015_m['UTC_h'] == jul_dec_2015_m['UTC_h'].iloc[abn_miss[i,0]]))
        bb=(np.array(bb,dtype=int)).transpose()
        # nearest date
        dff=pd.DataFrame(abs(jul_dec_2015_m['UTC_time'].iloc[bb[:,0]]-jul_dec_2015_m['UTC_time'].iloc[abn_miss[i,0]]))
        dff1 =min(dff.idxmin())
        tloc=int(np.asarray(np.where(jul_dec_2015_m.index==dff1)))
        jul_dec_2015_m['Demand (MW)'].iloc[abn_miss[i,0]] =jul_dec_2015_m['Demand (MW)'].iloc[tloc]
        jul_dec_2015_m['Label1'].iloc[abn_miss[i,0]]='abnomal'
#-------------------------------------------------------------------------------------------- 
        
        
#### --------final check---------
final_off=np.where((jul_dec_2015_m['Demand Ave (MW)'] >0) & (pd.isnull(jul_dec_2015_m['Demand (MW)'])))
final_off=(np.array(final_off,dtype=int)).transpose()
print("---finally, there are",len(final_off),"missing value in the file---")  

## by the order of BAs and date for the demand data
jul_dec_2015_m=jul_dec_2015_m.sort_values(by = ['Balancing Authority','UTC Time at End of Hour'],axis = 0,ascending = True)


#### write to excel
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2015_Jul_Dec_modified_n.xlsx'.format(path))
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2016_Jan_Jun_modified_n.xlsx'.format(path))
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2016_Jul_Dec_modified_n.xlsx'.format(path))
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2017_Jan_Jun_modified_n.xlsx'.format(path))
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2017_Jul_Dec_modified_n.xlsx'.format(path))
#writer = pd.ExcelWriter('{}/EIA930_BALANCE_2018_Jan_Jun_modified_n.xlsx'.format(path))
writer = pd.ExcelWriter('{}/EIA930_BALANCE_2018_Jul_Dec_modified_n.xlsx'.format(path))
df1 = pd.DataFrame(jul_dec_2015_m)
df1.to_excel(writer,sheet_name='Sheet 1',columns=['UTC Time at End of Hour','Balancing Authority','Demand (MW)','Demand_org (MW)','Demand Forecast (MW)','UTC_h','UTC_date','adjust','Label1'],header=True,index=False)
writer.save()

#####-----count the code running time-----
end=datetime.datetime.now()
#select['d']=0
## summary data inforamtion
#for i in range(len(BAs)):
#    cc=np.where(jul_dec_2015_m['Balancing Authority']==BAs[i])
#    cc=(np.array(cc,dtype=int)).transpose()
#    select=jul_dec_2015_m.iloc[cc[:,0]]
#    select=select.reset_index()
#    dd=np.where(select['Label2']=='nan')
#    dd=(np.array(dd,dtype=int)).transpose()
#    for ii in range(len(dd)):
#        print(ii)
#        select['d'].iloc[ii+1]=select['index'].iloc[ii+1]-select['index'].iloc[ii]
    
    


## simple plot the result
# import matplotlib.pyplot as plt
# gb_2015_sum = jul_dec_2015_m.groupby(['UTC Time at End of Hour'])["Demand (MW)"].sum()
# plt.plot(gb_2015_sum)

#a=a.apply(lambda x: math.log(x,math.e))
#for i in range(len(BAs)):
#    for j in range(24):
#    a=jul_dec_2015_m[(jul_dec_2015_m['Balancing Authority']==BAs[i])&(jul_dec_2015_m['UTC_h']==j)]
#    plt.hist(a['Demand (MW)'], color = 'blue', edgecolor = 'black', bins = int(180/5))
    #a=a['Demand (MW)'].apply(lambda x: math.log(x,math.e))
#plt.hist(sum_2015_jul, color = 'blue', edgecolor = 'black', bins = int(180/5))