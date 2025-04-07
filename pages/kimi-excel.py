import streamlit as st
import pandas as pd
from openai import OpenAI
import json

# 设置页面布局
st.set_page_config(layout="wide")

# 设置页面标题和副标题
st.title("LLM-EXCEL")
st.markdown("上传excel，基于excel中已有的信息，通过自然语言提取生成新的列。")

# 提示 Kimi AppKey 获取方式
st.markdown("**Kimi AppKey 获取方式**：访问 [Moonshot AI 官方网站](https://platform.moonshot.cn/console/) 注册开发者账户，在账户中生成 API 密钥作为 AppKey。")

# 文件上传，仅允许上传 Excel 文件
uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])

if uploaded_file:
    try:
        # 读取 Excel 文件
        df = pd.read_excel(uploaded_file)

        # 预览前 10 行数据
        st.subheader("文件数据预览（前 10 行）")
        st.dataframe(df.head(10))

        # 分两列布局输入框
        col1, col2 = st.columns(2)
        with col1:
            # Kimi AppKey 输入框
            app_key = st.text_input("Kimi AppKey")
        with col2:
            # 提示词输入框
            prompt = st.text_input("提示词")

        # 新列名称输入框
        new_column_name = st.text_input("新列名称")

        # 确定按钮
        if st.button("确定"):
            if app_key and prompt and new_column_name:
                try:
                    # 创建 OpenAI 客户端
                    client = OpenAI(
                        api_key=app_key,
                        base_url="https://api.moonshot.cn/v1"
                    )

                    # 定义生成新列内容的函数
                    def generate_new_column(row):
                        # 构建完整的上下文信息，包含列名和列内容
                        context = " ".join([f"{col}: {val}" for col, val in row.items()])
                        full_prompt = f"{prompt}，根据以下信息生成结果：{context}。请以 JSON 格式返回结果，例如：{{\"result\": \"具体结果\"}}"
                        try:
                            # 调用 Kimi 模型生成回答
                            completion = client.chat.completions.create(
                                model="moonshot-v1-8k",
                                messages=[
                                    {"role": "system", "content": "以指定的 JSON 格式返回结果，无需多余解释和铺垫。"},
                                    {"role": "user", "content": full_prompt}
                                ],
                                temperature=0.3
                            )
                            # 获取回答内容
                            result_str = completion.choices[0].message.content
                            try:
                                result_json = json.loads(result_str)
                                return result_json.get("result", None)
                            except json.JSONDecodeError:
                                st.error(f"无法解析 Kimi 返回的 JSON 数据: {result_str}")
                                return None
                        except Exception as e:
                            st.error(f"调用 Kimi 模型时出错: {e}")
                            return None

                    # 应用函数生成新列
                    df[new_column_name] = df.apply(generate_new_column, axis=1)

                    # 显示生成后的 DataFrame
                    st.subheader("生成后的文件数据")
                    st.dataframe(df)

                    # 将 DataFrame 保存为 Excel 文件并提供下载链接
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    output.seek(0)

                    st.download_button(
                        label="下载生成后的文件",
                        data=output,
                        file_name="generated_file.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"处理文件时出错: {e}")
            else:
                st.warning("请确保填写了 Kimi AppKey、提示词和新列名称。")
    except Exception as e:
        st.error(f"读取文件时出错: {e}")