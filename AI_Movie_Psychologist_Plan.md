# 🎬 AI Movie Psychologist — Kế hoạch triển khai End-to-End

> **Tagline:** *"AI hiểu bạn thích gì qua cách bạn cảm nhận về phim"*

---

## 🎯 Mục tiêu project

Project này hướng đến **hai mục tiêu song song**:

**1. Portfolio kỹ thuật**
Demonstrate khả năng xây dựng hệ thống AI end-to-end gồm: data pipeline, fine-tuning NLP model, vector search, LLM integration, và full-stack web. Mỗi bước được document rõ ràng qua Jupyter Notebooks — vừa là nơi thử nghiệm, vừa là bằng chứng kỹ thuật cho người xem portfolio.

**2. Sản phẩm có thể launch thật**
Một web app mà user thật có thể dùng — nhập phim yêu thích, mô tả tâm trạng, nhận lại phân tích tâm lý cá nhân hóa và danh sách phim phù hợp. Điểm khác biệt so với các trang recommend phim thông thường: **không chỉ nói xem phim gì, mà giải thích tại sao phim đó match tâm lý của chính người đó**.

---

## 📦 Dataset & vai trò từng nguồn

| Dataset | Nguồn | Vai trò |
|---------|-------|---------|
| IMDB Sentiment (50k reviews + label) | Kaggle | Train sentiment classifier — model học đọc cảm xúc từ văn bản |
| IMDB Official (4 file .tsv) | imdbws.com | Movie metadata: title, year, genres, rating, director, cast |
| TMDB Plot (JSON cache) | TMDB API — crawl 1 lần | Bổ sung plot/overview cho từng phim |

**Hai dataset phục vụ hai mục đích hoàn toàn khác nhau:**
- IMDB Sentiment → train model đọc cảm xúc **user input**
- IMDB metadata + TMDB plot → database phim để **recommend**

---

## 🎬 Demo flow chính của web

```
User vào web
    ↓
Nhập 2-3 phim yêu thích
Chọn mood hiện tại (dropdown)
Gõ tự do: "Tôi muốn thứ gì đó existential nhưng không quá depressing"
    ↓
AI phân tích trong ~3-5 giây
    ↓
┌─────────────────────────────────────────┐
│  🧠 PERSONALITY PROFILE                 │
│  "Bạn có xu hướng bị thu hút bởi       │
│  narrative phi tuyến, nhân vật cô đơn  │
│  mang gánh nặng hiện sinh..."           │
├─────────────────────────────────────────┤
│  🎯 TASTE DNA                           │
│  • Nonlinear narrative                  │
│  • Cosmic solitude                      │
│  • Sacrifice & time                     │
├─────────────────────────────────────────┤
│  🎬 RECOMMENDED FILMS                   │
│  [Poster] Annihilation (2018)           │
│  → "Giống Interstellar nhưng tối hơn,  │
│  match với trạng thái empty bạn đang   │
│  cảm thấy..."                           │
└─────────────────────────────────────────┘
```

---

## 📐 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                      USER BROWSER                       │
│                 Next.js Frontend                        │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                       │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │  Sentiment   │  │ Recommender │  │  LLM Layer    │  │
│  │  Classifier  │  │ (ChromaDB)  │  │ Gemini 2.5    │  │
│  │ (DistilBERT) │  │             │  │ Flash         │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
└──────────┬────────────────┬───────────────┬─────────────┘
           │                │               │
    ┌──────▼──────┐  ┌──────▼──────┐ ┌─────▼──────┐
    │  ChromaDB   │  │ PostgreSQL  │ │  Redis     │
    │ (Vector DB) │  │ (metadata)  │ │  (cache)   │
    └─────────────┘  └─────────────┘ └────────────┘
