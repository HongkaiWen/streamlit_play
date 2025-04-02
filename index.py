import streamlit as st
import os

from apscheduler.schedulers.background import BackgroundScheduler

import access_log

st.set_page_config(
    page_title="魔法工具箱",
    page_icon="⚙",
)

st.write("# 欢迎来到魔法工具箱 ⚙️")

st.sidebar.success("请选择一个功能使用")

# 提取环境变量
env_enable_access_log = os.environ.get('ENABLE_ACCESS_LOG')

print(env_enable_access_log)

if env_enable_access_log == 'Y':
    print('start init...')

    # 初始化调度器
    scheduler = BackgroundScheduler()
    # 添加定时任务，每 5 分钟执行一次 save_records_to_excel 函数
    scheduler.add_job(access_log.save_records_to_excel, 'interval', minutes=5)

    print('start init...')

    # 启动调度器
    scheduler.start()

    print('finished init...')

# https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app#convert-an-existing-app-into-a-multipage-app