# ===============================
# test/framework/telegram_handler.py
# ===============================
import asyncio
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

from test.framework.watchlist.store import add_stock, remove_stock, get_watchlist
from test.framework.watchlist.manual_additions import (
    add_manual_symbol,
    remove_manual_symbol,
    get_manual_symbols,
)
from test.tel_logger import tel_log


def send_message(text: str):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ 텔레그램 메시지 전송 실패: {e}")


def handle_command(text: str):
    """텔레그램 명령어 처리"""
    text = text.strip().lower()
    
    # 도움말
    if text == "/help":
        send_message(
            "📋 정찰봇 명령어\n\n"
            "/add 종목코드 - 종목 추가 (당일 한정, 장 마감 후 자동 제거)\n"
            "/remove 종목코드 - 종목 제거\n"
            "/list - 현재 watchlist 확인\n"
            "/status - 상태 확인"
        )
        return
    
    # 종목 추가
    if text.startswith("/add "):
        parts = text.split()
        if len(parts) < 2:
            send_message("❌ 사용법: /add 종목코드\n예: /add 005930")
            return
        
        stk_cd = parts[1].strip()
        
        # 1. 즉시 반영 (실시간 감시용)
        add_stock(stk_cd)
        
        # 2. 영속 저장 (파일)
        file_saved = add_manual_symbol(stk_cd, reason="/add command")
        
        if file_saved:
            current_list = get_watchlist()
            manual_count = len(get_manual_symbols())
            tel_log(
                "WATCHLIST",
                f"➕ 종목 추가: {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목\n"
                f"수동 추가 (당일 한정): {manual_count} 종목"
            )
            send_message(
                f"✅ 종목 추가됨: {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목\n"
                f"수동 추가 (당일 한정): {manual_count} 종목\n"
                f"💡 장 마감 후 자동으로 제거됩니다."
            )
        else:
            # 파일 저장 실패해도 메모리는 추가됨 (실시간 감시는 계속)
            current_list = get_watchlist()
            tel_log(
                "WATCHLIST",
                f"➕ 종목 추가 (메모리만): {stk_cd}\n"
                f"⚠️ 파일 저장 실패 (재시작 시 사라질 수 있음)\n"
                f"현재 watchlist: {len(current_list)} 종목"
            )
            send_message(
                f"✅ 종목 추가됨: {stk_cd}\n"
                f"⚠️ 파일 저장 실패 (재시작 시 사라질 수 있음)\n"
                f"현재 watchlist: {len(current_list)} 종목\n"
                f"💡 장 마감 후 자동으로 제거됩니다."
            )
        return
    
    # 종목 제거
    if text.startswith("/remove "):
        parts = text.split()
        if len(parts) < 2:
            send_message("❌ 사용법: /remove 종목코드\n예: /remove 005930")
            return
        
        stk_cd = parts[1].strip()
        
        # 1. 즉시 반영 (실시간 감시용)
        remove_stock(stk_cd)
        
        # 2. 영속 저장에서도 제거
        file_removed = remove_manual_symbol(stk_cd)
        
        current_list = get_watchlist()
        manual_count = len(get_manual_symbols())
        
        if file_removed:
            tel_log(
                "WATCHLIST",
                f"➖ 종목 제거: {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목\n"
                f"수동 추가: {manual_count} 종목"
            )
            send_message(
                f"✅ 종목 제거됨: {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목\n"
                f"수동 추가 (당일 한정): {manual_count} 종목"
            )
        else:
            tel_log(
                "WATCHLIST",
                f"➖ 종목 제거 (메모리만): {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목"
            )
            send_message(
                f"✅ 종목 제거됨: {stk_cd}\n"
                f"현재 watchlist: {len(current_list)} 종목"
            )
        return
    
    # 현재 watchlist 확인
    if text == "/list":
        current_list = get_watchlist()
        if current_list:
            msg = f"📋 현재 watchlist ({len(current_list)} 종목):\n" + "\n".join(current_list)
        else:
            msg = "📭 watchlist가 비어있습니다."
        send_message(msg)
        return
    
    # 상태 확인
    if text == "/status":
        current_list = get_watchlist()
        send_message(
            f"📊 정찰봇 상태\n\n"
            f"현재 watchlist: {len(current_list)} 종목\n"
            f"종목: {', '.join(current_list[:10])}{'...' if len(current_list) > 10 else ''}"
        )
        return
    
    # 알 수 없는 명령
    send_message("❓ 알 수 없는 명령 (/help로 도움말 확인)")


async def telegram_polling():
    """텔레그램 메시지 폴링 (비동기)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  텔레그램 설정이 없습니다. 폴링을 시작할 수 없습니다.")
        return
    
    print(f"📡 텔레그램 폴링 시작 (Chat ID: {TELEGRAM_CHAT_ID})")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    last_update_id = None
    
    # 기존 업데이트 클리어 (다른 인스턴스와의 충돌 방지)
    try:
        loop = asyncio.get_event_loop()
        clear_response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, params={"offset": -1, "timeout": 1}, timeout=5)
        )
        if clear_response.json().get("ok"):
            updates = clear_response.json().get("result", [])
            if updates:
                last_update_id = max(u.get("update_id", 0) for u in updates)
                print(f"🧹 기존 업데이트 {len(updates)}건 클리어 (last_update_id: {last_update_id})")
    except Exception as e:
        print(f"⚠️  기존 업데이트 클리어 실패 (무시): {e}")
    
    while True:
        try:
            params = {"timeout": 30}
            if last_update_id:
                params["offset"] = last_update_id + 1
            
            # 동기 requests를 비동기로 실행 (이벤트 루프 블로킹 방지)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, params=params, timeout=35)
            )
            
            data = response.json()
            
            if not data.get("ok"):
                error_desc = data.get("description", "알 수 없는 오류")
                
                # Conflict 오류는 다른 인스턴스가 실행 중일 때 발생
                if "Conflict" in error_desc or "terminated by other getUpdates" in error_desc:
                    print(f"⚠️  텔레그램 API 충돌: 다른 봇 인스턴스가 실행 중입니다.")
                    print(f"   💡 해결 방법: 다른 정찰봇 프로세스를 종료하세요.")
                    # 충돌 시 더 긴 대기
                    await asyncio.sleep(10)
                else:
                    print(f"⚠️  텔레그램 API 오류: {error_desc}")
                    await asyncio.sleep(5)
                continue
            
            updates = data.get("result", [])
            if updates:
                print(f"📨 텔레그램 메시지 {len(updates)}건 수신")
            
            for update in updates:
                last_update_id = update.get("update_id")
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                
                print(f"📩 메시지 수신: chat_id={chat_id}, text={text[:50]}")
                
                # 본인 채팅만 처리
                if str(chat_id) == str(TELEGRAM_CHAT_ID):
                    if text.startswith("/"):
                        print(f"✅ 명령어 처리: {text}")
                        handle_command(text)
                    else:
                        print(f"ℹ️  일반 메시지 (명령어 아님): {text[:50]}")
                else:
                    print(f"⚠️  다른 사용자 메시지 (무시): chat_id={chat_id}")
            
        except KeyboardInterrupt:
            # Ctrl+C로 종료 시 정상 종료
            print("\n📡 텔레그램 폴링 종료")
            break
        except asyncio.CancelledError:
            # 태스크 취소 시 정상 종료
            print("\n📡 텔레그램 폴링 취소됨")
            break
        except Exception as e:
            print(f"❌ 텔레그램 폴링 오류: {e}")
            await asyncio.sleep(5)

