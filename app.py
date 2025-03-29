import streamlit as st
import pandas as pd
import io

# 输入文件上传组件
st.title("数据处理工具")
uploaded_files = st.file_uploader("选择输入文件", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    # 处理文件（示例：合并 CSV）
    dfs = []
    for file in uploaded_files:
        if file.type == "text/csv":
            df = pd.read_csv(file)
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file)
        dfs.append(df)
    result = pd.concat(dfs)

    # 生成输出文件（示例：导出为 CSV）
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False)
    output.seek(0)

    # 下载按钮
    st.download_button(
        label="下载结果文件",
        data=output,
        file_name="result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )