import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

# ── Cấu hình Path ─────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR.parent / "data" / "processed"
CHROMA_PATH = SCRIPT_DIR.parent / "data" / "chromadb"
MOVIES_PATH = PROCESSED_DIR / "movies_final.csv"

COLLECTION_NAME = "movies"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256

def main():
    print("="*50)
    print("BẮT ĐẦU QUÁ TRÌNH BUILD VECTOR DATABASE (CHROMADB)")
    print("="*50)

    # 1. Load Data
    print(f"Loading data from: {MOVIES_PATH.name}...")
    try:
        df = pd.read_csv(MOVIES_PATH)
    except FileNotFoundError:
        print(f" LỖI: Không tìm thấy file {MOVIES_PATH}")
        return

    if "rich_text" not in df.columns or "imdb_id" not in df.columns:
        print(" LỖI: Dữ liệu thiếu cột 'rich_text' hoặc 'imdb_id'. Hãy kiểm tra lại file movies_final.csv!")
        return

    n = len(df)
    print(f" Tổng số phim cần index: {n:,}")

    # 2. Khởi tạo Model
    print(f"\nLoading embedding model: '{MODEL_NAME}' ... (lần đầu sẽ hơi lâu để tải model)")
    model = SentenceTransformer(MODEL_NAME)

    # 3. Khởi tạo ChromaDB
    print(f"\nInitializing ChromaDB tại: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    
    # Clean DB cũ (Xóa đi build lại từ đầu cho sạch)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f" Đã xóa collection cũ '{COLLECTION_NAME}'.")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # 4. Chạy vòng lặp Indexing
    print("\nBắt đầu quá trình mã hóa (Encode) và Indexing...")
    
    for i in range(0, n, BATCH_SIZE):
        batch = df.iloc[i:i+BATCH_SIZE].copy()
        
        texts = batch["rich_text"].fillna("").tolist()
        
        # Tạo vector
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        # Xử lý metadata an toàn cho ChromaDB
        metadatas = []
        for _, row in batch.iterrows():
            metadatas.append({
                "title": str(row.get("title", "")),
                "year": float(row.get("year", 0)) if pd.notna(row.get("year")) else 0.0,
                "genres": str(row.get("genres", "")),
                "rating": float(row.get("rating", 0)) if pd.notna(row.get("rating")) else 0.0,
                "director": str(row.get("director", ""))
            })

        # Đẩy vào ChromaDB
        collection.add(
            ids=batch["imdb_id"].astype(str).tolist(),
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )

        # In log tiến độ
        if (i // BATCH_SIZE) % 5 == 0 or i + BATCH_SIZE >= n:
            current = min(i + BATCH_SIZE, n)
            percent = (current / n) * 100
            print(f"  Đang chạy: {current:,}/{n:,} ({percent:.1f}%)")

    print("\n HOÀN TẤT! Vector Database đã sẵn sàng.")
    print(f"Bạn có thể kiểm tra thư mục: {CHROMA_PATH}")

if __name__ == "__main__":
    main()
