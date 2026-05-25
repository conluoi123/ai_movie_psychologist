# AI Movie Psychologist (Bác sĩ Tâm lý Điện ảnh)

![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Database-orange)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-green)

**Link test sản phẩm:** [https://huggingface.co/spaces/quoc123kaka/ai-movie-psychologist/tree/main](https://huggingface.co/spaces/quoc123kaka/ai-movie-psychologist/tree/main)

AI Movie Psychologist là một hệ thống Full-stack kết hợp giữa **Generative AI (LLM)**, **Xử lý ngôn ngữ tự nhiên (NLP)** và **Vector Search (RAG)**. Thay vì đề xuất phim theo thể loại cứng nhắc, hệ thống đóng vai trò như một bác sĩ tâm lý: Lắng nghe tâm sự của người dùng, đo lường cảm xúc, và kê một "đơn thuốc" điện ảnh giúp chữa lành hoặc xoa dịu tâm hồn họ.

---

## Motivation (Động lực phát triển)

Các hệ thống gợi ý phim hiện tại (Netflix, IMDB) thường dựa vào lịch sử xem (Collaborative Filtering) hoặc thể loại (Content-based). Tuy nhiên, khi một người đang gặp áp lực công việc hoặc thất tình, họ không tìm kiếm "Phim Hành Động" hay "Phim Hài". Họ tìm kiếm một **cảm giác**.
Dự án này ra đời để giải quyết bài toán đó: **Chuyển hóa cảm xúc trừu tượng thành siêu dữ liệu tìm kiếm cụ thể** bằng cách ứng dụng Prompt Engineering nâng cao và Vector Database.

---

## Tech Stack (Công nghệ sử dụng)

- **Frontend**: HTML5, CSS3 (Glassmorphism & Dark Mode), Vanilla JavaScript.
- **Backend Core**: FastAPI, Uvicorn, Pydantic.
- **Mô hình AI / ML**:
  - **Google Gemini 2.5 Flash**: Phân tích tâm lý & Dịch ngữ cảnh (HyDE).
  - **Hugging Face DistilBERT**: Fine-tune cục bộ để phân loại cảm xúc (Sentiment Classification).
  - **SentenceTransformers (`all-MiniLM-L6-v2`)**: Embedding văn bản.
- **Cơ sở dữ liệu Vector**: ChromaDB.
- **Data Engineering**: Pandas (Tiền xử lý 50.000+ phim từ IMDB).
- **Deployment**: Docker, Hugging Face Spaces.

---

## Kiến trúc Hệ thống (Các Layer)

Hệ thống hoạt động theo luồng **4 Lớp (Layers)** kết hợp tuần tự:

1. **Layer 1: Bắt mạch Cảm xúc (Local Sentiment Service)**
   - Text của user được đưa qua mô hình DistilBERT (đã fine-tune) chạy hoàn toàn ở Local.
   - Nếu phát hiện cảm xúc `Negative` (Tiêu cực), hệ thống tự động đẩy điểm `min_rating` lên mức an toàn (7.5+) để đảm bảo user được xem phim chất lượng cao, tránh làm tồi tệ thêm tâm trạng.

2. **Layer 2: Chuyển ngữ Context (LLM HyDE Translation)**
   - Sử dụng kỹ thuật **HyDE (Hypothetical Document Embeddings)**: Ép Gemini không được dùng các từ trừu tượng, mà phải tưởng tượng và viết ra một đoạn Cốt truyện (Plot) giả định hoàn hảo nhất cho user.
   - Trích xuất tự động `Keywords` và ép kiểu `Genres`.

3. **Layer 3: Reranking & Hybrid Search (Recommender)**
   - **Vector Search**: ChromaDB tính khoảng cách Cosine giữa Plot giả định và Plot của 36.000+ phim thật.
   - **Keyword Boost (Regex)**: Quét lại các từ khóa trong nội dung. Phim nào chứa đúng Keyword sẽ được thưởng điểm (Boost) để khắc phục điểm yếu "hiểu sai nghĩa đen" của Vector model nhỏ.
   - **Hard Filter**: Lọc bỏ các phim dưới chuẩn Rating hoặc sai Thể loại (Genres).

4. **Layer 4: Chế xuất Đơn thuốc (Psychological Report)**
   - Lấy thông tin Top 5 phim cuối cùng gửi ngược lại cho Gemini. Bác sĩ AI sẽ viết một đoạn phân tích tâm lý cá nhân hóa và giải thích tại sao những bộ phim này lại có tác dụng "chữa lành" cho họ.

---

## Những điểm mới & Đột phá trong dự án

- **Áp dụng HyDE trong RAG**: Khắc phục triệt để việc Vector Database bị "ngu" khi người dùng nhập câu hỏi quá ngắn hoặc quá trừu tượng.
- **Hybrid Reranking ngay trên RAM**: Không phụ thuộc hoàn toàn vào ChromaDB, tự code logic cộng điểm từ khóa bằng Regex để thao túng bảng xếp hạng (Ranking) một cách chủ động.
- **Zero-cost Backend**: Kết hợp hoàn hảo giữa Local Model (miễn phí) để filter vòng gửi xe và Cloud LLM (Gemini Flash free tier) để xử lý logic phức tạp, tối ưu hóa chi phí API.
- **Kiến trúc All-in-One**: Sử dụng `FastAPI StaticFiles` để biến Backend API thành một Web Server phục vụ Frontend, gom mọi thứ vào 1 container duy nhất cực kỳ dễ Deploy.

---

## Cấu trúc thư mục

```text
movie-psychologist/
├── backend/
│   ├── app/
│   │   ├── main.py                     # API Routing & StaticFiles mounting
│   │   └── service/
│   │       ├── llm_service.py          # Xử lý kết nối Gemini API
│   │       ├── recommender.py          # Logic Hybrid Search & ChromaDB
│   │       └── sentiment_service.py    # Xử lý mô hình Local DistilBERT
│   ├── data/
│   │   ├── chromadb/                   # Vector Database (Đã index)
│   │   └── models/
│   │       └── sentiment_model/        # Trọng số mô hình HuggingFace
├── frontend/
│   ├── index.html                      # Giao diện chính
│   ├── style.css                       # UI Glassmorphism
│   └── app.js                          # Xử lý sự kiện & Call API
├── scripts/                            # Các file Jupyter / Python build data
├── Dockerfile                          # Kịch bản Deploy lên Hugging Face
├── requirements.txt
└── README.md
```

---

## Hướng dẫn cài đặt & Chạy Local

### 1. Yêu cầu hệ thống

- Python 3.10 trở lên.
- Đã tải sẵn file `chromadb` và `sentiment_model` vào đúng cấu trúc thư mục.

### 2. Cài đặt thư viện

```bash
git clone <repo-url>
cd movie-psychologist
pip install -r requirements.txt
```

### 3. Cấu hình Biến môi trường

Tạo một file `.env` ở thư mục gốc (hoặc thư mục `backend`) và thêm API Key của Google Gemini:

```env
GEMINI_API_KEY=AIzaSyYourApiKeyHere...
```

### 4. Khởi chạy Server

Mở Terminal ở thư mục gốc hoặc thư mục `backend`, chạy lệnh:

```bash
uvicorn backend.app.main:app --reload
```

Sau đó mở trình duyệt và truy cập: `http://127.0.0.1:8000/`

---

## Hướng phát triển tương lai (Future Works)

- **User Profiling System**: Xây dựng hệ thống Đăng nhập. Lưu trữ lịch sử cảm xúc của người dùng qua từng ngày để vẽ ra biểu đồ Tâm lý học (Psychological Dashboard).
- **Collaborative Filtering**: Kết hợp thêm thuật toán gợi ý dựa trên người dùng có cùng hệ tư tưởng/cảm xúc (Matrix Factorization).
- **Voice-to-Text**: Cho phép người dùng nói/thu âm tiếng khóc, tiếng thở dài và dùng AI phân tích sắc thái giọng nói (Audio Sentiment) thay vì chỉ gõ văn bản.
