# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header
import ssl
import sys
import pandas as pd
import pymysql
import gc

class SendMail:
    '''
    Python3 全版本兼容的邮件发送类
    '''
    mail_from = ''
    mail_port = ''
    mail_host = ''
    mail_account = ''
    mail_psd = ''

    # 默认企业微信邮箱配置
    mail_58ba = {
        'smtp_host':'smtp.exmail.qq.com',
        'sender_address':'58ba@58ganji.com',
        'sender_display_name': '58经营数据部',
        'sender_port':'465',
        'sender_psd':'ba@6jNj*q'
    }

    def __init__(self, server_info=None):
        '''
        构造函数：初始化邮件服务器信息
        '''
        if server_info is None:
            server_info = self.mail_58ba
        elif not isinstance(server_info, dict):
            print('The \'server_info\' should be a Dict!')
            return

        # 从配置字典读取信息
        self.mail_host = server_info['smtp_host'].strip()
        self.mail_port = int(server_info['sender_port'])
        self.mail_account = server_info['sender_address']
        self.mail_psd = server_info['sender_psd']

        # 发件人格式：strip() 去除 Header.encode() 可能产生的换行符
        encoded_name = Header(server_info['sender_display_name'], 'utf-8').encode().strip()
        self.mail_from = f"{encoded_name} <{self.mail_account}>"

    def SendText(self, mailto_list, mail_tile, mail_content, mailcc_list=None, mailbcc_list=None, attachment_list=None):
        msg = MIMEMultipart('alternative')

        if not isinstance(mail_tile, str):
            mail_tile = str(mail_tile)
        msg['Subject'] = mail_tile
        msg['From'] = self.mail_from

        # 处理抄送、密送、收件人
        if mailcc_list is None:
            mailcc_list = []
        if mailbcc_list is None:
            mailbcc_list = []

        if isinstance(mailcc_list, list):
            msg['Cc'] = ';'.join(mailcc_list)
        else:
            print('mailcc_list must be list!')
            return

        if isinstance(mailbcc_list, list):
            msg['Bcc'] = ';'.join(mailbcc_list)
        else:
            print('mailbcc_list must be list!')
            return

        if isinstance(mailto_list, list):
            msg['To'] = ';'.join(mailto_list)
        else:
            print('mailto_list must be list!')
            return

        msg["Accept-Language"] = "zh-CN"
        msg["Accept-Charset"] = "utf-8"

        # 正文
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))

        # 附件
        if attachment_list is not None and isinstance(attachment_list, list):
            for afile in attachment_list:
                try:
                    fileName = afile[afile.rfind('/')+1:]
                    with open(afile, 'rb') as f:
                        mailfile = MIMEApplication(f.read())
                    mailfile.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', fileName))
                    msg.attach(mailfile)
                except:
                    pass

        # ===================== 兼容旧版 Python 3.6 的核心修复 =====================
        try:
            # 创建 SSL 上下文，兼容旧版 Python
            context = ssl.create_default_context()
            # 不使用 server_hostname 参数，改用 connect 后 login
            server = smtplib.SMTP_SSL(
                host=self.mail_host,
                port=self.mail_port,
                context=context,
                timeout=15
            )

            server.login(self.mail_account, self.mail_psd)
            server.sendmail(self.mail_from, mailto_list + mailcc_list + mailbcc_list, msg.as_string())
            server.close()
            gc.collect()
            print("✅ 邮件发送成功！")

        except Exception as e:
            print(f"❌ 发送失败：{str(e)}")

    def SendTable(self, mailto_list, mail_subject, mail_title, mail_tables, v_date, mailcc_list=None, mailbcc_list=None, attachment_list=None, add_comment=None):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = str(mail_subject)
        msg['From'] = self.mail_from

        # 基础校验
        if not (isinstance(mail_title, list) and isinstance(mail_tables, list) and isinstance(v_date, list)):
            print("参数必须是列表")
            return
        if len(mail_title) != len(mail_tables) or len(mail_tables) != len(v_date):
            print("列表长度不一致")
            return

        # 处理抄送、收件人
        if mailcc_list is None: mailcc_list = []
        if mailbcc_list is None: mailbcc_list = []
        msg['Cc'] = ';'.join(mailcc_list)
        msg['Bcc'] = ';'.join(mailbcc_list)
        msg['To'] = ';'.join(mailto_list)

        msg["Accept-Language"] = "zh-CN"
        msg["Accept-Charset"] = "utf-8"

        # HTML 模板
        html_head = '''
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>经分邮件报表</title>
        <body>
        <div>
        <p style="font-size:20px;text-align:center"><strong>'''
        html_title = '''</strong></p>
        <p><strong>数据日期:</strong>'''
        html_version = '''</p>
        <table width="1200" border="1" bordercolor="black" cellspacing="2">
        <tr>'''
        html_tail = '''</table>
        <p><strong>备注：</strong>''' + str(add_comment) + '''</p>
        </body></html>'''

        # 拼接表格
        for title, df, dt in zip(mail_title, mail_tables, v_date):
            html = html_head + title + html_title + str(dt) + html_version
            # 表头
            for col in df.columns:
                html += f'<td style="background:#66ccff;font-size:17px;text-align:center"><strong>{col}</strong></td>'
            html += '</tr>'
            # 内容
            for i, (idx, row) in enumerate(df.iterrows()):
                bg = '#e0f3ff' if i%2==0 else '#f1f7f9'
                html += f'<tr style="background:{bg};font-size:15px">'
                for val in row:
                    html += f'<td><strong>{val}</strong></td>'
                html += '</tr>'
            html += html_tail
            msg.attach(MIMEText(html, 'html', 'utf-8'))

        # ===================== 兼容旧版 Python 3.6 的核心修复 =====================
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                host=self.mail_host,
                port=self.mail_port,
                context=context,
                timeout=15
            )
            server.login(self.mail_account, self.mail_psd)
            server.sendmail(self.mail_from, mailto_list + mailcc_list + mailbcc_list, msg.as_string())
            server.close()
            gc.collect()
            print("✅ HTML表格邮件发送成功！")
        except Exception as e:
            print(f"❌ 发送失败：{str(e)}")