```

---

## 🌍 Kiến trúc RAG Đa ngôn ngữ (Cross-lingual RAG) & Hybrid Search

Để giải quyết bài toán người dùng nhập tiếng Việt nhưng Database lưu tiếng Anh, hệ thống áp dụng luồng **Two-stage RAG (Retrieval-Augmented Generation)**:

1. **Tầng 1: "Phiên dịch tâm lý" (Gemini 2.5 Flash)**
   - User nhập văn bản tiếng Việt tự do (VD: *"Tôi đang áp lực công việc, muốn phim gì đó thoát ly thực tại"*).
   - Gemini Flash đóng vai trò Cầu nối (Bridge), đánh giá tâm lý sơ bộ và chuyển đổi thành **Search Query (Tiếng Anh)**: *"Movies about escaping reality, workplace burnout, relaxing fantasy, finding peace."*

2. **Tầng 2: Hybrid Search (ChromaDB + Keyword Boost)**
   - **Semantic Search:** Đưa câu tiếng Anh vào model `all-MiniLM-L6-v2` để lấy Top 50 phim từ ChromaDB.
   - **Reranker (Keyword Boost & Filter):** Áp dụng logic lọc cứng (genres/rating) và cộng điểm tự động (regex keyword boost) ngay trên RAM (dùng Pandas) để chắt lọc ra **Top 5** phim phù hợp nhất. Điểm mạnh ở đây là sửa chữa được các sai sót ngớ ngẩn của Vector.

3. **Tầng 3: Tổng hợp tư vấn (Gemini 2.5 Flash)**
   - Gửi nội dung (Plot) của Top 5 phim này ngược lại cho Gemini Flash kèm Prompt: *"Dưới vai trò chuyên gia tâm lý, hãy tư vấn cho user bằng tiếng Việt và khuyên họ xem 2 trong số 5 phim này để giải tỏa áp lực."*

**=> Ý nghĩa đối với Portfolio:** Việc kết hợp giữa Fine-tune Sentiment (để vẽ biểu đồ phân tích tâm lý UI), Hybrid Search (tăng độ chính xác tìm kiếm) và RAG Đa ngôn ngữ (chăm sóc khách hàng tự nhiên) sẽ chứng minh năng lực thiết kế hệ thống AI của bạn ở tầm Senior/Full-stack AI.

---

## 📁 Cấu trúc thư mục

```
movie-psychologist/
├── notebooks/
│   ├── 01_eda_sentiment.ipynb          # EDA IMDB 50k sentiment dataset
│   ├── 02_eda_imdb_metadata.ipynb      # EDA sau khi filter & merge 4 file
│   ├── 03_sentiment_classifier.ipynb   # Train, eval, confusion matrix
│   ├── 04_embedding_pipeline.ipynb     # So sánh models, PCA 2D viz
│   ├── 05_recommender_prototype.ipynb  # Prototype ChromaDB + visualize
│   ├── 06_llm_prompt_lab.ipynb         # A/B test Gemini prompts + cost
│   └── 07_full_pipeline_demo.ipynb     # Demo end-to-end (ipywidgets)
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── recommend.py
│   │   │   ├── analyze.py
│   │   │   └── profile.py
│   │   └── services/
│   │       ├── sentiment_service.py    # Fine-tuned DistilBERT
│   │       ├── nlp_service.py          # Embedding + theme extraction
│   │       ├── recommender.py          # ChromaDB similarity search
│   │       ├── llm_service.py          # Gemini 2.5 Flash + fallback chain
│   │       └── user_profiler.py        # Build & persist taste profile
│   ├── data/
│   │   ├── raw/
│   │   │   ├── sentiment/              # IMDB_Dataset.csv (50k reviews)
│   │   │   └── imdb_official/          # 4 file .tsv từ imdbws.com
│   │   ├── processed/
│   │   │   ├── movies_merged.csv       # Sau filter & merge 4 file (36,184 phim)
│   │   │   ├── tmdb_plots.json         # Plot cache từ TMDB API
│   │   │   └── movies_final.csv        # Sau merge plot (sẵn sàng để index)
│   │   ├── models/
│   │   │   └── sentiment_model/        # Fine-tuned DistilBERT weights
│   │   └── chromadb/                   # Persistent vector index
│   ├── scripts/
│   │   ├── 01_download_imdb.py         # Download 4 file từ imdbws.com
│   │   ├── 02_filter_merge.py          # Filter + join 4 file → 36,184 phim
│   │   ├── 03_crawl_tmdb_plot.py       # Crawl plot từ TMDB → JSON cache
│   │   ├── 03b_merge_plot.py           # Merge JSON plot vào movies_merged
│   │   ├── 04_train_sentiment.py       # Fine-tune DistilBERT
│   │   └── 05_build_chroma_index.py    # Build ChromaDB vector index
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Landing + input form
│   │   ├── results/page.tsx            # Recommendations + psychology report
│   │   └── profile/page.tsx            # User taste profile history
│   ├── components/
│   │   ├── MoodInput.tsx
│   │   ├── MovieCard.tsx
│   │   ├── PersonalityRadar.tsx
│   │   └── PsychReport.tsx
│   ├── lib/api.ts
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🗂️ Phase 1: Thu thập & xây dựng Raw Data

### 1.1 Download IMDB Official Datasets

```bash
cd backend/data/raw/imdb_official

wget https://datasets.imdbws.com/title.basics.tsv.gz
wget https://datasets.imdbws.com/title.ratings.tsv.gz
wget https://datasets.imdbws.com/title.principals.tsv.gz
wget https://datasets.imdbws.com/name.basics.tsv.gz

gunzip *.tsv.gz
```

