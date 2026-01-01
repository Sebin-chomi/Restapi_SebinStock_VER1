from monthly_pnl_graph import generate_monthly_pnl_graph
from periodic_report import monthly_report, weekly_report
from risk_manager import clear_halt, get_pnl_status, halt_trading, is_trading_halted
from tel_send import send_message, send_photo
from weekly_pnl_graph import generate_weekly_pnl_graph

_app_ref = None


def register_app(app):
    global _app_ref
    _app_ref = app


def handle_command(text: str, token=None):
    text = text.strip().lower()

    # ===============================
    # 도움말
    # ===============================
    if text == "/help":
        send_message(
            "/status\n/pause\n/resume\n"
            "/weekly /weekly_graph\n"
            "/monthly /monthly_graph\n"
            "/add 종목\n/remove 종목\n/list"
        )
        return

    # ===============================
    # 원격 정지 / 재개
    # ===============================
    if text == "/pause":
        halt_trading()
        send_message("🛑 자동매매 일시 중단")
        return

    if text == "/resume":
        clear_halt()
        send_message("▶️ 자동매매 재개")
        return

    # ===============================
    # 상태 조회
    # ===============================
    if text == "/status":
        halted = is_trading_halted()
        status = get_pnl_status()

        if not status:
            send_message("📊 거래 데이터 없음")
            return

        manual_cnt = len(_app_ref.get_manual_watch_list()) if _app_ref else 0
        state = "🛑 중단" if halted else "🟢 정상"

        send_message(
            f"📊 자동매매 상태\n\n"
            f"상태: {state}\n"
            f"누적 PnL: {status['cum_pnl']:,}원\n"
            f"MDD: {status['mdd'] * 100:.2f}%\n"
            f"거래일수: {status['total_days']}일\n"
            f"수동 종목: {manual_cnt}개"
        )
        return

    # ===============================
    # 수동 종목 관리
    # ===============================
    if text.startswith("/add "):
        if _app_ref:
            _app_ref.add_manual_watch(text.split()[1])
        return

    if text.startswith("/remove "):
        if _app_ref and not _app_ref.remove_manual_watch(text.split()[1]):
            send_message("⚠️ 수동 종목 아님")
        return

    if text == "/list":
        if not _app_ref:
            return
        manual = _app_ref.get_manual_watch_list()
        send_message("📋 수동 종목\n" + "\n".join(manual) if manual else "📭 없음")
        return

    # ===============================
    # 리포트 / 그래프
    # ===============================
    if text == "/weekly":
        r = weekly_report()
        if r:
            send_message(str(r))
        return

    if text == "/weekly_graph":
        g = generate_weekly_pnl_graph()
        if g:
            send_photo(g["output_path"])
        return

    if text == "/monthly":
        r = monthly_report()
        if r:
            send_message(str(r))
        return

    if text == "/monthly_graph":
        g = generate_monthly_pnl_graph()
        if g:
            send_photo(g["output_path"])
        return

    send_message("❓ 알 수 없는 명령 (/help)")
