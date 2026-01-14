import numpy as np
import config

def detect_and_print_specific_peaks(audio_array, threshold=0.25, silence_threshold=0.05):
    """
    정적 상태(silence_threshold)에서 피크(threshold)로 치솟는 순간을 감지하여 인덱스 리스트를 반환합니다.
    """
    print(f"\n{'*'*20} 정적({silence_threshold}) -> 피크({threshold}) 분석 시작 {'*'*20}")
    
    # 채널 처리 (다채널일 경우 첫 번째 채널 사용)
    if len(audio_array.shape) > 1:
        signal = audio_array[:, 0]
    else:
        signal = audio_array

    abs_signal = np.abs(signal)
    detected_indices = []
    
    is_looking_for_start = True 
    # 정적 판단을 위한 최소 지속 시간 (50ms)
    required_silence_duration = int(config.SAMPLE_RATE * 0.05) 
    silence_counter = 0

    for i in range(len(abs_signal)):
        curr_val = abs_signal[i]

        if is_looking_for_start:
            # 정적 상태에서 임계값을 돌파하는 시점 포착
            if curr_val >= threshold:
                print(f"[피크 감지] Index: {i:8d} | 시각: {i/config.SAMPLE_RATE:.3f}s | 값: {signal[i]:.4f}")
                detected_indices.append(i)
                is_looking_for_start = False 
                silence_counter = 0
        else:
            # 다시 정적 상태로 돌아오는지 감시
            if curr_val < silence_threshold:
                silence_counter += 1
            else:
                silence_counter = 0 

            if silence_counter >= required_silence_duration:
                is_looking_for_start = True

    if not detected_indices:
        print(f"조건을 만족하는 지점이 없습니다.")
    else:
        print(f"\n총 {len(detected_indices)}개의 유효한 연주 시작 지점을 발견했습니다.")
    print(f"{'*'*60}\n")
    
    return detected_indices