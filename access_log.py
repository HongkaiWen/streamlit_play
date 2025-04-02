import streamlit as st
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os

# 用于存储访问记录的列表，作为内存缓冲区
access_records = []
# 定义锁，确保线程安全
lock = threading.Lock()

log_file_path = '/log/access_log.xlsx'

# 提取环境变量
env_enable_access_log = os.environ.get('ENABLE_ACCESS_LOG')


def log_access(app_name):
    if env_enable_access_log != 'Y':
        return

    """
    记录访问信息到内存缓冲区
    """
    global access_records
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with lock:
        access_records.append([current_time, app_name])


def save_records_to_excel():
    """
    将内存中的访问记录写入 Excel 文件
    """
    global access_records
    with lock:
        if access_records:
            try:
                df = pd.DataFrame(access_records, columns=['访问时间', '应用名称'])
                try:
                    existing_df = pd.read_excel('access_log.xlsx')
                    new_df = pd.concat([existing_df, df], ignore_index=True)
                except FileNotFoundError:
                    new_df = df
                new_df.to_excel('access_log.xlsx', index=False)
                access_records = []  # 清空内存缓冲区
            except Exception as e:
                st.error(f"写入 Excel 文件时出错: {e}")