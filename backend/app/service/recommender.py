import os
import re
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
'''
- MovieRecommender: Tìm kiếm phim dựa trên vector và metadata

Cấu trúc dữ liệu của một Movie khi lưu vào ChromaDB sẽ có dạng: 
{
    "title": str,
    "year": float,
    "genres": str,
    "rating": float,
    "director": str
}

- Lưu ý: ChromaDB trả về "distance" (càng nhỏ càng giống).
 Dùng hybrid_search để khắc phục yếu điểm của vector search nếu nó ko trả ra kết quả. Cụ thể sẽ cho vector mở rộng ra lấy 50 kết quả. Sau đó, sử dụng Regex để đếm từ khóa, phim nào chứa + 0.05 điểm. Cuối cùng Sort lại danh sách. 

'''
class MovieRecommender:
    def __init__(self, chroma_path: str):
        """
        Hàm khởi tạo (Chạy 1 lần duy nhất khi Server khởi động)
        """
        # 1. Load não bộ mã hóa (Encoding)
        print("Đang load model SentenceTransformer...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # 2. Kết nối tới ổ cứng chứa ChromaDB
        print(f"Đang kết nối ChromaDB tại: {chroma_path} ...")
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_collection(name="movies")

    def _vector_search(self, query: str, top_k: int = 50):
        """
        Bước 1 của Hybrid: Chỉ dùng sức mạnh của Toán học (Vector) để lấy ra 50 phim.
        """
        # Biến câu nói tiếng Anh thành ma trận số
        query_embedding = self.encoder.encode(query).tolist()
        
        # Nhờ ChromaDB tìm các điểm gần nhất trong không gian N-chiều
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Dọn dẹp cục data rườm rà của ChromaDB thành một List các Dictionary dễ đọc
        movies = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                movie = {
                    "imdb_id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    # Lưu ý: ChromaDB trả về "distance" (càng nhỏ càng giống).
                    "distance": results["distances"][0][i] if "distances" in results else 0,
                    **results["metadatas"][0][i]  # Giải nén các trường (title, year, rating, genres)
                }
                movies.append(movie)
        return movies

    def hybrid_search(self, 
                      query: str, 
                      keywords: list = None,
                      min_rating: float = 0.0,
                      genres_filter: list = None,
                      top_k_final: int = 5):
        """
        Bước 2 của Hybrid: Tìm Vector xong thì Lọc cứng và Rerank (Chấm điểm lại).
        """
        # 1. Lấy Top 50 bằng trí tuệ nhân tạo (Semantic)
        raw_results = self._vector_search(query, top_k=50)
        df = pd.DataFrame(raw_results)
        
        if df.empty:
            return []

        # 2. Tính lại điểm: Chuyển khoảng cách (distance) thành điểm tương đồng (Similarity)
        # 1 - distance sẽ ra con số từ 0 -> 1 (càng gần 1 càng xịn)
        df['score_cosine'] = 1 - df['distance']

        # 3. Kỹ thuật RERANKER (Keyword Boost)
        # Nếu AI ngu ngơ vector tìm sót, ta dùng luật tự nhiên bù vào.
        df['score_kw'] = 0.0
        if keywords:
            for kw in keywords:
                # Regex tìm đúng từ (word boundary \b) không phân biệt hoa thường
                pattern = re.compile(rf"\b{kw}\b", re.IGNORECASE)
                # Cứ thấy chữ đó xuất hiện trong Nội dung (document), thưởng 0.05 điểm!
                df['score_kw'] += df['document'].apply(
                    lambda x: 0.05 if pd.notna(x) and pattern.search(str(x)) else 0.0
                )

        # 4. Cộng tổng điểm
        df['score_final'] = df['score_cosine'] + df['score_kw']

        # 5. Lọc Cứng (Hard Rules)
        # - Chỉ giữ phim có Rating >= mức user mong muốn
        df = df[df['rating'] >= min_rating]
        
        # - Lọc thể loại (Genres)
        if genres_filter and len(genres_filter) > 0:
            def match_genre(row_genres):
                if pd.isna(row_genres): return False
                # Nếu có chứa ít nhất 1 thể loại yêu cầu thì Giữ lại (True)
                return any(g.lower() in str(row_genres).lower() for g in genres_filter)
            df = df[df['genres'].apply(match_genre)]

        # 6. Chốt sổ: Sắp xếp lại danh sách từ cao xuống thấp và cắt lấy Top K
        df_final = df.sort_values(by="score_final", ascending=False).head(top_k_final)
        
        # Trả về kết quả dưới dạng JSON (List of Dicts) để API gửi cho Frontend
        return df_final.to_dict('records')