| File | Columns chính | Kích thước (~) |
|------|--------------|----------------|
| `title.basics.tsv` | tconst, titleType, primaryTitle, startYear, genres, runtimeMinutes | ~1GB |
| `title.ratings.tsv` | tconst, averageRating, numVotes | ~25MB |
| `title.principals.tsv` | tconst, ordering, nconst, category | ~700MB |
| `name.basics.tsv` | nconst, primaryName | ~800MB |

### 1.2 Filter & Merge 4 file → 36,184 phim

```python
# scripts/02_filter_merge.py
import pandas as pd

RAW = "backend/data/raw/imdb_official"
OUT = "backend/data/processed"

# ── Step 1: Load & filter basics + ratings ───────────────────────
print("Loading title.basics ...")
basics = pd.read_csv(f"{RAW}/title.basics.tsv", sep="\t",
                     na_values="\\N", low_memory=False)

ratings = pd.read_csv(f"{RAW}/title.ratings.tsv", sep="\t",
                      na_values="\\N")

movies = (
    basics
    .query("titleType == 'movie'")
    .query("startYear >= '1970'")
    .merge(ratings, on="tconst", how="inner")
    .query("numVotes >= 1000")
    .query("averageRating >= 5.0")
    [["tconst", "primaryTitle", "startYear",
      "genres", "runtimeMinutes", "averageRating", "numVotes"]]
    .rename(columns={
        "tconst":         "imdb_id",
        "primaryTitle":   "title",
        "startYear":      "year",
        "runtimeMinutes": "runtime",
        "averageRating":  "rating",
        "numVotes":       "votes",
    })
    .reset_index(drop=True)
)
print(f"  → {len(movies):,} phim sau filter")   # 36,184

# ── Step 2: Tách director + top 3 actors từ principals ───────────
print("Loading title.principals ...")
principals = pd.read_csv(f"{RAW}/title.principals.tsv", sep="\t",
                         na_values="\\N", low_memory=False)

valid_ids  = set(movies["imdb_id"])
principals = principals[principals["tconst"].isin(valid_ids)]

directors = (
    principals[principals["category"] == "director"]
    .groupby("tconst")["nconst"].first()
    .reset_index()
    .rename(columns={"nconst": "director_nconst"})
)

actors = (
    principals[
        principals["category"].isin(["actor", "actress"]) &
        (principals["ordering"] <= 3)
    ]
    .groupby("tconst")["nconst"].apply(list)
    .reset_index()
    .rename(columns={"nconst": "actor_nconsts"})
)

# ── Step 3: Lookup tên từ name.basics ────────────────────────────
print("Loading name.basics ...")
names = pd.read_csv(f"{RAW}/name.basics.tsv", sep="\t",
                    na_values="\\N", low_memory=False,
                    usecols=["nconst", "primaryName"])

nconst_to_name = names.set_index("nconst")["primaryName"].to_dict()

directors["director"] = directors["director_nconst"].map(nconst_to_name)

def resolve_actors(nconst_list):
    if not isinstance(nconst_list, list):
        return ""
    return ", ".join(nconst_to_name.get(nc, "") for nc in nconst_list).strip(", ")

actors["cast"] = actors["actor_nconsts"].apply(resolve_actors)

# ── Step 4: Join tất cả ──────────────────────────────────────────
movies = (
    movies
    .merge(directors[["tconst", "director"]], left_on="imdb_id",
           right_on="tconst", how="left").drop(columns=["tconst"])
    .merge(actors[["tconst", "cast"]], left_on="imdb_id",
           right_on="tconst", how="left").drop(columns=["tconst"])
)

movies["genres"] = movies["genres"].fillna("").str.split(",")
movies.to_csv(f"{OUT}/movies_merged.csv", index=False)
print(f"✅ {len(movies):,} phim → movies_merged.csv")
# Output: 36,184 phim với title, year, genres, rating, director, cast
```

### 1.3 Crawl Plot từ TMDB API (1 lần, lưu JSON cache)

```python
# scripts/03_crawl_tmdb_plot.py
import requests, pandas as pd, time, json
from pathlib import Path

TMDB_API_KEY = "your_tmdb_api_key"
CACHE_FILE   = "backend/data/processed/tmdb_plots.json"

cache  = json.loads(Path(CACHE_FILE).read_text()) if Path(CACHE_FILE).exists() else {}
movies = pd.read_csv("backend/data/processed/movies_merged.csv")

def fetch_plot(imdb_id: str) -> str | None:
    if imdb_id in cache:
        return cache[imdb_id]
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/find/{imdb_id}",
            params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"},
            timeout=10
        )
        results = r.json().get("movie_results", [])
        if results:
            detail = requests.get(
                f"https://api.themoviedb.org/3/movie/{results[0]['id']}",
                params={"api_key": TMDB_API_KEY}, timeout=10
            ).json()
            plot = detail.get("overview", "")
            cache[imdb_id] = plot
            return plot
    except Exception as e:
        print(f"  Error {imdb_id}: {e}")
    return None

for i, row in movies.iterrows():
    fetch_plot(row["imdb_id"])
    if i % 500 == 0:
        Path(CACHE_FILE).write_text(json.dumps(cache, ensure_ascii=False))
        print(f"  [{i}/{len(movies)}] cached {len(cache)} plots")
    time.sleep(0.03)   # ~33 req/s < giới hạn 40 req/s của TMDB

Path(CACHE_FILE).write_text(json.dumps(cache, ensure_ascii=False))
print(f"✅ Done — {len(cache)} plots saved to {CACHE_FILE}")
# Thời gian: ~18–30 phút cho 36,184 phim
```

