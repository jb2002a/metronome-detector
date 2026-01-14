import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import base64
from io import BytesIO
import threading

os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd

# --- 설정 ---
ASIO_DEVICE_ID = 18
SAMPLE_RATE = 44100
RECORD_DURATION = 10  # 10초 녹음
SOFTWARE_GAIN = 60.0
METRONOME_BPM = 120  # 메트로놈 BPM
CHROMATIC_ENABLED = True  # 크로매틱 클릭 활성화

# 녹음 버퍼
recorded_data = []

# 메트로놈 사운드 생성
def generate_metronome_click(duration_ms=50, frequency=1000, sample_rate=44100):
    """메트로놈 클릭 사운드 생성 (강박용)"""
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    # 사인파 + 엔벨로프
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-10 * t)  # 빠르게 감쇠
    return (tone * envelope * 0.3).astype(np.float32)

def generate_chromatic_click(duration_ms=30, frequency=1500, sample_rate=44100):
    """크로매틱 클릭 사운드 생성 (약박용 - 높은 음)"""
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    # 더 높은 주파수 + 짧은 지속시간
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-15 * t)  # 더 빠르게 감쇠
    return (tone * envelope * 0.2).astype(np.float32)

# 미리 사운드 생성
METRONOME_SOUND = generate_metronome_click()  # 강박 (1박)
CHROMATIC_SOUND = generate_chromatic_click()   # 약박 (크로매틱)

# 메트로놈 상태
metronome_active = False
current_beat = 0
beat_interval_samples = 0
sample_counter = 0

def audio_callback(indata, outdata, frames, time_info, status):
    global recorded_data, metronome_active, current_beat, sample_counter
    
    # 입력 증폭
    guitar_input = indata[:, 0]
    amplified = np.clip(guitar_input * SOFTWARE_GAIN, -1.0, 1.0)
    
    # 녹음
    recorded_data.extend(amplified)
    
    # 메트로놈 + 기타 믹스
    output_signal = amplified.copy()
    
    if metronome_active:
        # 각 프레임마다 박자 체크
        for i in range(frames):
            if sample_counter >= beat_interval_samples:
                sample_counter = 0
                current_beat = (current_beat + 1) % 4
            sample_counter += 1
        
        # 클릭 사운드 삽입
        if sample_counter < len(METRONOME_SOUND):
            # 소절 첫 박 (1박) - 강한 클릭
            if current_beat == 0:
                click_len = min(len(METRONOME_SOUND) - sample_counter, frames)
                output_signal[:click_len] += METRONOME_SOUND[sample_counter:sample_counter + click_len]
            # 나머지 박 - 약한 클릭
            else:
                click_len = min(len(METRONOME_SOUND) - sample_counter, frames)
                output_signal[:click_len] += METRONOME_SOUND[sample_counter:sample_counter + click_len] * 0.6
        
        # 크로매틱 클릭 (8분음표 - 박 사이)
        if CHROMATIC_ENABLED:
            chromatic_position = beat_interval_samples // 2
            if chromatic_position - 100 < sample_counter < chromatic_position + len(CHROMATIC_SOUND):
                offset = sample_counter - chromatic_position
                if 0 <= offset < frames:
                    click_len = min(len(CHROMATIC_SOUND) - offset, frames - offset)
                    if click_len > 0 and offset >= 0:
                        output_signal[offset:offset + click_len] += CHROMATIC_SOUND[:click_len]
    
    # 출력
    output_signal = np.clip(output_signal, -1.0, 1.0)
    for i in range(outdata.shape[1]):
        outdata[:, i] = output_signal

