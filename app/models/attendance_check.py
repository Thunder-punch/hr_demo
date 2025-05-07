import asyncio
import datetime
import pyautogui
from bleak import BleakScanner

# Beacon 광고 데이터에서 고정된 해쉬값 (실제 해쉬값으로 수정하세요)
TARGET_HASH = "1006281a7e7495d1"  # 실제 Beacon의 고정 해쉬값으로 수정


async def check_for_beacon(scan_duration=8):
    """
    지정한 시간(scan_duration) 동안 BLE 스캔을 수행하여,
    Manufacturer Data의 해쉬값에 TARGET_HASH가 포함되어 있으면 True를 반환합니다.
    """
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{now_str}] 스캔 시작: 해쉬값 '{TARGET_HASH}' 검색 중...")
    try:
        devices = await BleakScanner.discover(timeout=scan_duration)
        for device in devices:
            # device.metadata에 "manufacturer_data"가 포함되어 있다면 확인합니다.
            manufacturer_data = device.metadata.get("manufacturer_data", {})
            for mfg_id, mfg_bytes in manufacturer_data.items():
                hex_str = mfg_bytes.hex()  # bytes를 hex 문자열로 변환
                if TARGET_HASH.lower() in hex_str.lower():
                    now_str = datetime.datetime.now().strftime('%H:%M:%S')
                    print(f"[{now_str}] Beacon 발견: {device.name} ({device.address}), 해쉬: {hex_str}")
                    return True
    except Exception as e:
        now_str = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{now_str}] 스캔 중 에러 발생: {e}")
    
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{now_str}] 해쉬값 '{TARGET_HASH}' 미발견")
    return False

async def attendance_loop():
    """
    BLE 스캔을 주기적으로 수행하여, TARGET_HASH가 포함된 Beacon이 발견되면
    채팅창에 출근 메시지를 전송하고 루프를 종료합니다.
    """
    prev_state = False
    scan_interval = 10  # 10초 간격
    while True:
        try:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] 출석 체크 루프 시작")
            found = await check_for_beacon(scan_duration=8)
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] 스캔 결과: {found} (이전 상태: {prev_state})")
            
            if found and not prev_state:
                now = datetime.datetime.now().strftime("%H:%M")
                first_message = "정태우 현 시간 출근"
                chat_message = f"정태우 출근했습니다. ({now})"
                
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"[{now_str}] 출석 체크 메시지 전송 시작")
                # 채팅창이 미리 활성화되어 있어야 합니다.
                pyautogui.typewrite(first_message, interval=0.05)
                pyautogui.press("enter")
                await asyncio.sleep(1)
                pyautogui.typewrite(chat_message, interval=0.05)
                pyautogui.press("enter")
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"[{now_str}] 출석 체크 메시지 전송 완료!")
                print(f"[{now_str}] Beacon 발견 후 루프 정지")
                break  # Beacon 발견 후 루프 종료
            
            prev_state = found

        except Exception as e:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] 출석 체크 루프 에러: {e}")
        
        await asyncio.sleep(scan_interval)

if __name__ == "__main__":
    asyncio.run(attendance_loop())