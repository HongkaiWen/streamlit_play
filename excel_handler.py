import streamlit as st
import pandas as pd
import numpy as np


def get_column_type(series):
    # 先尝试判断是否为日期或时间日期类型
    try:
        pd.to_datetime(series, errors='raise')
        if series.astype(str).str.contains(' ').any():
            return '时间日期类型'
        return '日期类型'
    except (ValueError, TypeError):
        pass

    # 判断是否为数字类型
    if pd.to_numeric(series, errors='coerce').notnull().all() and np.issubdtype(
            pd.to_numeric(series, errors='coerce').dtype, np.number):
        return '数字类型'

    # 其他情况为文本类型
    return '文本类型'


# 设置页面标题
st.title('Excel 文件列信息与前 10 行数据展示')

# 上传 Excel 文件
uploaded_file = st.file_uploader("请上传 Excel 文件", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # 读取 Excel 文件
        df = pd.read_excel(uploaded_file)

        # 获取列名和对应的基本类型
        column_info = {
            '列名': df.columns.tolist(),
            '基本类型': [get_column_type(df[col]) for col in df.columns]
        }
        column_info_df = pd.DataFrame(column_info)

        # 展示列信息
        st.subheader('Excel 文件各列及对应基本类型信息')
        st.dataframe(column_info_df)

        # 展示前 10 行数据
        st.subheader('表格的前 10 行数据')
        st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"处理文件时出现错误: {e}")
