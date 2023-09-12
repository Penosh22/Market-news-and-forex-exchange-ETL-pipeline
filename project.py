from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from GoogleNews import GoogleNews
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2
import datetime as dt
import pandas as pd
from psycopg2 import sql
import requests as re
from bs4 import BeautifulSoup as bs

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "catchup": False,
    "schedule_interval": "@daily"
}

dag = DAG(
    dag_id='market_news_extract',
    schedule_interval=None,
    start_date=days_ago(1),
    schedule=None,
    max_active_runs=180
)

def get_market_highlights():
    googlenews = GoogleNews()
    googlenews.get_news('stock market')  # Adjust the keyword as needed
    news_arr = googlenews.get_texts()
    news=[]

    for i,j in enumerate(news_arr):
        news.append((i,j.replace("'","")))
    print(*news,sep='\n')
    df = pd.DataFrame(news,columns=[0,1])
    mysql_hook= PostgresHook(
    postgres_conn_id = 'postgres_config',
    schema = "airflow_db"
    )    

    for row in range(len(df)):
        sql = f'''INSERT INTO google_news values (
        '{df.iloc[row,0]}','{df.iloc[row,1]}'
        )'''
        mysql_hook.run(sql=sql)

def fetch_forex_data():
    url = "https://economictimes.indiatimes.com/markets/forex"
    response = re.get(url)
    soup = bs(response.text, 'html.parser')
    table = soup.find('table', class_='tblData5')
    tablerows = table.find_all('tr')
    values_list = []
    for tr in tablerows[1:]:
        data = tr.find_all('td')
        values = []
        for td in data[0:7]:
            value = td.text.strip()
            values.append(value)
        values_list.append(values)

    df1= pd.DataFrame(values_list,columns=['currency_pair','price','change','percentage_change','OPEN','prev_close','low_high'])
    mysql_hook= PostgresHook(
    postgres_conn_id = 'postgres_config',
    schema = "airflow_db"
    )    
    for row in range(len(df1)):
        sql = f'''INSERT INTO forex_data values (
        '{df1.iloc[row,0]}','{df1.iloc[row,1]}','{df1.iloc[row,2]}','{df1.iloc[row,3]}','{df1.iloc[row,4]}','{df1.iloc[row,5]}','{df1.iloc[row,6]}'
        )'''
        mysql_hook.run(sql=sql)    


get_market_highlights= PythonOperator(
    task_id = "get_market_highlights",
    python_callable= get_market_highlights,
    dag=dag
)

forex_data_task = PythonOperator(
    task_id="get_forex_data",
    python_callable=fetch_forex_data,
    dag=dag
)



get_market_highlights >> forex_data_task
