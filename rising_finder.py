import numpy as np

def print_rising_moments(audio_data, threshold=0.3):
    """
    음성 데이터 리스트에서 0 부근에 있다가 임계값을 돌파하며 치솟는 '그 순간'만 출력합니다.
    
    :param audio_data: 녹음된 음성 샘플 리스트
    :param threshold: 치솟는 것으로 간주할 기준값 (절대값 기준)
    """
    print(f"--- 돌파 시점 분석 시작 (임계값: {threshold}) ---")
    
    # 분석을 위해 numpy 배열로 변환
    data = np.array(audio_data)
    abs_data = np.abs(data)
    
    detected_count = 0
    
    # 1번 인덱스부터 순회하며 이전 값과 현재 값을 비교
    for i in range(1, len(abs_data)):
        prev_val = abs_data[i-1]
        curr_val = abs_data[i]
        
        # 조건: 이전 값은 임계값 이하(0 부근)이고, 현재 값은 임계값을 초과(피크 시작)
        if prev_val <= threshold and curr_val > threshold:
            print(f"[검출] 인덱스: {i:7d} | 이전 값: {data[i-1]:.4f} -> 현재 값: {data[i]:.4f} (돌파!)")
            detected_count += 1
            
    if detected_count == 0:
        print("조건을 만족하는 돌파 시점이 없습니다.")
    else:
        print(f"--- 분석 완료: 총 {detected_count}번의 돌파 시점 발견 ---")
