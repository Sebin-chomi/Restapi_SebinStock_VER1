import asyncio 
import websockets
import json
import random
from config import socket_url
from check_n_buy import chk_n_buy
from get_setting import get_setting
from login import fn_au10001 as get_token

class RealTimeSearch:
    def __init__(self, on_connection_closed=None):
        self.socket_url = socket_url + '/api/dostk/websocket'
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.receive_task = None
        self.on_connection_closed = on_connection_closed
        self.token = None

    async def connect(self, token):
        """WebSocket 서버 연결 및 로그인"""
        try:
            self.token = token
            print(f"🌐 실시간 서버({self.socket_url}) 연결 시도...")
            self.websocket = await websockets.connect(self.socket_url)
            self.connected = True
            
            # 로그인 패킷 전송
            login_packet = {'trnm': 'LOGIN', 'token': token}
            await self.send_message(login_packet)
            print("📤 로그인 패킷 전송 완료")
        except Exception as e:
            print(f'❌ 연결 에러: {e}')
            self.connected = False

    async def send_message(self, message):
        if self.connected and self.websocket:
            if not isinstance(message, str):
                message = json.dumps(message)
            await self.websocket.send(message)

    async def receive_messages(self):
        """서버로부터 메시지를 계속 받아 처리하는 루프"""
        print("📥 메시지 수신 루프가 시작되었습니다.")
        while self.keep_running and self.connected and self.websocket:
            try:
                raw_message = await self.websocket.recv()
                response = json.loads(raw_message)

                # 1. PING 처리 (연결 유지용)
                if response.get('trnm') == 'PING':
                    await self.send_message(response)
                    continue

                # 2. 실시간 종목 포착 시 (REAL)
                if response.get('trnm') == 'REAL' and response.get('data'):
                    items = response['data']
                    for item in items:
                        vals = item.get('values', {})
                        jmcode = vals.get('9001')
                        if jmcode:
                            price = abs(float(vals.get('10', 0)))
                            volume = int(vals.get('13', 0))
                            avg_vol = int(vals.get('avg_vol', 0))
                            
                            # [중요] run_in_executor를 사용하여 비동기 루프 방해 없이 매수 체크 실행
                            loop = asyncio.get_running_loop()
                            loop.run_in_executor(
                                None, chk_n_buy, jmcode, price, volume, avg_vol, self.token
                            )

                # 3. 로그인 및 목록 요청 처리
                elif response.get('trnm') == 'LOGIN':
                    print(f"✅ 서버 응답: {response.get('return_msg')}")
                    await self.send_message({'trnm': 'CNSRLST'}) # 조건식 목록 요청

                elif response.get('trnm') == 'CNSRLST':
                    print("📋 조건식 목록 수신 완료")

            except websockets.ConnectionClosed:
                print("⚠️ 웹소켓 연결이 종료되었습니다.")
                break
            except Exception as e:
                print(f"⚠️ 수신 루프 에러: {e}")
                await asyncio.sleep(1)

    async def start(self, token):
        self.keep_running = True
        await self.connect(token)
        if self.connected:
            # 백그라운드에서 메시지 수신 시작
            self.receive_task = asyncio.create_task(self.receive_messages())
            
            # 설정된 조건식 번호로 실시간 검색 등록
            seq = get_setting('search_seq', '1') # 기본값 1
            await asyncio.sleep(1)
            await self.send_message({
                'trnm': 'CNSRREQ',
                'seq': seq,
                'search_type': '1',
                'stex_tp': 'K',
            })
            print(f"🚀 조건식 {seq}번으로 실시간 감시를 시작했습니다.")
            return True
        return False