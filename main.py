import os
import sys

# [중요] sounddevice를 import하기 전에 반드시 먼저 실행되어야 합니다.
os.environ["SD_ENABLE_ASIO"] = "1"

import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import config
from utils import bars_to_sleep_ms
from audio_engine import AudioHandler
from visualizer import create_waveform_with_metronome, save_analysis_image

def detect_and_print_specific_peaks(audio_array, threshold=0.5, silence_threshold=0.01):
    """
    0.01 수준의 정적 상태에서 0.5 이상으로 치솟는 첫 번째 샘플만 감지하여 출력합니다.
    """
    print(f"\n{'*'*20} 정적($0.01$) -> 피크($0.5$) 분석 시작 {'*'*20}")
    
    # 채널 처리 (첫 번째 채널 사용)
    if len(audio_array.shape) > 1:
        signal = audio_array[:, 0]
    else:
        signal = audio_array

    abs_signal = np.abs(signal)
    detected_count = 0
    
    # 상태 관리 변수
    # True: 현재 정적 상태이며 피크를 기다림
    # False: 현재 음이 지속 중이거나 감지 후 대기 중
    is_looking_for_start = True 
    
    # 음이 끝났다고 판단하기 위해 필요한 연속 정적 샘플 수 (예: 50ms)
    # 44100Hz 기준 약 2205 샘플
    required_silence_duration = int(config.SAMPLE_RATE * 0.05) 
    silence_counter = 0

    for i in range(len(abs_signal)):
        curr_val = abs_signal[i]

        if is_looking_for_start:
            # 1. 정적 상태에서 0.5를 돌파하는 순간 포착
            if curr_val >= threshold:
                print(f"[피크 감지] Index: {i:8d} | 값: {signal[i]:.4f}")
                detected_count += 1
                is_looking_for_start = False # 감지 상태 해제 (다음 정적까지 대기)
                silence_counter = 0
        else:
            # 2. 다시 0.01 부근으로 돌아왔는지 확인 (진동 중 0점을 지나는 것과 구별 필요)
            if curr_val < silence_threshold:
                silence_counter += 1
            else:
                silence_counter = 0 # 중간에 다시 커지면 카운트 리셋

            # 일정 시간(duration) 동안 계속 조용하다면 다시 탐색 준비
            if silence_counter >= required_silence_duration:
                is_looking_for_start = True

    if detected_count == 0:
        print(f"조건($0.01$ -> $0.5$)을 만족하는 지점이 없습니다.")
    else:
        print(f"\n총 {detected_count}개의 유효한 연주 시작 지점을 발견했습니다.")
    print(f"{'*'*60}\n")

def main():
    # 1. 초기화
    audio_handler = AudioHandler()
    
    countin_ms, countin_beats = bars_to_sleep_ms(
        config.COUNTIN_BARS, config.METRONOME_BPM, config.SAMPLE_RATE, config.BEATS_PER_BAR
    )

    print(f"{'='*70}")
    print(f"🎸 크로매틱 분석기 ({config.METRONOME_BPM} BPM)")
    print(f"⏱️  카운트인: {config.COUNTIN_BARS} bar ({countin_beats} beats)")
    print(f"📊 녹음 시간: {config.RECORD_DURATION}초")
    print(f"{'='*70}\n")

    try:
        # 2. 장치 설정
        info = sd.query_devices(config.ASIO_DEVICE_ID)
        channels = min(info["max_input_channels"], info["max_output_channels"])
        
        print(f"DEVICE: {info['name']}")
        print(f"CHANNELS: {channels} (ASIO Mode)")

        # 3. 스트림 실행
        with sd.Stream(
            device=config.ASIO_DEVICE_ID,
            samplerate=config.SAMPLE_RATE,
            blocksize=config.BLOCK_SIZE,
            dtype="float32",
            channels=channels,
            callback=audio_handler.callback,
        ):
            audio_handler.metronome_active = True
            print(f"🎼 카운트인 시작! ({config.COUNTIN_BARS} bar)")
            sd.sleep(countin_ms)

            # 녹음 정렬 및 시작
            audio_handler.reset_state()
            audio_handler.is_recording = True
            
            print("\n🚀 녹음 시작! 크로매틱 연주 Go!\n")
            
            for i in range(config.RECORD_DURATION, 0, -1):
                bar = "█" * (config.RECORD_DURATION - i + 1) + "░" * (i - 1)
                print(f"  ⏱️  [{bar}] {i:2d}초 남음", end="\r")
                sd.sleep(1000)

            audio_handler.metronome_active = False
            audio_handler.is_recording = False

        print("\n\n✓ 녹음 완료! 분석 중...")

        # 4. 결과 데이터 추출
        audio_data = audio_handler.get_recorded_array()
        
        if len(audio_data) == 0:
            print("❌ 녹음된 데이터가 없습니다.")
            return

        # 5. 사용자가 요청한 0.01 -> 0.5 급증 구간 분석 적용
        detect_and_print_specific_peaks(audio_data, threshold=0.5, silence_threshold=0.01)

        # 6. 시각화 및 결과 저장
        fig = create_waveform_with_metronome(audio_data)
        filename = save_analysis_image(fig)

        print(f"\n✅ 분석 완료: {filename}")
        plt.show()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()