### 1.4 Merge Plot JSON vào movies_merged.csv

```python
# scripts/03b_merge_plot.py
import pandas as pd, json

movies = pd.read_csv("backend/data/processed/movies_merged.csv")
plots  = json.load(open("backend/data/processed/tmdb_plots.json", encoding="utf-8"))

movies["plot"] = movies["imdb_id"].map(plots)

total    = len(movies)
has_plot = movies["plot"].notna().sum()
missing  = movies["plot"].isna().sum()

print(f"Total   : {total:,}")
print(f"Has plot: {has_plot:,} ({has_plot/total*100:.1f}%)")
print(f"Missing : {missing:,} ({missing/total*100:.1f}%)")

# Fallback: phim thiếu plot vẫn giữ lại nếu có genres + cast
def build_rich_text(row) -> str:
    parts = [f"Title: {row['title']} ({row['year']})"]
    if row.get("genres"):
        parts.append(f"Genres: {', '.join(row['genres']) if isinstance(row['genres'], list) else row['genres']}")
    parts.append(f"Rating: {row['rating']} ({int(row['votes']):,} votes)")
    if pd.notna(row.get("director")):
        parts.append(f"Director: {row['director']}")
    if pd.notna(row.get("cast")) and row["cast"] != "":
        parts.append(f"Cast: {row['cast']}")
    # Plot: dùng nếu đủ dài, bỏ qua nếu quá ngắn
    if pd.notna(row.get("plot")) and len(str(row["plot"])) > 50:
        parts.append(f"Plot: {row['plot']}")
    return "\n".join(parts)

movies["rich_text"] = movies.apply(build_rich_text, axis=1)

# Drop chỉ khi không có cả plot lẫn genres
movies_final = movies[
    movies["plot"].notna() | movies["genres"].notna()
].reset_index(drop=True)

movies_final.to_csv("backend/data/processed/movies_final.csv", index=False)
print(f"✅ {len(movies_final):,} phim → movies_final.csv")
```

**Fallback priority khi thiếu data:**

```
Plot đầy đủ (>50 chars)   → dùng làm semantic anchor chính
Plot ngắn / thiếu         → embed từ genres + director + cast
Thiếu cả genres lẫn plot  → drop
```

> **Tại sao plot quan trọng hơn cast/director:**
> Plot capture được *tone, theme, emotional arc* — thứ mà genres không thể phân biệt.
> Ví dụ: `Interstellar` và `Transformers` đều là `Action, Adventure, Sci-Fi`
> nhưng plot khác hoàn toàn. Cast/director chỉ hữu ích khi user input có tên người cụ thể.

---

## 🤖 Phase 2: Train Sentiment Classifier

Dataset IMDB 50k reviews dùng để **fine-tune model đọc cảm xúc từ user input** — thay vì dùng pre-trained generic model, đây là điểm kỹ thuật nổi bật nhất của project.

```python
# scripts/04_train_sentiment.py
import pandas as pd, re, torch
from sklearn.model_selection import train_test_split
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer, TrainingArguments
)
from datasets import Dataset

# ── Chuẩn bị data ────────────────────────────────────────────────
df = pd.read_csv("backend/data/raw/sentiment/IMDB_Dataset.csv")
# Columns: review, sentiment (positive/negative)

df["label"]  = (df["sentiment"] == "positive").astype(int)
df["review"] = df["review"].apply(lambda x: re.sub(r"<.*?>", " ", x).strip())

train_df, test_df = train_test_split(df, test_size=0.1, random_state=42, stratify=df["label"])
val_df, test_df   = train_test_split(test_df, test_size=0.5, random_state=42)
print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

# ── Tokenize ──────────────────────────────────────────────────────
MODEL_NAME = "distilbert-base-uncased"
tokenizer  = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(batch["review"], truncation=True,
                     max_length=512, padding="max_length")

train_ds = Dataset.from_pandas(train_df[["review","label"]]).map(tokenize, batched=True)
val_ds   = Dataset.from_pandas(val_df[["review","label"]]).map(tokenize, batched=True)

# ── Train ─────────────────────────────────────────────────────────
model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

training_args = TrainingArguments(
    output_dir="backend/data/models/sentiment_model",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=torch.cuda.is_available(),
)

Trainer(model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds).train()

model.save_pretrained("backend/data/models/sentiment_model")
tokenizer.save_pretrained("backend/data/models/sentiment_model")
print("✅ Sentiment model saved")
# Expected accuracy: ~93–95% trên test set
```

