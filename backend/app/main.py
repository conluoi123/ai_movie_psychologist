from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import 2 Class thần thánh chúng ta vừa viết
from app.service.recommender import MovieRecommender
from app.service.llm_service import PsychologistLLM
from app.service.sentiment_service import SentimentService
# 1. Khởi tạo App FastAPI
app = FastAPI(title="AI Movie Psychologist API", version="1.0")

# 2. Tìm đúng đường dẫn tới thư mục chromadb (nằm ở thư mục gốc)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chromadb")

SENTIMENT_MODEL_PATH = os.path.join(BASE_DIR, "data", "models")

# Khởi động 2 "nhân viên" ngay khi bật server (Chỉ chạy 1 lần)
print("Đang khởi động hệ thống AI...")
recommender = MovieRecommender(chroma_path=CHROMA_PATH)
llm_service = PsychologistLLM()
sentiment_service = SentimentService(SENTIMENT_MODEL_PATH)
print("✅ Hệ thống đã sẵn sàng!")

# Cấu trúc dữ liệu yêu cầu gửi từ Frontend (hoặc User)
class UserInput(BaseModel):
    text: str              # Lời tâm sự của User
    min_rating: float = 6.0  # Điểm đánh giá tối thiểu (mặc định 6.0)

# Cấu hình để phục vụ các file Frontend
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.post("/api/recommend")
def get_recommendation(user_input: UserInput):
    print(f"\n[1] Bệnh nhân nói: {user_input.text}")
    
    # --- BƯỚC 1: Dịch Tâm Lý ---
    print("[2] LLM đang phân tích và dịch tâm lý...")
    extracted = llm_service.translate_to_search_query(user_input.text)
    
    search_query = extracted.get("search_query", "")
    keywords = extracted.get("keywords", [])
    print(f"    -> Query: {search_query}")
    print(f"    -> Keywords: {keywords}")
    print(f"    -> Sentiment Model đo nhịp tim....")
    final_rating = user_input.min_rating
    user_mood = sentiment_service.analyze_sentiment(user_input.text)
    if user_mood == "Negative" and final_rating < 6.0: 
        user_input.min_rating = 7.5
        print(f"    -> Cảnh báo: User đang buồn! Đẩy ngưỡng điểm lên 7.5 để chọn phim 'chữa lành' hơn.")
        
    # --- BƯỚC 2: Tìm Phim ---
    print("[3] Recommender đang quét VectorDB...")
    movies = recommender.hybrid_search(
        query=search_query,      
        keywords=keywords,       
        min_rating=final_rating,
        top_k_final=5
    )
    
    if not movies:
        return {
            "psychological_analysis": "Rất tiếc, bộ não tôi trống rỗng, không tìm thấy phim phù hợp.", 
            "movies": []
        }
        
    # --- BƯỚC 3: Chế xuất lời khuyên ---
    print("[4] Bác sĩ LLM đang viết đơn thuốc (lời khuyên)...")
    advice = llm_service.generate_psychological_report(user_input.text, movies)
    
    # Trả toàn bộ cục JSON mập mạp này về cho màn hình máy tính của User
    return {
        "psychological_analysis": advice,
        "search_extracted": extracted,
        "movies": movies
    }
