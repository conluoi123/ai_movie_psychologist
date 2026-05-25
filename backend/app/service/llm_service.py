import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load file .env để lấy API_KEY
load_dotenv()

class PsychologistLLM:
    def __init__(self):
        """Khởi tạo Bác sĩ tâm lý AI"""
        # 1. Báo danh với Google
        api_key = os.getenv("GEMINI_API")
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API trong file .env!")
            
        genai.configure(api_key=api_key)
        
        # 2. Chọn model. Ta dùng bản 2.5 Flash vì nó phản hồi gần như tức thì và siêu rẻ.
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def translate_to_search_query(self, user_text: str):
        """
        GIAI ĐOẠN 1: Dịch Tâm Lý (Vietnamese -> English JSON)
        Sử dụng kỹ thuật HyDE (Tạo cốt truyện giả định) và Lọc Thể loại.
        """
        prompt = f"""
        Bạn là một chuyên gia phân tích tâm lý qua phim ảnh.
        Bệnh nhân đang nói: "{user_text}"
        
        Nhiệm vụ của bạn là tưởng tượng ra một BỘ PHIM HOÀN HẢO nhất để xoa dịu/thỏa mãn tâm trạng này.
        Hãy trích xuất 3 thông tin sau bằng TIẾNG ANH:
        
        1. search_query: Viết một câu tóm tắt trực tiếp CỐT TRUYỆN của bộ phim hoàn hảo đó (Không dùng các từ chỉ cảm xúc trừu tượng như "soul healing", "stress relief". Hãy tả cụ thể cảnh vật, con người, sự kiện).
        Ví dụ: "A peaceful story about a young person leaving the city to live on a farm, growing vegetables and cooking food."
        2. keywords: 3-5 danh từ/tính từ miêu tả bối cảnh hoặc chủ đề cốt lõi. (Ví dụ: ["nature", "farm", "cooking", "friends"])
        3. genres: Trả về một list chứa 1 đến 2 thể loại phim CHÍNH XÁC nhất trong danh sách sau đây để chặn các phim sai chủ đề:
        [Action, Adventure, Animation, Biography, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Musical, Mystery, Romance, Sci-Fi, Sport, Thriller, War, Western]
        
        BẮT BUỘC TRẢ VỀ ĐÚNG MỘT ĐỊNH DẠNG JSON NHƯ SAU, KHÔNG GIẢI THÍCH:
        {{
            "search_query": "...",
            "keywords": ["...", "..."],
            "genres": ["...", "..."]
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            print(f"Lỗi LLM (Translate): {e}")
            return {
                "search_query": "A story about friends going on a fun adventure",
                "keywords": ["fun", "adventure", "friends"],
                "genres": ["Comedy", "Adventure"]
            }


    def generate_psychological_report(self, user_text: str, recommended_movies: list):
        """
        GIAI ĐOẠN 2: Tư Vấn Chữa Lành (Data -> Tiếng Việt)
        Lấy Top phim tìm được từ Recommender, gửi cho Gemini để nó "chế biến" thành bức thư tư vấn.
        """
        # 1. Ép danh sách Top phim thành chuỗi văn bản cho AI dễ đọc
        movies_str = ""
        for i, m in enumerate(recommended_movies, 1):
            # Truyền TOÀN BỘ nội dung plot, không được cắt ngắn để tránh AI bịa chuyện
            movies_str += f"{i}. {m['title']} ({m['year']}) - Rating: {m['rating']}\nNội dung từ Database:\n{m['document']}\n\n"

        # 2. Bơm Prompt "Nhập vai" cho AI
        prompt = f"""
        Bạn là "AI Movie Psychologist" - một Bác sĩ tâm lý vô cùng tinh tế và ấm áp.
        Bệnh nhân nói với bạn: "{user_text}"
        
        Hệ thống cơ sở dữ liệu đã tìm ra các bộ phim phù hợp nhất dưới đây:
        {movies_str}
        
        Nhiệm vụ của bạn: Viết một lời tư vấn tâm lý ngắn gọn bằng Tiếng Việt.
        - Hãy thể hiện sự thấu cảm sâu sắc với tâm trạng của họ.
        - Khuyên họ xem 1 đến 2 bộ phim phù hợp nhất trong danh sách trên và giải thích sự liên kết giữa thông điệp bộ phim đó với hoàn cảnh hiện tại của họ.
        
        LUẬT BẮT BUỘC (CỰC KỲ QUAN TRỌNG):
        - CHỈ ĐƯỢC PHÉP sử dụng đúng phần "Nội dung từ Database" ở trên để giải thích nội dung phim. 
        - TUYỆT ĐỐI KHÔNG được tự ý "chém gió", tưởng tượng, hoặc bịa thêm tình tiết phim không có thật. Nếu dữ liệu không đề cập chi tiết, hãy nói chung chung về thông điệp chính.
        - Trình bày dạng văn bản bình thường, ấm áp như một người bạn (không dùng Markdown phức tạp).
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Lỗi LLM (Report): {e}")
            return "Rất tiếc, đường truyền tâm lý đang bị nhiễu. Nhưng tôi tin rằng xem một bộ phim hay bên dưới sẽ giúp tâm trạng bạn tốt hơn rất nhiều!"
