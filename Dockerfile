# 使用 Python 基础镜像
FROM python:3.9-slim

RUN mkdir /log

# 设置工作目录
WORKDIR /app

# 复制项目依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码到工作目录
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 定义环境变量，允许外部访问
ENV STREAMLIT_SERVER_ALLOW_RUN_ON_ROOT=true

# 运行 Streamlit 应用
CMD ["streamlit", "run", "index.py"]