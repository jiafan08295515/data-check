# -*- coding: utf-8 -*-
#####GR大屏数据监控
import sys
import Myspace3 as ms
from MyThread import *
import datetime 
import pandas as pd
import numpy as np
import MyDataFrame as md

mn=datetime.date.today().replace(day=1).strftime("%Y-%m")
last_month = (datetime.date.today().replace(day=1) - datetime.date.resolution).strftime("%Y-%m")
print(last_month)
two_month_ago = (((datetime.date.today().replace(day=1) - datetime.date.resolution)
                 ).replace(day=1) - datetime.date.resolution).strftime("%Y-%m")

# 数据最大日期查询
sql01 = '''
select 'app_gr_overview_data_mn' as table_name,''as bu,max(mn) as mn from (select mn,count(*) as cn  from   db58_db58_teg_mddp.app_gr_overview_data_mn where  mn >='''+"'"+two_month_ago+"'"+''' group by mn) t where t.cn=13
union all 
select 'app_gr_aunt_portrayal_tag_mn' as table_name,'' as bu,max(partition_dt) as mn from db58_db58_teg_mddp.app_gr_aunt_portrayal_tag_mn  where  partition_dt >='''+"'"+two_month_ago+"'"+'''
union all
select 'app_gr_work_city_flow_mn' as table_name,'' as bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_work_city_flow_mn where  mn >='''+"'"+two_month_ago+"'"+''' 
union all
select 'app_gr_work_portrayal_mn' as table_name,'' as bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_work_portrayal_mn where  mn >='''+"'"+two_month_ago+"'"+'''
union all
select 'app_gr_work_post_salary_mn' as table_name,'' as bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_work_post_salary_mn where  mn >='''+"'"+two_month_ago+"'"+''' 
union all
select 'app_gr_training_course_mn' as table_name,'' as bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_training_course_mn where  mn >='''+"'"+two_month_ago+"'"+'''
union all
select 'app_gr_comfortable_house_mn' as table_name,bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_comfortable_house_mn where  mn >='''+"'"+two_month_ago+"'"+''' group  by  bu
union all
select 'app_gr_car_data_mn' as table_name,'' as bu,max(mn) as mn from db58_db58_teg_mddp.app_gr_car_data_mn where  mn >='''+"'"+two_month_ago+"'"+'''
 '''
db = ms.DbMgmt()
mdf = md.MyDataFrame()
sendmail = ms.SendMail()
table_name = ""
df=pd.DataFrame()
user_list=['jiafan02@58.com']
#读取数据并开启多线层
#thread01 = MyThread(db.SpecialQuery,
#                    args=(sql01, db.conn_dp, "set mapreduce.job.queuename=root.offline.hdp_fin_ba.explorer"))
thread01 = MyThread(db.QueryResult,args=(sql01, db.conn_gr_db, 'mysql'))
thread01.start()
thread01.join()
df01 = thread01.get_result()
print(df01)
# 写入 MySQL
db_mysql = ms.DbMgmt()
df_mysql = df01[['table_name', 'bu', 'mn']].copy()
df_mysql.rename(columns={'mn': 'max_mn'}, inplace=True)
df_mysql['update_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

##db_mysql.update(db_mysql.conn_gr_db, 'delete from  db58_db58_teg_mddp.app_gr_check_max_date_mn')
# 写入 MySQL 结果表（先 UPDATE，无匹配则 INSERT）
for _, row in df_mysql.iterrows():
    update_sql = (
        "UPDATE db58_db58_teg_mddp.app_gr_check_max_date_mn "
        "SET max_mn='" + str(row['max_mn']) + "', update_time='" + str(row['update_time']) + "' "
        "WHERE table_name='" + str(row['table_name']) + "' AND bu='" + str(row['bu']) + "'"
    )
    db_mysql.update(db_mysql.conn_gr_db, update_sql)
    insert_sql = (
        "INSERT INTO db58_db58_teg_mddp.app_gr_check_max_date_mn "
        "(table_name, bu, max_mn, update_time) "
        "SELECT '" + str(row['table_name']) + "', '" + str(row['bu']) + "', "
        "'" + str(row['max_mn']) + "', '" + str(row['update_time']) + "' "
        "FROM DUAL "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM db58_db58_teg_mddp.app_gr_check_max_date_mn "
        "WHERE table_name='" + str(row['table_name']) + "' AND bu='" + str(row['bu']) + "')"
    )
    db_mysql.update(db_mysql.conn_gr_db, insert_sql)
# 逐行检查 mn 是否等于 last_month
abnormal_rows = df01[df01['mn'] != last_month]
print(last_month)
print(abnormal_rows)
if len(abnormal_rows) > 0:
    # 有异常：构建 DataFrame 用于 HTML 表格邮件
    abnormal_df = abnormal_rows[['table_name', 'bu', 'mn']].copy()
    abnormal_df.rename(columns={
        'table_name': '表名',
        'bu': 'BU',
        'mn': '最大日期'
    }, inplace=True)
    abnormal_df.reset_index(drop=True, inplace=True)

    sendmail.SendTable(
        mailto_list=user_list,
        mail_subject='【GR大屏数据异常】GR大屏数据更新异常',
        mail_title=[last_month + '月份 以下数据更新异常，请及时处理'],
        mail_tables=[abnormal_df],
        v_date=['数据日期: ' + last_month],
        add_comment=['异常标准：最大日期 ≠ ' + last_month]
    )
    exit(1)
else:
    sendmail.SendText(mailto_list=user_list, mail_tile='【GR大屏数据正常】GR大屏数据正常',
                      mail_content=last_month + '月份' + ' 数据更新无异常!' + '\n' + '大吉大利,今晚吃鸡!',
                      attachment_list=[])
