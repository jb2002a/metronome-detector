import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import base64
from io import BytesIO

os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd

# --- 설정 ---
ASIO_DEVICE_ID = 18
SAMPLE_RATE = 44100
RECORD_DURATION = 10  # 10초 녹음
COUNTIN_DURATION = 3  # 3초 카운트인
SOFTWARE_GAIN = 60.0
METRONOME_BPM = 120  # 메트로놈 BPM
CHROMATIC_ENABLED = True  # 크로매틱 클릭 활성화

# 녹음 버퍼
recorded_data = []
is_recording = False

# 메트로놈 사운드 생성
def generate_metronome_click(duration_ms=50, frequency=1000, sample_rate=44100):
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-10 * t)
    return (tone * envelope * 0.3).astype(np.float32)

def generate_chromatic_click(duration_ms=30, frequency=1500, sample_rate=44100):
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-15 * t)
    return (tone * envelope * 0.2).astype(np.float32)

def generate_countin_click(duration_ms=80, frequency=800, sample_rate=44100):
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-8 * t)
    return (tone * envelope * 0.5).astype(np.float32)

METRONOME_SOUND = generate_metronome_click()
CHROMATIC_SOUND = generate_chromatic_click()
COUNTIN_SOUND = generate_countin_click()

metronome_active = False
current_beat = 0
beat_interval_samples = 0
sample_counter = 0

def audio_callback(indata, outdata, frames, time_info, status):
    global recorded_data, metronome_active, current_beat, sample_counter, is_recording
    
    guitar_input = indata[:, 0]
    amplified = np.clip(guitar_input * SOFTWARE_GAIN, -1.0, 1.0)
    
    if is_recording:
        recorded_data.extend(amplified)
    
    output_signal = amplified.copy()
    
    if metronome_active:
        for i in range(frames):
            if sample_counter >= beat_interval_samples:
                sample_counter = 0
                current_beat = (current_beat + 1) % 4
            sample_counter += 1
        
        # 카운트인과 녹음 모두 동일한 메트로놈 (4박 강약 없이 통일)
        if sample_counter < len(METRONOME_SOUND):
            click_len = min(len(METRONOME_SOUND) - sample_counter, frames)
            output_signal[:click_len] += METRONOME_SOUND[sample_counter:sample_counter + click_len]
        
        # 크로매틱 클릭 (8분음표)
        if CHROMATIC_ENABLED:
            chromatic_position = beat_interval_samples // 2
            if chromatic_position - 100 < sample_counter < chromatic_position + len(CHROMATIC_SOUND):
                offset = sample_counter - chromatic_position
                if 0 <= offset < frames:
                    click_len = min(len(CHROMATIC_SOUND) - offset, frames - offset)
                    if click_len > 0 and offset >= 0:
                        output_signal[offset:offset + click_len] += CHROMATIC_SOUND[:click_len]
    
    output_signal = np.clip(output_signal, -1.0, 1.0)
    for i in range(outdata.shape[1]):
        outdata[:, i] = output_signal

