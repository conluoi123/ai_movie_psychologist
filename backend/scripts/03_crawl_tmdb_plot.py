# scripts/03_crawl_tmdb_plot.py
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR.parent / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "movies_merged.csv"
OUTPUT_FILE = PROCESSED_DIR / "movies_final.csv"
CACHE_FILE = PROCESSED_DIR / "tmdb_plot_cache.json"

load_dotenv(SCRIPT_DIR.parent / ".env")
TMDB_API_KEY = os.getenv("API_KEY") or os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

if not TMDB_API_KEY:
    raise RuntimeError("Missing API key. Set API_KEY (or TMDB_API_KEY) in backend/.env")

cache_lock = threading.Lock()
write_lock = threading.Lock()
thread_local = threading.local()

if CACHE_FILE.exists():
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
else:
    cache = {}


def get_session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        session.headers.update({"Accept": "application/json", "User-Agent": "MovieRecommenderBot/1.0"})
        thread_local.session = session
    return thread_local.session


def fetch_plot(imdb_id: str) -> str | None:
    imdb_id = str(imdb_id)

    with cache_lock:
        if imdb_id in cache:
            return cache[imdb_id]

    session = get_session()

    try:
        r = session.get(
            f"{BASE_URL}/find/{imdb_id}",
            params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"},
            timeout=12,
        )
        if r.status_code != 200:
            return None

        results = r.json().get("movie_results", [])
        if not results:
            with cache_lock:
                cache[imdb_id] = None
            return None

        tmdb_id = results[0]["id"]

        detail_resp = session.get(
            f"{BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=12,
        )
        if detail_resp.status_code != 200:
            return None

        detail = detail_resp.json()
        plot = detail.get("overview") or None

        with cache_lock:
            cache[imdb_id] = plot

        return plot

    except Exception:
        return None


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    movies = pd.read_csv(INPUT_FILE)
    if "imdb_id" not in movies.columns:
        raise ValueError("Input file must contain 'imdb_id' column")

    imdb_ids = movies["imdb_id"].astype(str).tolist()
    plots = [None] * len(imdb_ids)

    max_workers = min(12, (os.cpu_count() or 8) * 2)
    flush_every = 500

    print(f"Start crawling {len(imdb_ids)} movies with {max_workers} threads...")

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(fetch_plot, imdb_id): idx
            for idx, imdb_id in enumerate(imdb_ids)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            plots[idx] = future.result()
            completed += 1

            if completed % flush_every == 0:
                with write_lock, cache_lock:
                    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                print(f"  [{completed}/{len(imdb_ids)}] cached {len(cache)} plots")

    with write_lock, cache_lock:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    movies["plot"] = plots
    movies_final = movies.dropna(subset=["plot"]).query("plot != ''")
    movies_final.to_csv(OUTPUT_FILE, index=False)

    print(f"Done. {len(movies_final)} movies have metadata + plot")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
