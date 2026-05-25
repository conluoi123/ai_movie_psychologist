# Sử dụng image Python chuẩn và nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong Docker
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào Docker
# (Bao gồm cả backend, frontend, chromadb và model)
COPY . .

# Hugging Face Spaces yêu cầu mở cổng 7860
EXPOSE 7860

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1
# Đọc biến môi trường từ Secret của Hugging Face (sẽ cấu hình trên Web sau)
# ENV GEMINI_API_KEY="..."

# Di chuyển vào thư mục backend trước khi chạy để code python nhận diện đúng đường dẫn 'app...'
WORKDIR /app/backend

# Lệnh khởi chạy server FastAPI (bây giờ chạy từ trong backend)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
