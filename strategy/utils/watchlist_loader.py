import csv
from pathlib import Path
from datetime import datetime


def load_watchlist(scan_date: str | None = None) -> dict:
    """
    TEST / LIVE 공용 watchlist 로더
    - TEST 기준: TEST/watchlist/output/watchlist_YYYY-MM-DD.csv
    - 반환값: { code: {watch_tier, score_total, source_tags} }
    """

    if scan_date is None:
        scan_date = datetime.now().strftime("%Y-%m-%d")

    # ==================================================
    # 🔑 TEST 기준 경로 설정
    # ==================================================
    # strategy/utils/watchlist_loader.py 기준
    # parents[2] → TEST/
    base = Path(__file__).resolve().parents[2]
    watchlist_dir = base / "watchlist" / "output"
    path = watchlist_dir / f"watchlist_{scan_date}.csv"

    watch = {}

    if not path.exists():
        print(f"[WARN] watchlist not found: {path}")
        return watch

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            code = r["code"].strip()

            watch[code] = {
                "watch_tier": r["watch_tier"].strip(),
                "score_total": float(r["score_total"]),
                "source_tags": r.get("source_tags", "").strip(),
            }

    print(f"[INFO] watchlist loaded: {len(watch)} symbols")
    return watch


def split_by_tier(watch: dict):
    """
    watch dict → tier별 분리
    """
    tier1 = {k: v for k, v in watch.items() if v["watch_tier"] == "TIER1"}
    tier2 = {k: v for k, v in watch.items() if v["watch_tier"] == "TIER2"}
    return tier1, tier2