> **Không có GPU?** Train trên Google Colab T4 (miễn phí) mất ~20 phút.
> Train trên CPU mất ~4–6 giờ.

---

## 🧠 Phase 3: NLP Engine

```python
# services/nlp_service.py
from sentence_transformers import SentenceTransformer
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast
import torch, re

class NLPService:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(
            "./data/models/sentiment_model"
        )
        self.sentiment_model = DistilBertForSequenceClassification.from_pretrained(
            "./data/models/sentiment_model"
        ).eval()

    def predict_sentiment(self, text: str) -> dict:
        inputs = self.tokenizer(text, return_tensors="pt",
                                truncation=True, max_length=512)
        with torch.no_grad():
            probs = torch.softmax(
                self.sentiment_model(**inputs).logits, dim=1
            )[0]
        label = "positive" if probs[1] > probs[0] else "negative"
        return {"label": label, "score": float(probs.max())}

    def analyze_user_input(self, favorite_movies, current_mood, free_text) -> dict:
        combined  = f"Favorite films: {', '.join(favorite_movies)}. " \
                    f"Mood: {current_mood}. Looking for: {free_text}"
        embedding = self.embedder.encode(combined, normalize_embeddings=True)
        return {
            "embedding":     embedding.tolist(),
            "sentiment":     self.predict_sentiment(free_text),
            "themes":        self._extract_themes(free_text),
            "combined_text": combined,
        }

    def _extract_themes(self, text: str) -> list[str]:
        theme_map = {
            r"existential|meaning of life|vô nghĩa":  ["existentialism", "philosophy"],
            r"cô đơn|lonely|isolation":               ["solitude", "alienation"],
            r"hy vọng|hopeful|uplifting":             ["redemption", "hope"],
            r"tối|dark|depressing|noir":              ["noir", "tragedy"],
            r"tình yêu|romance|love":                 ["romance", "relationships"],
            r"thời gian|time|nonlinear|phi tuyến":    ["time", "nonlinear narrative"],
            r"hành động|action|thriller":             ["action", "thriller"],
            r"gia đình|family|coming.of.age":         ["family", "coming-of-age"],
        }
        found = []
        for pattern, themes in theme_map.items():
            if re.search(pattern, text.lower()):
                found.extend(themes)
        return list(set(found))
```

---

## 🔍 Phase 4: Build ChromaDB Index & Recommender

```python
# scripts/05_build_chroma_index.py
from sentence_transformers import SentenceTransformer
import chromadb, pandas as pd

df     = pd.read_csv("backend/data/processed/movies_final.csv")
model  = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="backend/data/chromadb")
col    = client.get_or_create_collection("movies", metadata={"hnsw:space": "cosine"})

BATCH = 256
for i in range(0, len(df), BATCH):
    batch = df.iloc[i:i+BATCH]
    embs  = model.encode(batch["rich_text"].tolist(), normalize_embeddings=True)
    col.add(
        ids=batch["imdb_id"].tolist(),
        embeddings=embs.tolist(),
        documents=batch["rich_text"].tolist(),
        metadatas=batch[["title","year","genres","rating","votes",
                          "director","cast"]].to_dict("records")
    )
    print(f"  Indexed {min(i+BATCH, len(df))}/{len(df)}")

print(f"✅ {col.count()} phim indexed")
```

```python
# services/recommender.py
import chromadb
from sentence_transformers import SentenceTransformer

class MovieRecommender:
    def __init__(self):
        self.col   = chromadb.PersistentClient(
            path="./data/chromadb"
        ).get_collection("movies")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def recommend(self, user_embedding: list[float], n_results: int = 8) -> list[dict]:
        results = self.col.query(
            query_embeddings=[user_embedding],
            n_results=n_results,
            include=["metadatas", "distances", "documents"]
        )
        return [
            {**meta, "imdb_id": id_, "similarity": round(1 - dist, 3)}
            for meta, id_, dist in zip(
                results["metadatas"][0],
                results["ids"][0],
                results["distances"][0]
            )
        ]
```

---

## 🤖 Phase 5: LLM Layer — Gemini 2.5 Flash + Fallback Chain

**Rate limit Gemini 2.5 Flash:**

| Tier | RPM | TPM | RPD |
|------|-----|-----|-----|
| Free | 10 | 250,000 | 250 |
| Paid Tier 1 | 150–300 | 250,000 | Không giới hạn |

Free tier 250 RPD → chịu được ~250 user/ngày, đủ cho giai đoạn đầu launch.