def create_waveform_with_metronome(audio_data, bpm, sample_rate):
    """파형과 심플 그리드 시각화"""
    duration = len(audio_data) / sample_rate
    time_axis = np.linspace(0, duration, len(audio_data))
    
    # Figure 설정
    fig, ax = plt.subplots(figsize=(18, 7), dpi=100)
    
    # 파형 그리기
    ax.plot(time_axis, audio_data, color='#2E86DE', linewidth=0.5, alpha=0.8)
    ax.fill_between(time_axis, audio_data, alpha=0.3, color='#2E86DE')
    
    # 메트로놈 그리드 - 모두 빨간 점선으로 통일
    beat_interval = 60.0 / bpm  # 초 단위 (1박)
    chromatic_interval = beat_interval / 2  # 8분음표
    
    # 모든 그리드 포인트 수집 (1박 + 8분음표)
    all_grid_points = []
    
    # 1박 단위
    beat_positions = np.arange(0, duration, beat_interval)
    all_grid_points.extend(beat_positions)
    
    # 크로매틱 (8분음표 - 박 사이)
    if CHROMATIC_ENABLED:
        chromatic_positions = np.arange(chromatic_interval, duration, beat_interval)
        all_grid_points.extend(chromatic_positions)
    
    # 정렬 후 중복 제거
    all_grid_points = sorted(set(all_grid_points))
    
    # 모든 그리드를 빨간 점선으로 그리기
    for grid_pos in all_grid_points:
        ax.axvline(grid_pos, color='#FF6B6B', linestyle='--', 
                   linewidth=1.5, alpha=0.7)
    
    # 스타일링
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Amplitude', fontsize=13, fontweight='bold')
    
    title = f'Guitar Performance Analysis | {bpm} BPM'
    if CHROMATIC_ENABLED:
        title += ' (8th Note Grid)'
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    ax.set_facecolor('#F8F9FA')
    
    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2E86DE', alpha=0.3, label='Guitar Signal'),
        plt.Line2D([0], [0], color='#FF6B6B', linestyle='--', linewidth=1.5, 
                   label=f'Grid ({bpm} BPM, 8th notes)'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    plt.tight_layout()
    return fig

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_base64

def save_analysis_image(fig, filename=None):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"guitar_chromatic_{timestamp}.png"
    
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ 이미지 저장: {filename}")
    return filename

def record_and_analyze():
    global recorded_data, metronome_active, current_beat, sample_counter, beat_interval_samples, is_recording
    recorded_data = []
    current_beat = 0
    sample_counter = 0
    is_recording = False
    
    beat_interval_samples = int(SAMPLE_RATE * 60.0 / METRONOME_BPM)
    
    print(f"{'='*70}")
    print(f"🎸 심플 그리드 크로매틱 분석기 ({METRONOME_BPM} BPM)")
    print(f"{'='*70}")
    print(f"⏱️  카운트인: {COUNTIN_DURATION}초")
    print(f"📊 녹음 시간: {RECORD_DURATION}초")
    print(f"🎵 박자: 4/4박자 (8분음표 그리드)")
    print(f"{'='*70}\n")
    
    try:
        info = sd.query_devices(ASIO_DEVICE_ID)
        channels = min(info['max_input_channels'], info['max_output_channels'])
        
        with sd.Stream(device=ASIO_DEVICE_ID,
                       samplerate=SAMPLE_RATE,
                       blocksize=512,
                       dtype='float32',
                       channels=channels,
                       callback=audio_callback):
            
            metronome_active = True
            
            print("🎼 카운트인 시작! (메트로놈만 들림)")
            print("   준비하세요...\n")
            
            beats_per_countin = int(COUNTIN_DURATION * METRONOME_BPM / 60)
            for i in range(COUNTIN_DURATION, 0, -1):
                current_bar = ((COUNTIN_DURATION - i) * METRONOME_BPM // 60) + 1
                total_bars = beats_per_countin
                bar_display = '█' * current_bar + '░' * (total_bars - current_bar)
                print(f"  🎵 [{bar_display}] {i}초 전", end='\r')
                sd.sleep(1000)
            
            print("\n\n🚀 녹음 시작! 크로매틱 연주 Go!\n")
            
            is_recording = True
            
            for i in range(RECORD_DURATION, 0, -1):
                bar = '█' * (RECORD_DURATION - i + 1) + '░' * (i - 1)
                print(f"  ⏱️  [{bar}] {i:2d}초 남음", end='\r')
                sd.sleep(1000)
            
            metronome_active = False
            is_recording = False
        
        print("\n\n✓ 녹음 완료! 분석 이미지 생성 중...")
        
        audio_array = np.array(recorded_data)
        fig = create_waveform_with_metronome(audio_array, METRONOME_BPM, SAMPLE_RATE)
        
        filename = save_analysis_image(fig)
        img_base64 = fig_to_base64(fig)
        
        print("\n" + "="*70)
        print("📊 분석 준비 완료!")
        print("="*70)
        print(f"✅ 이미지 파일: {filename}")
        print(f"✅ Base64 길이: {len(img_base64):,} 문자")
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