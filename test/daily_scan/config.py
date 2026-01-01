# =====================================================
# 🔁 장 마감 후, 종목 필터링을 위한 설정 값
# =====================================================

SCAN_VERSION = "scan_v1.0"

# Watch tier cut
WATCH_TIER_1 = 80
WATCH_TIER_2 = 65

# Liquidity hard filter
MIN_TRADING_VALUE = 50_000_000_000  # 50억

# Feature parameters
VOLUME_AVG_PERIOD = 20
ATR_PERIOD = 14

# Scan behavior flags (for future use)
ENABLE_POST_MARKET_SCAN = True      # 지금은 수동 실행만
SAVE_RAW_FEATURES = True            # 원본 지표 저장 여부