> **Lưu ý:** RPD reset lúc midnight Pacific Time (= 3pm chiều giờ Việt Nam).

```python
# services/llm_service.py
import google.generativeai as genai
import time, json, os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM = """
Bạn là nhà tâm lý học chuyên về điện ảnh. Bạn đọc được tính cách và
tâm trạng người xem qua cách họ mô tả cảm xúc với phim. Phân tích
sắc sảo, cá nhân hóa cao, tránh sáo rỗng. Viết tiếng Việt tự nhiên.
Chỉ trả về JSON thuần, không markdown, không giải thích thêm.
"""

def build_prompt(user_input: dict, movies: list[dict], analysis: dict) -> str:
    movie_list = "\n".join([
        f"- {m['title']} ({m['year']}) | Rating: {m['rating']} | Score: {m['similarity']}"
        for m in movies[:5]
    ])
    return f"""
{SYSTEM}

Người dùng chia sẻ:
- Phim yêu thích: {user_input['favorite_movies']}
- Tâm trạng: {user_input['mood']}
- Họ nói: "{user_input['free_text']}"
- Sentiment: {analysis['sentiment']}
- Chủ đề nổi bật: {analysis['themes']}

Phim phù hợp nhất:
{movie_list}

Trả về JSON với 4 trường:
1. "personality_profile": 3-4 câu phân tích xu hướng tâm lý
2. "taste_dna": list 4-5 string mô tả DNA điện ảnh
3. "movie_explanations": object {{title: "lý do match 1-2 câu"}}
4. "hidden_insight": 1 quan sát bất ngờ mà người dùng chưa nhận ra
"""

def generate_report(user_input: dict, movies: list[dict], analysis: dict) -> dict:
    prompt = build_prompt(user_input, movies, analysis)

    # ── Tầng 1: Gemini 2.5 Flash ─────────────────────────────────
    try:
        model    = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"⚠️  Gemini 2.5 Flash failed: {e}")

    # ── Tầng 2: Retry với exponential backoff ─────────────────────
    for wait in [2, 4, 8]:
        try:
            time.sleep(wait)
            model    = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception:
            continue

    # ── Tầng 3: Gemini 2.0 Flash (quota cao hơn, nhẹ hơn) ────────
    try:
        model    = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"⚠️  Gemini 2.0 Flash failed: {e}")

    # ── Tầng 4: Template fallback (không cần LLM, không bao giờ crash)
    return _template_fallback(movies, analysis)


def _template_fallback(movies: list[dict], analysis: dict) -> dict:
    themes     = analysis.get("themes", [])
    top_genres = set()
    for m in movies[:3]:
        g = m.get("genres", [])
        if isinstance(g, list):
            top_genres.update(g[:2])
    return {
        "personality_profile": (
            f"Bạn có xu hướng thích các bộ phim mang chủ đề "
            f"{', '.join(themes[:3]) if themes else 'đa dạng'}. "
            f"Thị hiếu nghiêng về {', '.join(list(top_genres)[:3])}."
        ),
        "taste_dna": themes[:5] if themes else ["Đa dạng thể loại"],
        "movie_explanations": {
            m["title"]: f"Phù hợp với thị hiếu của bạn ({m['similarity']:.0%} tương đồng)."
            for m in movies[:5]
        },
        "hidden_insight": "Hệ thống đang tạm thời quá tải — phân tích chi tiết sẽ sớm trở lại.",
        "_fallback": True
    }
```

**Fallback chain tóm tắt:**
```
Gemini 2.5 Flash → Retry x3 (2s/4s/8s) → Gemini 2.0 Flash → Template
```

---

## 🌐 Phase 6: FastAPI Backend

```python
# app/routers/recommend.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.nlp_service import NLPService
from app.services.recommender import MovieRecommender
from app.services.llm_service import generate_report

router      = APIRouter()
nlp         = NLPService()
recommender = MovieRecommender()

class RecommendRequest(BaseModel):
    favorite_movies: list[str]
    current_mood: str
    free_text: str
    n_results: int = 8

@router.post("/recommend")
async def recommend(req: RecommendRequest):
    analysis = nlp.analyze_user_input(
        req.favorite_movies, req.current_mood, req.free_text
    )
    movies = recommender.recommend(analysis["embedding"], req.n_results)
    report = generate_report(req.model_dump(), movies, analysis)
    return {"movies": movies, "report": report}
```

---

## 📓 Phase 7: Jupyter Notebooks

### Notebook 01 — EDA Sentiment Dataset

