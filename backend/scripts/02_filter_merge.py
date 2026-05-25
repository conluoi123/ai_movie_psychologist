import os
import pandas as pd

# Lấy đường dẫn tuyệt đối của thư mục chứa script này (backend/scripts)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Lùi lại 2 cấp để ra thư mục gốc (Sentiment Analysis - 17092024)
ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Đặt đường dẫn tuyệt đối tới data gốc và thư mục output
RAW = os.path.join(ROOT_DIR, "backend", "data", "raw")
OUT = os.path.join(ROOT_DIR, "backend", "data", "processed")

# ── Step 1: Load & filter basics + ratings ───────────────────────
print("Loading title.basics ...")
basics = pd.read_csv(f"{RAW}/title.basics.tsv/title.basics.tsv", sep="\t",
                     na_values="\\N", low_memory=False)

print("Loading title.ratings ...")
ratings = pd.read_csv(f"{RAW}/title.ratings.tsv/title.ratings.tsv", sep="\t",
                      na_values="\\N")

movies = (
    basics
    .query("titleType == 'movie'")      # ~600k entries → chỉ lấy phim
    .query("startYear >= 1970")         # bỏ phim cũ quá
    .merge(ratings, on="tconst", how="inner")
    .query("numVotes >= 1000")          # đủ lượt vote để tin cậy
    .query("averageRating >= 5.0")      # lọc phim quá tệ
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
print(f"  → {len(movies):,} phim sau filter")   # ~50k–80k

# ── Step 2: Load principals → tách director + top 3 actors ───────
print("Loading title.principals in chunks (to prevent Out Of Memory) ...")
valid_ids = set(movies["imdb_id"])

chunks = []
for chunk in pd.read_csv(f"{RAW}/title.principals.tsv/title.principals.tsv", sep="\t",
                         na_values="\\N", chunksize=1000000, low_memory=False):
    # Lọc ngay từng chunk để tiết kiệm RAM
    chunks.append(chunk[chunk["tconst"].isin(valid_ids)])

principals = pd.concat(chunks, ignore_index=True)
del chunks # Giải phóng RAM

# Đạo diễn: category == "director"
directors = (
    principals[principals["category"] == "director"]
    .groupby("tconst")["nconst"]
    .first()                            # lấy đạo diễn đầu tiên
    .reset_index()
    .rename(columns={"nconst": "director_nconst"})
)

# Diễn viên: category == "actor" hoặc "actress", ordering <= 3
actors = (
    principals[
        principals["category"].isin(["actor", "actress"]) &
        (principals["ordering"] <= 3)
    ]
    .groupby("tconst")["nconst"]
    .apply(list)                        # list tối đa 3 nconst
    .reset_index()
    .rename(columns={"nconst": "actor_nconsts"})
)

# ── Step 3: Load name.basics → lookup tên người ──────────────────
print("Loading name.basics in chunks ...")
# Lấy danh sách nconst hợp lệ để lọc ngay khi đọc file
valid_nconsts = set(directors["director_nconst"].dropna())
for actors_list in actors["actor_nconsts"].dropna():
    valid_nconsts.update(actors_list)

name_chunks = []
for chunk in pd.read_csv(f"{RAW}/name.basics.tsv/name.basics.tsv", sep="\t",
                         na_values="\\N", chunksize=1000000, low_memory=False,
                         usecols=["nconst", "primaryName"]):
    name_chunks.append(chunk[chunk["nconst"].isin(valid_nconsts)])

names = pd.concat(name_chunks, ignore_index=True)
del name_chunks

nconst_to_name = names.set_index("nconst")["primaryName"].to_dict()

# ── Step 4: Map nconst → tên thật ────────────────────────────────
directors["director"] = directors["director_nconst"].map(nconst_to_name)

def resolve_actors(nconst_list: list) -> str:
    if not isinstance(nconst_list, list):
        return ""
    return ", ".join(
        nconst_to_name.get(nc, "") for nc in nconst_list
    ).strip(", ")

actors["cast"] = actors["actor_nconsts"].apply(resolve_actors)

# ── Step 5: Join tất cả vào movies ───────────────────────────────
movies = (
    movies
    .merge(directors[["tconst", "director"]], left_on="imdb_id", right_on="tconst", how="left")
    .drop(columns=["tconst"])
    .merge(actors[["tconst", "cast"]], left_on="imdb_id", right_on="tconst", how="left")
    .drop(columns=["tconst"])
)

# genres từ "Action,Drama" → list ["Action", "Drama"]
movies["genres"] = movies["genres"].fillna("").str.split(",")

# ── Step 6: Xem kết quả & lưu ────────────────────────────────────
print("\nSample output:")
print(movies[["title","year","genres","rating","director","cast"]].head(3).to_string())

print(f"\nNull counts:\n{movies[['director','cast']].isnull().sum()}")

movies.to_csv(f"{OUT}/movies_merged.csv", index=False)
print(f"\n✅ Saved {len(movies):,} phim → {OUT}/movies_merged.csv")
# Expected: ~50,000–80,000 rows
# Columns: imdb_id, title, year, genres, runtime, rating, votes, director, cast