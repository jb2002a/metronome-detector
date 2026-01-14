import sounddevice as sd
import numpy as np

# 설정
DEVICE_ID = 24  # Analogue 1 + 2 (Focusrite USB Audio), WASAPI
FS = 44100      # 샘플링 레이트
BLOCK_SIZE = 512 # 약 11.6ms 단위로 분석

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    
    # 스칼렛 1번 입력(왼쪽 채널)의 최대 진폭 계산
    # indata는 (512, 2) 형태의 배열입니다.
    volume = np.max(np.abs(indata[:, 0]))
    
    # 텍스트로 볼륨 시각화 (터미널에서 게이지가 움직임)
    gauge = int(volume * 100)
    print(f"입력 강도: [{'#' * gauge}{' ' * (100 - gauge)}] {volume:.4f}", end='\r')

try:
    print(f"스칼렛 2i2 (ID: {DEVICE_ID}) 입력을 시작합니다.")
    with sd.InputStream(device=DEVICE_ID,
                        channels=2,
                        samplerate=FS,
                        blocksize=BLOCK_SIZE,
                        callback=audio_callback):
        while True:
            sd.sleep(100)
except KeyboardInterrupt:
    print("\n중단되었습니다.")