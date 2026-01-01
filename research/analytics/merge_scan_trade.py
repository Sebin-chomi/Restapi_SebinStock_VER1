import pandas as pd
from pathlib import Path

def merge_scan_and_trades(scan_csv: Path, trade_csv: Path, output_csv: Path):
    scan = pd.read_csv(scan_csv)
    trades = pd.read_csv(trade_csv)

    merged = trades.merge(
        scan,
        on=["date", "symbol"],
        how="left",
        suffixes=("", "_scan")
    )

    output_csv.parent.mkdir(exist_ok=True, parents=True)
    merged.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"[MERGE DONE] rows={len(merged)} → {output_csv}")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent

    scan_csv = base / "data" / "scan" / "scan_result_2025-03.csv"
    trade_csv = base / "data" / "trades" / "trade_log_2025-03.csv"
    output_csv = base / "output" / "merged_2025-03.csv"

    merge_scan_and_trades(scan_csv, trade_csv, output_csv)
