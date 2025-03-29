import streamlit as st
import pandas as pd

# 标题与文本
st.title("销售数据分析仪表盘")
st.write("数据来源：2023年季度报告")

# 文件上传
uploaded_file = st.file_uploader("上传销售数据", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # 交互式组件
    selected_product = st.selectbox("选择产品", df["产品"].unique())

    # 数据可视化
    filtered_df = df[df["产品"] == selected_product]
    st.bar_chart(filtered_df, x="月份", y="销售额")