```python
import pandas as pd, matplotlib.pyplot as plt
from wordcloud import WordCloud

df = pd.read_csv("backend/data/raw/sentiment/IMDB_Dataset.csv")
df["label"]  = (df["sentiment"] == "positive").astype(int)
df["length"] = df["review"].str.len()

# Label balance
df["sentiment"].value_counts().plot(kind="bar", color=["#e63946","#2a9d8f"])
plt.title("Label Distribution"); plt.show()

# Review length by sentiment
df.groupby("sentiment")["length"].hist(alpha=0.6, bins=50, figsize=(10,4))
plt.title("Review Length by Sentiment"); plt.show()

# Wordcloud
for label in ["positive", "negative"]:
    text = " ".join(df[df["sentiment"]==label]["review"])
    wc   = WordCloud(width=800, height=300, background_color="black").generate(text)
    plt.figure(figsize=(12,4)); plt.imshow(wc); plt.axis("off")
    plt.title(f"Wordcloud — {label}"); plt.show()
```

### Notebook 02 — EDA IMDB Metadata (sau merge)

```python
import pandas as pd, matplotlib.pyplot as plt, ast

df = pd.read_csv("backend/data/processed/movies_merged.csv")
print(f"Shape: {df.shape}")           # (36184, 9)
print(df.isnull().sum())

# Rating distribution
df["rating"].hist(bins=20, color="#e63946", figsize=(8,3))
plt.title("Rating Distribution"); plt.show()

# Top genres
from collections import Counter
all_genres = []
for g in df["genres"].dropna():
    try:    all_genres.extend(ast.literal_eval(g))
    except: all_genres.extend(str(g).split(","))
top = Counter(all_genres).most_common(15)
genres, counts = zip(*top)
plt.barh(genres[::-1], counts[::-1], color="#457b9d")
plt.title("Top 15 Genres"); plt.tight_layout(); plt.show()

# Phim theo thập kỷ
df["decade"] = (df["year"].astype(float)//10*10).astype(str)+"s"
df["decade"].value_counts().sort_index().plot(kind="bar", color="#2a9d8f")
plt.title("Films by Decade"); plt.xticks(rotation=45); plt.show()
```

### Notebook 03 — Sentiment Classifier Eval

```python
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Sau khi train xong
preds  = trainer.predict(test_ds)
y_pred = preds.predictions.argmax(axis=1)
y_true = test_df["label"].tolist()

print(classification_report(y_true, y_pred, target_names=["negative","positive"]))

ConfusionMatrixDisplay.from_predictions(
    y_true, y_pred,
    display_labels=["negative","positive"], cmap="Blues"
)
plt.title("Confusion Matrix — Fine-tuned DistilBERT"); plt.show()

# Error analysis
test_df["pred"] = y_pred
wrong = test_df[test_df["label"] != test_df["pred"]]
print(f"\n🔍 5 review bị classify sai:")
print(wrong.sample(5)[["review","sentiment","pred"]].to_string())
```

### Notebook 04 — Embedding Visualization

```python
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
import plotly.express as px
import pandas as pd, numpy as np

df    = pd.read_csv("backend/data/processed/movies_final.csv").sample(1000, random_state=42)
model = SentenceTransformer("all-MiniLM-L6-v2")
embs  = model.encode(df["rich_text"].tolist(), normalize_embeddings=True)

coords = PCA(n_components=2).fit_transform(embs)
df["x"], df["y"] = coords[:,0], coords[:,1]
df["primary_genre"] = df["genres"].apply(
    lambda g: eval(g)[0] if isinstance(g,str) and g.startswith("[") else str(g).split(",")[0]
)

fig = px.scatter(
    df, x="x", y="y", color="primary_genre",
    hover_data=["title","year","rating"],
    title="Movie Embedding Space (PCA 2D) — 1000 phim ngẫu nhiên",
    width=950, height=600
)
fig.show()

# Similarity heatmap benchmark films
benchmark = ["Interstellar","The Matrix","Her","Parasite","Fight Club","2001: A Space Odyssey"]
bm_df     = df[df["title"].isin(benchmark)].drop_duplicates("title")
bm_embs   = model.encode(bm_df["rich_text"].tolist(), normalize_embeddings=True)
sim_mat   = np.dot(bm_embs, bm_embs.T)

import seaborn as sns
plt.figure(figsize=(8,6))
sns.heatmap(sim_mat, xticklabels=bm_df["title"], yticklabels=bm_df["title"],
            annot=True, fmt=".2f", cmap="RdYlGn", vmin=0, vmax=1)
plt.title("Cosine Similarity — Benchmark Films")
plt.xticks(rotation=45, ha="right"); plt.tight_layout(); plt.show()
```

### Notebook 06 — LLM Prompt Lab (Gemini)

