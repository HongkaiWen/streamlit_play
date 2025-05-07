import streamlit as st
from pdf2docx import Converter
import os
import tempfile

# 左侧目录菜单默认收起
st.set_page_config(initial_sidebar_state="collapsed")
# 添加返回到 index 页面的链接
st.markdown("[返回首页](/)")

# 向用户显示提示信息
st.info("本程序服务端不保留任何用户上传和生成的文件，请放心使用。")

# 添加自定义 CSS 样式
st.markdown(
    """
    <style>
    /* 整体应用样式 */
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
        padding: 3rem;
        background-color: #f5f5f5;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* 按钮样式 */
    .stButton>button {
        background-color: #2196F3;
        color: white;
        border-radius: 25px;
        font-size: 18px;
        padding: 12px 30px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #1976D2;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* 文件上传组件样式 */
    .stFileUploader {
        margin-bottom: 30px;
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* 文本输入框样式 */
    .stTextInput {
        margin-bottom: 30px;
    }

    /* 标题样式 */
    h1 {
        color: #2196F3;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* 子标题样式 */
    h3 {
        color: #333;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def pdf_to_word(pdf_file, word_file):
    cv = Converter(pdf_file)
    cv.convert(word_file, start=0, end=None)
    cv.close()

st.title('📄 PDF 转 Word 工具')

# 让用户上传 PDF 文件
st.markdown("### 步骤 1: 选择 PDF 文件")
uploaded_file = st.file_uploader("点击下方按钮选择一个 PDF 文件", type="pdf")

if uploaded_file is not None:
    # 移除生成唯一标识的代码
    # unique_id = str(int(time.time() * 1000))
    # 自动生成输出的 Word 文件名，不添加唯一标识
    output_filename = os.path.splitext(uploaded_file.name)[0] + '.docx'
    
    st.markdown("### 步骤 2: 输出文件名已自动生成")
    st.write(f"输出的 Word 文件名: {output_filename}")
    
    # 开始转换按钮
    st.markdown("### 步骤 3: 开始转换")
    if st.button('🚀 开始转换'):
        temp_pdf = None
        try:
            # 创建临时文件
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_pdf.write(uploaded_file.read())
            temp_pdf.close()

            with open(output_filename, 'wb') as f:
                pdf_to_word(temp_pdf.name, f)
            
            st.success(f'🎉 转换成功！文件已保存为 {output_filename}')

            # 提供下载链接
            with open(output_filename, "rb") as file:
                btn = st.download_button(
                    label="📥 点击下载转换后的文件",
                    data=file,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        except Exception as e:
            st.error(f'❌ 转换失败: {e}')
        finally:
            if temp_pdf is not None and os.path.exists(temp_pdf.name):
                os.unlink(temp_pdf.name)
            try:
                if os.path.exists(output_filename):
                    os.unlink(output_filename)
            except Exception as del_e:
                st.error(f'❌ 删除生成的 Word 文件时出错: {del_e}')