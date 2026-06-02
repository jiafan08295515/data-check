# -*- coding: utf-8 -*-
'''
Created on 2017年10月13日

@author: gaojibin
'''
import pandas as pd 
import datetime
import time



class MyDataFrame():
    df1 = pd.DataFrame({'user_id':['1001', '1002', '1003', '1004'],'day_price': ['100', '200', '300', '400']})
    df2 = pd.DataFrame({'user_id':['1001', '1002', '1003', '1005'],'day_price': ['100', '200', '300', '500']})
    
    def __init__(self):
        pass
    
    def diffDataFrame(self,dataFrame,string_left,string_right,num_digit,num_threshold):
        dataFrame=dataFrame.where(dataFrame.notnull(), None)
        dataFrame['diff']=None
        dataFrame['flag']=None
        for i in range(0, len(dataFrame.index)):
            if dataFrame.loc[i,string_left]!=None and dataFrame.loc[i,string_right]!=None:
                dataFrame.loc[i,'diff']=round(float(dataFrame.loc[i,string_left])-float(dataFrame.loc[i,string_right]),num_digit)
                if abs(dataFrame.loc[i,'diff'])>num_threshold:
                    dataFrame.loc[i,'flag']=1
                else:
                    dataFrame.loc[i,'flag']=0
            elif dataFrame.loc[i,string_left]==None and dataFrame.loc[i,string_right]==None:
                dataFrame.loc[i,'flag']=0
            elif dataFrame.loc[i,string_left]==None and dataFrame.loc[i,string_right]==0:
                dataFrame.loc[i,'flag']=0
            elif dataFrame.loc[i,string_left]==0 and dataFrame.loc[i,string_right]==None:
                dataFrame.loc[i,'flag']=0
            else:
                dataFrame.loc[i,'diff']=None
                dataFrame.loc[i,'flag']=1
        dataFrame=dataFrame[dataFrame['flag'].isin([1])]
        dataFrame=dataFrame.drop('flag',1)
        return dataFrame
                
    def specialDataFrame(self,dataFrame,string):
        print(string)
        dataFrame=dataFrame.where(dataFrame.notnull(),None)
        print(1)
        dataFrame=dataFrame.dropna(subset=['stat_date'])
        print(2)
        dataFrame['flag']=None
        for i in range(0, len(dataFrame.index)):
#            print dataFrame.iloc[i,3]
            service_begin_date=datetime.datetime.strptime(dataFrame.iloc[i,3],'%Y-%m-%d').date()
#            print dataFrame.iloc[i,4]
            service_end_date=datetime.datetime.strptime(dataFrame.iloc[i,4],'%Y-%m-%d').date()
#            print dataFrame.iloc[i,5]
            v_date=datetime.datetime.strptime(dataFrame.iloc[i,5],'%Y-%m-%d').date()
            if service_begin_date<=v_date and service_end_date>=v_date:
                dataFrame.loc[i,'flag']=0
        dataFrame=dataFrame.dropna(subset=['flag'])
        dataFrame_new=dataFrame.groupby(['user_id','sign_city_name','city_type','service_begin_dt','service_end_dt','pay_type','cate1','cate2'])['num'].sum()
        dataFrame=dataFrame_new.reset_index()
        dataFrame.columns=['user_id','sign_city_name','city_type','service_begin_dt','service_end_dt','pay_type','cate1','cate2','num']        
        print(string+'结束')
        return dataFrame
