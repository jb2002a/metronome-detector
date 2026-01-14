import os
import sys

os.environ["SD_ENABLE_ASIO"] = "1"

import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import config
from utils import bars_to_sleep_ms
from audio_engine import AudioHandler
from visualizer import create_waveform_with_metronome, save_analysis_image
# 분리된 분석 함수를 임포트합니다.
from analyzer import detect_and_print_specific_peaks

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
        
        # 3. 스트림 실행 및 녹음
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

        # 4. 데이터 결과 처리
        audio_data = audio_handler.get_recorded_array()
        
        if len(audio_data) == 0:
            print("❌ 녹음된 데이터가 없습니다.")
            return

        # 5.  피크 감지 수행 및 인덱스 획득
        detected_indices = detect_and_print_specific_peaks(audio_data, threshold=0.25, silence_threshold=0.1)

        # 6. 시각화 및 이미지 저장
        fig = create_waveform_with_metronome(audio_data, detected_indices=detected_indices)
        filename = save_analysis_image(fig)

        print(f"\n✅ 분석 완료: {filename}")
        plt.show()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()