class FileDialog:
    '''

    '''
    def __init__(self):

        '''
        '''
    def GetFiles(self):
        from PyQt4 import QtGui
        QtGui.QApplication(sys.argv)
        FilenNames=QtGui.QFileDialog.getOpenFileName(caption=str('选择文件'),directory=r'c:',filter="All(*.*)")
        return FilenNames

    def GetPath(self):
        from PyQt4 import QtGui
        dir_path=QtGui.QFileDialog.getExistingDirectory(caption=str('选择文件夹'),directory=r'C:')
        return dir_path

class DbMgmt:
    '''
            本类记录常用的SQL连接配置，并根据传入的sql进行语句查询，并以pandas的DataFrame的方式返回查询结果
       目前如何使用错误代码尚未研究清楚，下一步需进一步研究如何正确监控类的函数执行中抛出的异常。
   pymysql.connect()函数的参数也需要进一步研究，目前支持哪些参数尚不完全确认。
   目前发现指定Charset为utf8格式能够有效避免查询结果中的中文乱码问题。
    '''
    conn_ba_db={'user':'wuser_ba',
        'password':'58ganji@BAsql110',
        'host':'bareports.58dns.org',
        'port':13356,
        'charset':'utf8'}
    conn_ba={'user':'wuser_ba',
        'password':'58ganji@BAsql110',
        'host':'bareports.58dns.org',
         #'db':'test', 可以指定库信息或者更灵活的方式是在SQL中指定，但是DataFrame插入数据时，由于name字段不支持指定库名，需要提前在连接信息中指定
        'port':13356,
        'charset':'utf8'}
    conn_flow={'user':'jirongdi',
        'password':'MIwbtefvfnUwe&',
        'host':'10.126.84.133',
        'port':5029,
        'charset':'utf8'}
    conn_flow_130={'user':'gaojibin',
        'password':'MIwbgjimdUwe&',
        'host':'10.126.84.130',
        'port':5029,
        'charset':'utf8'}
    conn_chr={'user':'pmctestuser',
        'password':'w65i#lRny&tgh&#d8t',
        'host':'10.126.96.21',
        'port':58886,
        'charset':'utf8'}
    conn_dp={'user':'hdp_fin_ba',
        #'password':'batest149',
        'host':'hiveserver.58dns.org',
        'port':10000,
        'auth_mechanism':'PLAIN'}
    conn_cq={'user':'ba_hive',
        'password':'jfcqtableau123*',
        'host':'10.126.81.219',
        'port':10000,
        'auth_mechanism':'PLAIN'}
    conn_cq_kylin='kylin://amortize_mbbi_income:fclf91nagd13@kylin2.58dns.org:80/roc_ba_mbbi_project?version=v1'
    conn_yc_kylin='kylin://hdp_fin_ba:yFpDmIFDBg@kylin2.olap.58dns.org:80/roc_ba_mbbi_project?version=v1'
    conn_dp_anjuke_bi={'user':'hdp_anjuke_bi',
        #'password':'batest149',
        'host':'hiveserver.58dns.org',
        'port':10000,
        'auth_mechanism':'PLAIN'}
    conn_dp_xxzl={'user':'hdp_ubu_xxzl',
        'host':'hiveserver.58dns.org',
        'port':10000,
        'auth_mechanism':'PLAIN'}
    conn_ba_mbbi={'user':'aplus_admin',
        'password':'007f5630526da559',
        'host':'test1263.db.58dns.org',
        'port':23610,
        'charset':'utf8'}
    conn_dorisDB_config = {
        "user": "hdp_bic_bd_rw",
        "password": "ZqTffINP2H",
        "host": "sr-cdb-sync-1490-1-jdbc.58dns.org",
        "port": 9030,
        "charset": "utf8"
    }

    conn_gr_db = {
        "user": "db58tegmddp_priv",
        "password": "10177b7f4a24bf2e",
        "host": "db58tegmddp.db.58dns.org",
        "port": 15500,
        "charset": "utf8"
        }