```python
import google.generativeai as genai, time, json, os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

test_input = {
    "favorite_movies": ["Interstellar", "Arrival", "Blade Runner 2049"],
    "mood": "empty",
    "free_text": "Tôi muốn thứ gì đó existential nhưng không quá depressing"
}

# A/B test system prompt
prompts = {
    "V1 — Ngắn":  "Bạn là nhà tâm lý học điện ảnh. Phân tích ngắn gọn.",
    "V2 — Chi tiết": """Bạn là nhà tâm lý học chuyên về điện ảnh.
Đọc tâm lý sâu qua thị hiếu phim. Sắc sảo, cá nhân hóa, tránh sáo rỗng."""
}

for name, system in prompts.items():
    start    = time.time()
    model    = genai.GenerativeModel("gemini-2.5-flash",
                   system_instruction=system)
    response = model.generate_content(str(test_input))
    elapsed  = time.time() - start
    print(f"\n{'='*50}\n{name} | {elapsed:.2f}s")
    print(response.text[:400])

# Cost estimate (Gemini 2.5 Flash: ~$0.15/1M input, $0.60/1M output tokens)
usage = response.usage_metadata
cost  = (usage.prompt_token_count * 0.15 + usage.candidates_token_count * 0.60) / 1_000_000
print(f"\nEst. cost/request: ${cost:.5f}")
print(f"Est. cost/1000 users: ${cost*1000:.2f}")
```

---

## 📦 Dependencies

### backend/requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
google-generativeai==0.8.0
sentence-transformers==2.7.0
transformers==4.41.0
datasets==2.19.0
torch==2.3.0
chromadb==0.5.0
pandas==2.2.0
numpy==1.26.4
scikit-learn==1.4.0
pydantic==2.7.0
python-dotenv==1.0.0
redis==5.0.4
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
requests==2.32.0
```

### notebooks/requirements (thêm)

```
jupyter
ipywidgets
plotly
seaborn
wordcloud
matplotlib
```

---

## 🗺️ Roadmap triển khai

| Phase | Task | Kết quả | Thời gian |
|-------|------|---------|-----------|
| **P1** | Setup repo, Docker, .env | Skeleton project | 1 ngày |
| **P2** | Download 4 IMDB files | Raw data ~2.5GB | 0.5 ngày |
| **P2.5** | 📓 Notebook 02: EDA metadata | Hiểu distribution data | 0.5 ngày |
| **P3** | filter_merge.py | **36,184 phim** | 0.5 ngày |
| **P4** | crawl_tmdb_plot.py | JSON cache ~30 phút | 1 ngày |
| **P4.5** | merge_plot.py | movies_final.csv | 0.5 ngày |
| **P5** | 📓 Notebook 01: EDA sentiment | Hiểu dataset 50k | 0.5 ngày |
| **P6** | Train sentiment classifier | ~93–95% accuracy | 1–2 ngày |
| **P6.5** | 📓 Notebook 03: Eval classifier | Confusion matrix | 0.5 ngày |
| **P7** | Build ChromaDB index | Vector DB sẵn sàng | 0.5 ngày |
| **P7.5** | 📓 Notebook 04–05: Embedding + recommender viz | Validate pipeline | 1 ngày |
| **P8** | FastAPI endpoints | Backend hoàn chỉnh | 2 ngày |
| **P8.5** | 📓 Notebook 06: Gemini prompt lab | Tối ưu prompt | 0.5 ngày |
| **P9** | Frontend Next.js | UI hoàn chỉnh | 3–4 ngày |
| **P9.5** | 📓 Notebook 07: Full demo | ipywidgets demo | 0.5 ngày |
| **P10** | Integration test + deploy | Live product | 2 ngày |
| **Tổng** | | | **~3 tuần** |

---

## 🚀 Bước tiếp theo ngay bây giờ

Bạn đã có:
- ✅ `movies_merged.csv` — 36,184 phim
- ✅ `tmdb_plots.json` — plot cache từ TMDB

**Chạy tiếp:**
```bash
# Merge plot vào merged
python scripts/03b_merge_plot.py

# Xem kết quả có bao nhiêu phim có plot
# Sau đó vào Notebook 01 + 02 để EDA
jupyter notebook notebooks/
```

---

## 💡 Tips & Gotchas

- **TMDB crawl interrupt-safe:** Script 03 có JSON cache — dừng giữa chừng chạy lại tiếp tục từ chỗ dừng
- **Gemini RPD reset:** Lúc midnight Pacific = 3pm giờ Việt Nam — nếu quota hết, đợi đến 3pm
- **Train sentiment trên CPU:** ~4–6 giờ. Dùng Google Colab T4 (free) chỉ mất ~20 phút
- **ChromaDB:** Chạy `build_chroma_index.py` một lần — không rebuild khi restart server
- **Fallback flag:** Khi LLM trả về `_fallback: true`, frontend nên hiển thị khác đi để user biết

---

*IMDB Official Datasets · TMDB API · DistilBERT · Sentence Transformers · Gemini 2.5 Flash · ChromaDB*
