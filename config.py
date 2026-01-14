# config.py

# 오디오 장치 설정
ASIO_DEVICE_ID = 18
SAMPLE_RATE = 44100
BLOCK_SIZE = 64

# 녹음 설정
RECORD_DURATION = 10        # 녹음 시간(초)
SOFTWARE_GAIN = 60.0        # 소프트웨어 증폭

# 음악적 설정
METRONOME_BPM = 100
COUNTIN_BARS = 1            # 카운트인 마디 수
BEATS_PER_BAR = 4           # 박자표 (4/4)

# 시각화 설정
CHROMATIC_ENABLED = True    # 시각화 그리드 표시 여부
CHROMATIC_BEATS = 4        # 시각화 그리드 박자 수