# describe formatted
    def __init__(self):

        print('Class is established!')


    def QueryResult(self,sqlquery,conn_config,database_type,index_colm=None):

        try:
            try:
                if database_type=='hive':
                    import impala.dbapi as hive
                    sql_connection=hive.connect(**conn_config)
                elif database_type=='mysql':
                    mysql_config = dict(conn_config)
                    mysql_config.setdefault('connect_timeout', 30)
                    mysql_config.setdefault('read_timeout', 300)
                    mysql_config.setdefault('write_timeout', 30)
                    sql_connection=pymysql.connect(**mysql_config)
                else:
                    print('Database_type should be hive or mysql!')
                    return
                print('Connection is ok!')
                if index_colm is None:
                    print('Ready to read Data!')
                    return pd.read_sql(sqlquery,con=sql_connection)
                    print('Data is loaded!')
                else:
                    print('Ready to read Data!')
                    return pd.read_sql(sqlquery,con=sql_connection,index_col=index_colm)
                    print('Data is loaded!')
            finally:
                sql_connection.close()
                gc.collect()
                print('Connection closed!')
        except Exception as general_err:
            print('An error is encountered:\n',general_err)
    def InsertDFrame(self,dataframe,table_name,table_exists,conn_config,sql_flavor,chunk_size):
        try:
            try:
                if dataframe is None and table_name is None and table_exists is None and conn_config is None and sql_flavor is None and chunk_size is None:
                    print('Parameters Missing,please check!')
                else:
                    sql_connection=pymysql.connect(**conn_config)
                    dataframe.to_sql(name=table_name, con=sql_connection, flavor=sql_flavor, if_exists=table_exists, chunksize=chunk_size)
                    print('Data was inserted to %s successfully!',table_name)
            finally:
                gc.collect()
                sql_connection.close()
        except Exception as general_err:
            print('An error is encountered:\n',general_err)
    def update(self,conn_config,sql_flavor):
        try:
            try:
                if conn_config is None and sql_flavor is None:
                    print('Parameters Missing,please check!')
                else:
                    sql_connection = pymysql.connect(**conn_config)
                    my_cousor = sql_connection.cursor()
                    my_cousor.execute(sql_flavor)
                    sql_connection.commit()
                    print('Data was updated to successfully!')
            finally:
                my_cousor.close()
                gc.collect()
                sql_connection.close()
        except Exception as general_err:
            print('An error is encountered:\n',general_err)
    def SpecialQuery(self,sqlquery,conn_config,para=None):
        try:
            try:
                import impala.dbapi as hive
                sql_connection= hive.connect(**conn_config)
                cursor = sql_connection.cursor()
                print('Connection is ok!')
                if para is not None:
                  cursor.execute(para)
                print('Ready to read Data!')
                cursor.execute(sqlquery)
                column_names = []
                for column in cursor.description:
                  column_name = column[0]
                  column_names.append(column_name)
                result=cursor.fetchall()
                df=pd.DataFrame(result,columns=column_names)
                print('Data is loaded!')
                return df
            finally:
                sql_connection.close()
                gc.collect()
                print('Connection closed!')
        except Exception as general_err:
            print('An error is encountered:\n',general_err)
    def KylinQuery(self,sqlquery,conn_config):
        import sqlalchemy as sa
        kylin_engine = sa.create_engine(conn_config)
        results = kylin_engine.execute(sqlquery)
        a=[e for e in results]
        df=pd.DataFrame(a)
        return df
    def InsertDataFrame(self,dataframe,table_name,table_exists,conn_config,chunk_size):
         import sqlalchemy as sa
         engine=sa.create_engine('mysql+pymysql://%s:%s@%s:%s/%s' %('wuser_ba','58ganji@BAsql110','10.126.93.226','58885','dbwww58com_ba_reports'), encoding="utf-8",echo=True)
         dataframe.to_sql(name=table_name, schema='dbwww58com_ba_reports', con=engine, if_exists=table_exists, chunksize=chunk_size, index=False)
    #20211209新增dorisDB查询
    def DorisDBQuery(self,sql,config):
        # connect to doris
        try:
            cnx = pymysql.connect(**config)
        except:
            print("connect to doris failed")
            exit(1)
        print("connect to doris successfully")
        cursor = cnx.cursor()
        # query data
        try:
            cursor.execute(sql)
            column_names = []
            for column in cursor.description:
              column_name = column[0]
              column_names.append(column_name)
            result=cursor.fetchall()
            df=pd.DataFrame(list(result),columns=column_names)
            print("query data successfully")
            return df
        except:
            print("query data failed")
            exit(1)
        finally:
            cnx.close()
            print('Connection closed!')
    #20211222新增hive表删除
    def SpecialDrop(self,sqlquery,conn_config,para=None):
        try:
            try:
                import impala.dbapi as hive
                sql_connection= hive.connect(**conn_config)
                cursor = sql_connection.cursor()
                print('Connection is ok!')
                if para is not None:
                  cursor.execute(para)
                print('Ready to read Data!')
                cursor.execute(sqlquery)
                print('sql已执行成功')
            finally:
                sql_connection.close()
                gc.collect()
                print('Connection closed!')
        except Exception as general_err:
            print('An error is encountered:\n',general_err)