def create_waveform_with_metronome(audio_data, bpm, sample_rate):
    """파형과 메트로놈 그리드를 시각화"""
    duration = len(audio_data) / sample_rate
    time_axis = np.linspace(0, duration, len(audio_data))
    
    # Figure 설정
    fig, ax = plt.subplots(figsize=(18, 7), dpi=100)
    
    # 파형 그리기
    ax.plot(time_axis, audio_data, color='#2E86DE', linewidth=0.5, alpha=0.8)
    ax.fill_between(time_axis, audio_data, alpha=0.3, color='#2E86DE')
    
    # 엔벨로프 추가 (타격 지점 강조)
    envelope = np.abs(audio_data)
    window_size = int(sample_rate * 0.01)  # 10ms 윈도우
    smoothed = np.convolve(envelope, np.ones(window_size)/window_size, mode='same')
    ax.plot(time_axis, smoothed, color='#E74C3C', linewidth=1.5, 
            alpha=0.6, label='Attack Envelope')
    
    # 메트로놈 그리드 (4/4박자)
    beat_interval = 60.0 / bpm  # 초 단위 (1박)
    chromatic_interval = beat_interval / 2  # 8분음표
    
    # 1박 단위 (강박/약박)
    beat_positions = np.arange(0, duration, beat_interval)
    for i, beat_pos in enumerate(beat_positions):
        # 소절 첫 박은 빨간색, 나머지는 주황색
        color = '#FF6B6B' if i % 4 == 0 else '#FFA502'
        linewidth = 2.5 if i % 4 == 0 else 1.5
        alpha = 0.8 if i % 4 == 0 else 0.6
        ax.axvline(beat_pos, color=color, linestyle='--', 
                   linewidth=linewidth, alpha=alpha)
    
    # 크로매틱 그리드 (8분음표 - 박 사이)
    if CHROMATIC_ENABLED:
        chromatic_positions = np.arange(chromatic_interval, duration, beat_interval)
        for chrom_pos in chromatic_positions:
            ax.axvline(chrom_pos, color='#95A5A6', linestyle=':', 
                       linewidth=1, alpha=0.5)
    
    # 스타일링
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Amplitude', fontsize=13, fontweight='bold')
    
    title = f'Guitar Performance Analysis | {bpm} BPM'
    if CHROMATIC_ENABLED:
        title += ' (Chromatic Grid Enabled)'
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    ax.set_facecolor('#F8F9FA')
    
    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2E86DE', alpha=0.3, label='Guitar Signal'),
        plt.Line2D([0], [0], color='#E74C3C', linewidth=1.5, label='Attack Envelope'),
        plt.Line2D([0], [0], color='#FF6B6B', linestyle='--', linewidth=2.5, label='Downbeat (1박)'),
        plt.Line2D([0], [0], color='#FFA502', linestyle='--', linewidth=1.5, label='Beat (2,3,4박)'),
    ]
    if CHROMATIC_ENABLED:
        legend_elements.append(
            plt.Line2D([0], [0], color='#95A5A6', linestyle=':', label='Chromatic (8분음표)')
        )
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    plt.tight_layout()
    return fig

def fig_to_base64(fig):
    """Figure를 base64 이미지로 변환"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_base64

def save_analysis_image(fig, filename=None):
    """이미지 저장"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"guitar_chromatic_{timestamp}.png"
    
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ 이미지 저장: {filename}")
    return filename

def record_and_analyze():
    global recorded_data, metronome_active, current_beat, sample_counter, beat_interval_samples
    recorded_data = []
    current_beat = 0
    sample_counter = 0
    
    # 박자 간격 계산
    beat_interval_samples = int(SAMPLE_RATE * 60.0 / METRONOME_BPM)
    
    print(f"{'='*70}")
    print(f"🎸 크로매틱 기타 연주 분석기 ({METRONOME_BPM} BPM)")
    print(f"{'='*70}")
    print(f"📊 녹음 시간: {RECORD_DURATION}초")
    print(f"🎵 박자: 4/4박자")
    print(f"✨ 크로매틱 그리드: {'활성화 (8분음표)' if CHROMATIC_ENABLED else '비활성화'}")
    print(f"{'='*70}\n")
    
    try:
        info = sd.query_devices(ASIO_DEVICE_ID)
        channels = min(info['max_input_channels'], info['max_output_channels'])
        
        # 녹음
        with sd.Stream(device=ASIO_DEVICE_ID,
                       samplerate=SAMPLE_RATE,
                       blocksize=512,
                       dtype='float32',
                       channels=channels,
                       callback=audio_callback):
            
            # 메트로놈 활성화
            metronome_active = True
            
            print("🎼 메트로놈 시작! 크로매틱 연주를 시작하세요!")
            print("   (강박 = 큰 소리, 약박 = 중간 소리, 크로매틱 = 작은 틱)")
            print()
            
            for i in range(RECORD_DURATION, 0, -1):
                bar = '█' * (RECORD_DURATION - i + 1) + '░' * (i - 1)
                print(f"  ⏱️  [{bar}] {i:2d}초 남음", end='\r')
                sd.sleep(1000)
            
            metronome_active = False
        
        print("\n\n✓ 녹음 완료! 분석 이미지 생성 중...")
        
        # 파형 이미지 생성
        audio_array = np.array(recorded_data)
        fig = create_waveform_with_metronome(audio_array, METRONOME_BPM, SAMPLE_RATE)
        
        # 이미지 저장
        filename = save_analysis_image(fig)
        
        # base64 인코딩 (Claude API 전송용)
        img_base64 = fig_to_base64(fig)
        
        print("\n" + "="*70)
        print("📊 분석 준비 완료!")
        print("="*70)
        print(f"✅ 이미지 파일: {filename}")
        print(f"✅ Base64 길이: {len(img_base64):,} 문자")
        print("\n💡 Claude에게 분석 요청 예시:")
        print("   '빨간 점선 = 소절 첫 박 (1박)")
        print("   '주황 점선 = 나머지 박 (2, 3, 4박)")
        print("   '회색 점선 = 크로매틱 (8분음표)")
        print("   '빨간 곡선 = 타격 강도 (엔벨로프)")
        print()
        print("   이 크로매틱 연주가 메트로놈에 얼마나 정확한지,")
        print("   어느 구간이 빠르고/느린지, 전체 정확도 %로 분석해줘'")
        print("="*70)
        
        plt.show()
        
        return filename, img_base64
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    record_and_analyze()
