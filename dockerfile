# 使用 Python 3.9 基础镜像
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 注意：Pygame 是图形程序，直接 docker run 会报错找不到 Display
# 这里我们通常只用它来跑逻辑测试或者配合 Dev Containers 映射显示器
CMD ["python", "main.py"]