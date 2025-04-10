import streamlit as st
import pandas as pd
from io import BytesIO
import traceback


def check_last_two_digits_consecutive(invoice_num):
    try:
        # 提取最后两位数字
        last_two = invoice_num[-2:]
        prefix = invoice_num[:-2]
        if last_two.isdigit():
            num = int(last_two)
            next_num = prefix + str(num + 1).zfill(2)
            prev_num = prefix + str(num - 1).zfill(2)
            return next_num, prev_num
        return None, None
    except IndexError:
        return None, None


def check_consecutive_invoices(df, invoice_column):
    # 把发票号放到一个集合（Python 里集合类似哈希表）里
    invoice_set = set(df[invoice_column].dropna())
    consecutive_indices = set()

    # 遍历原始数据的每一行
    for index, row in df.iterrows():
        invoice_number = row[invoice_column]
        if pd.notna(invoice_number):
            try:
                next_invoice, prev_invoice = check_last_two_digits_consecutive(invoice_number)
                if next_invoice and prev_invoice:
                    # 检查相邻的发票号是否在集合中
                    if next_invoice in invoice_set or prev_invoice in invoice_set:
                        consecutive_indices.add(index)
            except Exception as e:
                error_message = f"处理发票号 {invoice_number} 时出现错误：{str(e)}"
                stack_trace = traceback.format_exc()
                print(error_message)
                print(stack_trace)

    # 根据索引获取连号发票对应的行数据
    consecutive_data = df.loc[list(consecutive_indices)]
    # 按照发票号排序
    consecutive_data = consecutive_data.sort_values(by=invoice_column)
    return consecutive_data


def make_clickable(url):
    return f'<a href="{url}" target="_blank">发票链接</a>'


def main():
    st.title("发票连号检查")
    st.write("请上传包含发票信息的 Excel 文件。")

    # 上传文件
    uploaded_file = st.file_uploader("选择一个 Excel 文件", type=["xlsx"])

    if uploaded_file is not None:
        try:
            # 读取 Excel 文件
            df = pd.read_excel(uploaded_file)
            # 获取所有列名
            columns = df.columns.tolist()

            # 尝试找到“发票类别”列的索引
            default_index = columns.index("发票类别") if "发票类别" in columns else 0

            # 第一个下拉框，选择列，默认选中“发票类别”列
            selected_column = st.selectbox("选择列", columns, index=default_index)

            # 获取所选列的去重值
            unique_values = df[selected_column].dropna().unique().tolist()

            # 第二个下拉框，选择去重值，默认全部选中
            selected_values = st.multiselect("选择值", unique_values, default=unique_values)

            # 检查连号发票
            consecutive_data = check_consecutive_invoices(df, "发票号码")

            # 根据所选值筛选数据
            filtered_data = consecutive_data[consecutive_data[selected_column].isin(selected_values)]

            if not filtered_data.empty:
                filtered_data["发票原件地址"] = filtered_data["发票原件地址"].apply(make_clickable)

                st.write("发现连号的发票对应的行信息：")

                preview_columns = ['发票号码', '销售方名称', '价税合计', '开票日期', '关联单据类型', '单据编号',
                                   '发票原件地址', '发票类别', '创建人']

                # 预览最多 10 行
                preview = filtered_data[preview_columns]
                st.write(preview.to_html(escape=False), unsafe_allow_html=True)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_data.to_excel(writer, index=False)
                output.seek(0)

                # 下载按钮
                st.download_button(
                    label="下载所有连号发票的数据",
                    data=output,
                    file_name="consecutive_invoices.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("未发现符合条件的连号发票。")
        except Exception as e:
            error_message = f"处理文件时出现错误：{str(e)}"
            stack_trace = traceback.format_exc()
            st.error(error_message)
            print(stack_trace)


if __name__ == "__main__":
    main()