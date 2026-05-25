import pandas as pd
import json 
from pathlib import Path

# Cấu hình path 
SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR.parent / "data" / "processed"


# INPUT_FILE = PROCESSED_DIR / "movies_merged.csv"
# OUTPUT_FILE = PROCESSED_DIR / "movies_final.csv"
# CACHE_FILE = PROCESSED_DIR / "tmdb_plot_cache.json"

MOVIES_PATH = PROCESSED_DIR / "movies_merged.csv"

TMDB_PLOT_FILE = PROCESSED_DIR / "tmdb_plot_cache.json"

movies = pd.read_csv(MOVIES_PATH)
plots = json.load(open(TMDB_PLOT_FILE, "r", encoding="utf-8"))


movies["plots"] = movies["imdb_id"].map(plots)

total = len(movies)
has_plot = movies["plots"].notna().sum()
no_plot = total - has_plot 

print(f"Tổng số phim: {total}")
print(f"Phim có plot: {has_plot}")
print(f"Phim không có plot: {no_plot}")

# drop missing 
print(f"Drop missing rows")
movies_final = movies.dropna(subset=['plots']).reset_index(drop=True)
print(f"Số dòng sau drop: {len(movies_final):,} phim.")

# xây dựng dữ liệu cho AI 
def build_rich_text(row) -> str:
    parts = [f"Title: {row['title']} ({row['year']})"]
    
    if pd.notna(row.get("genres")) and row["genres"] != "":
        parts.append(f"Genres: {row['genres']}")
        
    parts.append(f"Rating: {row['rating']} ({int(row['votes']):,} votes)")
    
    if pd.notna(row.get("director")):
        parts.append(f"Director: {row['director']}")
        
    if pd.notna(row.get("cast")) and row["cast"] != "":
        parts.append(f"Cast: {row['cast']}")
    parts.append(f"Plot: {row['plots']}")
    
    return "\n".join(parts)

print("Đang tạo cột rich_text")
movies_final["rich_text"] = movies_final.apply(build_rich_text, axis=1)

# lưu file cuối cùng 

output_path = PROCESSED_DIR / "movies_final.csv"
movies_final.to_csv(output_path, index=False) # ko lưu chỉ số dòng 
print(f"Lưu thành công {len(movies_final) } phim vào file csv.")


