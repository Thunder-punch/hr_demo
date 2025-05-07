import asyncio
import datetime
import logging
from bleak import BleakScanner

# 기본 설정: 강한 신호 임계치 (dBm). 임계치 이상의 신호는 강한 신호로 간주.
STRONG_SIGNAL_THRESHOLD = -40

# 로깅 설정 (시간, 로그 레벨, 메시지)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

def current_time() -> str:
    """현재 시간을 HH:MM:SS 형식의 문자열로 반환합니다."""
    return datetime.datetime.now().strftime('%H:%M:%S')

async def scan_and_display_strong_devices(scan_duration: int = 8) -> None:
    """
    지정된 시간(scan_duration) 동안 BLE 디바이스를 스캔하여,
    신호 강도가 STRONG_SIGNAL_THRESHOLD 이상인 디바이스의 정보를 로그로 출력합니다.
    """
    logging.info("스캔 시작 (duration: %d초)", scan_duration)
    
    try:
        devices = await BleakScanner.discover(timeout=scan_duration)
    except Exception as e:
        logging.error("스캔 중 에러 발생: %s", e)
        return

    found_strong = False
    for device in devices:
        # device.rssi는 dBm 단위의 신호 강도를 제공합니다.
        rssi = device.rssi
        if rssi is not None and rssi >= STRONG_SIGNAL_THRESHOLD:
            found_strong = True
            logging.info("강한 신호 발견: %s (%s)", device.name, device.address)
            logging.info("    RSSI: %d dBm", rssi)
            # 최신 버전 Bleak에서는 advertisement_data 속성을 사용하는 것이 권장됩니다.
            adv_data = getattr(device, "advertisement_data", None)
            if adv_data is not None:
                logging.info("    AdvertisementData: %s", adv_data)
            else:
                # 만약 advertisement_data가 없다면 (혹은 구버전), metadata 속성을 사용합니다.
                metadata = getattr(device, "metadata", {})
                if metadata:
                    logging.info("    Metadata: %s", metadata)
            logging.info("-" * 50)

    if not found_strong:
        logging.info("강한 신호를 가진 디바이스가 없습니다.")

async def main() -> None:
    await scan_and_display_strong_devices()

if __name__ == "__main__":
    asyncio.run(main())
