import streamlit as st

def main():
    st.title("照片上传与处理应用")

    # 创建一个文件上传器，accept_multiple_files=False 表示只接受单个文件
    uploaded_file = st.file_uploader("请上传一张照片", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

    if uploaded_file is not None:
        # 当文件上传成功时，显示上传的图片
        st.image(uploaded_file, caption='上传的照片', use_column_width=True)

        # 后续可以在这里添加对照片的处理逻辑，例如图像识别、裁剪等
        # 这里只是简单打印一条消息
        st.write("你已成功上传照片，后续可以对其进行进一步处理。")


if __name__ == "__main__":
    main()
    
