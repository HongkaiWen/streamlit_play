import streamlit as st
import pandas as pd
from openai import OpenAI
import json
import queue
import threading
from time import time

# 设置页面布局
st.set_page_config(layout="wide")

# 设置页面标题和副标题
st.markdown("<h1 style='text-align: center; color: #336699;'>kimi & excel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>本应用可基于 Excel 文件内容和多个提示词，调用 Kimi 模型生成多个新列内容。</p>", unsafe_allow_html=True)

# 提示 Kimi AppKey 获取方式
st.markdown("<p style='text-align: center; color: #666;'>**Kimi AppKey 获取方式**：访问 <a href='https://platform.moonshot.cn/console/' target='_blank'>Moonshot AI 官方网站</a> 注册开发者账户，在账户中生成 API 密钥作为 AppKey。</p>", unsafe_allow_html=True)

# 选择免费版或收费版
version = st.selectbox("选择版本", ["免费版", "收费版"], index=0)

# 添加一些分隔线和空格，增强视觉效果
st.markdown("<hr>", unsafe_allow_html=True)
st.write("")

# 文件上传，仅允许上传 Excel 文件
uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"], key="file_uploader", help="请上传 Excel 格式的文件")

# 初始化 st.session_state 变量
if 'full_df' not in st.session_state:
    st.session_state.full_df = None
if 'prompts' not in st.session_state:
    st.session_state.prompts = []
if 'new_column_names' not in st.session_state:
    st.session_state.new_column_names = []
if 'app_key' not in st.session_state:
    st.session_state.app_key = ""

if uploaded_file:
    try:
        # 读取 Excel 文件
        df = pd.read_excel(uploaded_file)

        # 预览前 10 行数据
        st.subheader("文件数据预览")
        st.dataframe(df.head(10), use_container_width=True)

        # 添加一些分隔线和空格，增强视觉效果
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("")

        # Kimi AppKey 输入框
        st.session_state.app_key = st.text_input("Kimi AppKey", value=st.session_state.app_key, key="app_key_input", help="请输入有效的 Kimi AppKey")

        # 动态添加提示词和新列名称
        num_prompts = st.number_input("请输入需要生成的新列的数量", min_value=1, value=1, step=1, key="num_prompts_input")
        st.session_state.prompts = []
        st.session_state.new_column_names = []
        for i in range(num_prompts):
            col1, col2 = st.columns(2)
            with col1:
                prompt = st.text_input(f"提示词 {i + 1}", key=f"prompt_{i + 1}_input", help=f"请输入第 {i + 1} 个提示词")
                st.session_state.prompts.append(prompt)
            with col2:
                new_column_name = st.text_input(f"新列名称 {i + 1}", key=f"new_column_{i + 1}_input", help=f"请输入第 {i + 1} 个新列的名称")
                st.session_state.new_column_names.append(new_column_name)

        # 添加一些分隔线和空格，增强视觉效果
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("")

        # 确定按钮
        if st.button("确定", key="submit_button"):
            if st.session_state.app_key and all(st.session_state.prompts) and all(st.session_state.new_column_names):
                try:
                    # 创建 OpenAI 客户端
                    client = OpenAI(
                        api_key=st.session_state.app_key,
                        base_url="https://api.moonshot.cn/v1"
                    )

                    # 定义生成新列内容的函数
                    def generate_new_column(row, prompt):
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

                    # 免费版限制队列
                    def process_requests(request_queue, df, prompts, new_column_names):
                        request_times = []
                        max_requests_per_minute = 3
                        while True:
                            item = request_queue.get()
                            if item is None:
                                break
                            row, prompt, new_column_name = item
                            now = time()
                            # 移除一分钟前的请求记录
                            request_times[:] = [t for t in request_times if now - t < 60]
                            if len(request_times) >= max_requests_per_minute:
                                # 等待直到可以发送新请求
                                while len(request_times) >= max_requests_per_minute:
                                    now = time()
                                    request_times[:] = [t for t in request_times if now - t < 60]
                            result = generate_new_column(row, prompt)
                            df.at[row.name, new_column_name] = result
                            request_times.append(now)
                            request_queue.task_done()

                    # 预览部分（前 1 行）
                    preview_df = df.head(1).copy()
                    if version == "免费版":
                        request_queue = queue.Queue()
                        processing_thread = threading.Thread(target=process_requests, args=(request_queue, preview_df, st.session_state.prompts, st.session_state.new_column_names))
                        processing_thread.start()
                        for prompt, new_column_name in zip(st.session_state.prompts, st.session_state.new_column_names):
                            for _, row in preview_df.iterrows():
                                request_queue.put((row, prompt, new_column_name))
                        request_queue.join()
                        request_queue.put(None)
                        processing_thread.join()
                    else:
                        for prompt, new_column_name in zip(st.session_state.prompts, st.session_state.new_column_names):
                            preview_df[new_column_name] = preview_df.apply(lambda row: generate_new_column(row, prompt), axis=1)

                    # 显示生成后的预览 DataFrame
                    st.subheader("生成后的文件数据预览")
                    st.dataframe(preview_df, use_container_width=True)

                    # 添加一些分隔线和空格，增强视觉效果
                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.write("")

                    # 下载按钮
                    st.session_state.full_df = df.copy()
                    if version == "免费版":
                        request_queue = queue.Queue()
                        processing_thread = threading.Thread(target=process_requests, args=(request_queue, st.session_state.full_df, st.session_state.prompts, st.session_state.new_column_names))
                        processing_thread.start()
                        for prompt, new_column_name in zip(st.session_state.prompts, st.session_state.new_column_names):
                            for _, row in st.session_state.full_df.iterrows():
                                request_queue.put((row, prompt, new_column_name))
                        request_queue.join()
                        request_queue.put(None)
                        processing_thread.join()
                    else:
                        for prompt, new_column_name in zip(st.session_state.prompts, st.session_state.new_column_names):
                            st.session_state.full_df[new_column_name] = st.session_state.full_df.apply(lambda row: generate_new_column(row, prompt), axis=1)

                    st.write("full_df 已成功保存到 session_state")  # 调试信息

                except Exception as e:
                    st.error(f"处理文件时出错: {e}")
            else:
                st.warning("请确保填写了 Kimi AppKey、所有提示词和新列名称。")
    except Exception as e:
        st.error(f"读取文件时出错: {e}")

# 下载完整文件的按钮
if st.session_state.full_df is not None:
    # 将完整 DataFrame 保存为 Excel 文件并提供下载链接
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.full_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="点击下载完整文件",
        data=output,
        file_name="generated_file.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="actual_download_button"
    )