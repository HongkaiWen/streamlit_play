import streamlit as st
import pandas as pd
import io
from openai import OpenAI
import re


# 调用 Kimi 大模型生成代码
def call_kimi(table_structures, user_prompt, app_key):
    client = OpenAI(
        api_key=app_key,
        base_url="https://api.moonshot.cn/v1"
    )

    # 构建完整的提示信息
    table_info = "\n".join([f"表 {i + 1} 的结构：{str(structure)}" for i, structure in enumerate(table_structures)])
    full_prompt = f"请根据以下表结构和处理需求生成 Pandas 代码。\n{table_info}\n处理需求：{user_prompt}。请仅返回可执行的 Python 代码，使用 Pandas 库，代码假设已有数据框 df0, df1, ... 对应各个表，最后将结果存储在名为 'result' 的数据框中。"

    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system",
                 "content": "仅返回可执行的 Python 代码，使用 Pandas 库，代码假设已有数据框 df0, df1, ... 对应各个表，最后将结果存储在名为 'result' 的数据框中。"},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3
        )
        code = completion.choices[0].message.content
        return code
    except Exception as e:
        st.error(f"调用 Kimi 模型时出错：{e}")
        return None


# 预处理代码，提取有效 Python 代码
def preprocess_code(code):
    # 去除可能的代码块标记（如 ```python 和 ```）
    code = re.sub(r'```python', '', code)
    code = re.sub(r'```', '', code)
    # 去除多余的空行和前后空格
    code_lines = [line.strip() for line in code.splitlines() if line.strip()]
    return '\n'.join(code_lines)


# 将数据类型转换为通俗易懂的描述
def convert_dtype(dtype):
    if 'int' in str(dtype):
        return '整数'
    elif 'float' in str(dtype):
        return '小数'
    elif 'object' in str(dtype):
        return '文本'
    elif 'bool' in str(dtype):
        return '布尔值（真/假）'
    elif 'datetime' in str(dtype):
        return '日期时间'
    else:
        return str(dtype)


# 主程序
def main():
    st.title("Excel 数据处理应用")

    # 提示 Kimi AppKey 获取方式
    st.markdown(
        "<p style='text-align: center; color: #666;'>**Kimi AppKey 获取方式**：访问 <a href='https://platform.moonshot.cn/console/' target='_blank'>Moonshot AI 官方网站</a> 注册开发者账户，在账户中生成 API 密钥作为 AppKey。</p>",
        unsafe_allow_html=True)

    # 输入 Kimi AppKey
    app_key = st.text_input("输入 Kimi AppKey")

    # 上传多个 Excel 文件
    uploaded_files = st.file_uploader("上传 Excel 文件", type=["xlsx"], accept_multiple_files=True)

    if uploaded_files:
        if not app_key:
            st.warning("请输入有效的 Kimi AppKey 以调用模型。")
            return

        # 获取表结构
        table_structures = []
        dataframes = []
        for i, file in enumerate(uploaded_files):
            try:
                df = pd.read_excel(file)
                dataframes.append(df)
                # 获取列名和数据类型
                columns = df.columns.tolist()
                dtypes = df.dtypes.tolist()
                # 转换数据类型为通俗易懂的描述
                readable_dtypes = [convert_dtype(dtype) for dtype in dtypes]
                table_structure = pd.DataFrame({
                    '列名': columns,
                    '数据类型': readable_dtypes
                })
                table_structures.append(table_structure)
                st.write(f"文件 {i + 1} 的表结构：")
                st.table(table_structure)
            except Exception as e:
                st.error(f"读取文件 {file.name} 时出错：{e}")
                return

        # 用户输入处理描述
        user_prompt = st.text_area("描述要对数据进行的处理：")

        if st.button("生成并执行代码"):
            if not user_prompt:
                st.warning("请输入要对数据进行处理的描述。")
                return

            # 调用 Kimi 模型生成代码
            code = call_kimi(table_structures, user_prompt, app_key)
            if code:
                # 预处理代码
                clean_code = preprocess_code(code)
                st.write("生成并预处理后的代码：")
                st.code(clean_code)

                try:
                    # 执行生成的代码
                    local_vars = {'pd': pd}
                    for i, df in enumerate(dataframes):
                        local_vars[f'df{i}'] = df
                    exec(clean_code, globals(), local_vars)
                    result = local_vars.get('result')

                    if result is not None:
                        st.write("处理结果：")
                        st.dataframe(result)

                        # 提供下载链接
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            result.to_excel(writer, index=False)
                        output.seek(0)

                        st.download_button(
                            label="下载处理结果",
                            data=output,
                            file_name="processed_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("执行代码后未得到有效的结果，请检查生成的代码。")

                except Exception as e:
                    st.error(f"执行代码时出错：{e}")


if __name__ == "__main__":
    main()
