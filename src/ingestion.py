"""GDELT fetch + reproducible offline replay inputs."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def parse_gdelt_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # GDELT seendate is commonly YYYYMMDDHHMMSS in UTC.
        return datetime.strptime(str(value), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        try:
            dt = pd.to_datetime(value, utc=True, errors="raise")
            return dt.to_pydatetime()
        except Exception:
            return None


def fetch_gdelt(query: str = '(financial OR bank OR inflation OR sanctions OR "rate hike")',
                max_records: int = 50, timespan: str = "15m", timeout: int = 12) -> pd.DataFrame:
    """Fetch current article metadata/headlines from GDELT DOC API.

    GDELT commonly returns article title, URL, domain and seen date; this function does NOT
    scrape full article bodies. The title/snippet received is the evidence scope by default.
    """
    params = {"query": query, "mode": "ArtList", "format": "json", "maxrecords": int(max_records),
              "timespan": timespan, "sort": "HybridRel"}
    response = requests.get(GDELT_URL, params=params, timeout=timeout, headers={"User-Agent":"FinRiskHackathon/1.0"})
    response.raise_for_status()
    payload = response.json()
    articles = payload.get("articles", [])
    rows=[]
    for item in articles:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        domain = str(item.get("domain") or urlparse(url).netloc or "GDELT")
        rows.append({
            "source": f"GDELT:{domain}", "publisher": domain,
            "published_at": parse_gdelt_datetime(item.get("seendate")),
            "headline": title, "source_url": url, "source_mode": "live_poll",
        })
    return pd.DataFrame(rows, columns=["source","publisher","published_at","headline","source_url","source_mode"])


def load_replay_data(data_dir: str | Path | None = None) -> pd.DataFrame:
    folder=Path(data_dir) if data_dir else ROOT/"data"
    news=pd.read_csv(folder/"sample_news.csv").fillna("")
    social=pd.read_csv(folder/"sample_social_posts.csv").fillna("")
    frame=pd.concat([news,social],ignore_index=True)
    if "publisher" not in frame:
        frame["publisher"]=frame["source"].astype(str)
    frame["published_at"]=pd.to_datetime(frame["published_at"],utc=True,errors="coerce")
    return frame


def load_demo_cases(data_dir: str | Path | None = None) -> pd.DataFrame:
    folder=Path(data_dir) if data_dir else ROOT/"data"
    frame=pd.read_csv(folder/"demo_cases.csv").fillna("")
    return frame
