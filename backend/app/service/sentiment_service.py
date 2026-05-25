import os
from transformers import pipeline

class SentimentService:
    def __init__(self, model_path: str):
        """Khởi tạo Bộ phân tích cảm xúc bằng model Local"""
        print(f"Đang load mô hình Cảm xúc từ: {model_path} ...")
        
        # Gọi thẳng thư viện Pipeline của HuggingFace, bắt nó đọc model từ ổ cứng của bạn
        self.classifier = pipeline(
            "text-classification", 
            model=model_path, 
            tokenizer=model_path,
            device=-1  # Chạy bằng CPU (-1). Nếu sau này bạn có máy xịn cắm Card màn hình thì đổi thành 0
        )
        
    def analyze_sentiment(self, text: str) -> str:
        """
        Đọc đoạn văn của User và phán phán nó là Tích cực hay Tiêu cực.
        """
        try:
            # Chỉ lấy kết quả của phần tử đầu tiên [0]
            result = self.classifier(text)[0]
            label = result['label']
            score = result['score']
            
            print(f"    [AI Cảm xúc] Label: {label} | Độ tự tin: {score:.2f}")
            
            # Thông thường, HuggingFace sẽ nhả ra LABEL_0 (Tiêu cực) và LABEL_1 (Tích cực)
            # Tùy thuộc vào cách bạn map nhãn lúc train trên Kaggle
            if label == "LABEL_0" or str(label).lower() == "negative":
                return "Negative"
            else:
                return "Positive"
        except Exception as e:
            print(f"Lỗi khi chạy model Sentiment: {e}")
            # Nếu sập thì trả về Neutral để không ảnh hưởng luồng chính
            return "Neutral"
