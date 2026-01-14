# main.py
import os
import sys

# [중요] sounddevice를 import하기 전에 반드시 먼저 실행되어야 합니다.
# 원본 코드의 핵심 로직입니다.
os.environ["SD_ENABLE_ASIO"] = "1"

import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import config
from utils import bars_to_sleep_ms
from audio_engine import AudioHandler
from visualizer import create_waveform_with_metronome, save_analysis_image

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
        # 2. 장치 설정 (원본 코드 로직 그대로 복원)
        # ASIO 장치 정보를 가져옵니다.
        info = sd.query_devices(config.ASIO_DEVICE_ID)
        
        # 원본 코드: 입력/출력 중 작은 채널 수를 공통 채널 수로 사용
        channels = min(info["max_input_channels"], info["max_output_channels"])
        
        print(f"DEVICE: {info['name']}")
        print(f"CHANNELS: {channels} (ASIO Mode)")

        # 3. 스트림 실행
        with sd.Stream(
            device=config.ASIO_DEVICE_ID,
            samplerate=config.SAMPLE_RATE,
            blocksize=config.BLOCK_SIZE,
            dtype="float32",
            channels=channels,  # 원본대로 단일 정수값 전달
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

        # 4. 결과 저장
        audio_data = audio_handler.get_recorded_array()
        
        if len(audio_data) == 0:
            print("❌ 녹음된 데이터가 없습니다.")
            return

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