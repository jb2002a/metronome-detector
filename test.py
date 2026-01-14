import os
import numpy as np

# ASIO 활성화 (임포트 전 필수 실행)
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd

# --- 사용자 설정 파라미터 ---
ASIO_DEVICE_ID = 18 
SAMPLE_RATE = 44100
BLOCK_SIZE = 64
SOFTWARE_GAIN = 60.0  # 확인된 증폭 값 (0.008 수준의 입력을 위해 60배 설정)
# --------------------------

def debug_callback(indata, outdata, frames, time, status):
    if status:
        print(f"Status: {status}")
    
    # 1. 신호 검출 및 피크 값 계산 (터미널 출력용)
    peaks = np.max(np.abs(indata), axis=0)
    
    # 2. 증폭 및 모니터링 로직 (CH 0 입력을 모든 출력 채널로 전달)
    # 1번 단자(CH 0)의 신호를 가져와 게인을 곱합니다.
    guitar_signal = indata[:, 0] * SOFTWARE_GAIN
    
    # 디지털 클리핑 방지 (리미터)
    guitar_signal = np.clip(guitar_signal, -1.0, 1.0)
    
    # 모든 출력 채널(L, R 등)에 증폭된 기타 신호를 복사하여 소리가 나게 함
    # outdata의 모든 열에 동일한 신호를 할당합니다.
    for i in range(outdata.shape[1]):
        outdata[:, i] = guitar_signal

    # 3. 신호가 감지될 때만 터미널에 수치 표시
    if np.any(peaks > 0.001):
        output_str = " | ".join([f"CH {i}: {p:.4f}" for i, p in enumerate(peaks)])
        print(f"Signal Detected -> {output_str} | Monitor: ON (Gain x{SOFTWARE_GAIN})")

try:
    # 장치 정보 확인
    info = sd.query_devices(ASIO_DEVICE_ID)
    max_inputs = info['max_input_channels']
    max_outputs = info['max_output_channels']
    
    print(f"장치 이름: {info['name']}")
    print(f"입력 채널: {max_inputs}, 출력 채널: {max_outputs}")
    print(f"설정: {SAMPLE_RATE}Hz / {BLOCK_SIZE} Samples / Gain x{SOFTWARE_GAIN}")

    # 입출력 채널 수를 결정합니다.
    channels = min(max_inputs, max_outputs)
    
    # 스트림 시작
    with sd.Stream(device=ASIO_DEVICE_ID,
                   samplerate=SAMPLE_RATE,
                   blocksize=BLOCK_SIZE,
                   channels=channels,
                   dtype='float32',
                   callback=debug_callback):
        
        print(f"\n[{channels}채널 모니터링 및 증폭 시작] 기타를 연주하세요...")
        while True:
            sd.sleep(1000)

except Exception as e:
    print(f"오류: {e}")