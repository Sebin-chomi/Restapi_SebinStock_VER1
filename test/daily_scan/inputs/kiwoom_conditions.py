import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_condition_result(tag: str) -> list[str]:
    """
    tag: 'A_volume_burst' | 'B_volatility_jump' | 'C_volume_accum'
    return: ['005930', '000660', ...]
    """
    file_path = BASE_DIR / f"{tag}.csv"

    if not file_path.exists():
        print(f"[WARN] CSV not found: {file_path}")
        return []

    symbols = []

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get("symbol")
            if symbol:
                symbols.append(symbol.strip())

    return symbols



""" # 미래 버전 - 나중에는 이것만 바꾸면 된다
def load_condition_result(tag):
    return kiwoom_api.get_condition_result(tag)
 """