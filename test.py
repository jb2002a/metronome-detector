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
RECORD_DURATION = 10          # 10초 녹음

# 카운트인(초) -> 마디 기반으로 변경
COUNTIN_BARS = 1              # 카운트인 마디 수 (4/4 기준)
BEATS_PER_BAR = 4             # 4/4

SOFTWARE_GAIN = 60.0
METRONOME_BPM = 120           # 메트로놈 BPM
BLOCK_SIZE = 64               # 오디오 블록 크기
CHROMATIC_ENABLED = True      # 시각화 그리드에는 8분음표 표시 (소리는 안 남)

# 녹음 버퍼
recorded_data = []
is_recording = False

# --- 유틸: 마디 기반 카운트인 시간을 샘플 정렬 기반으로 계산 ---
def bars_to_sleep_ms(countin_bars, bpm, sample_rate, beats_per_bar=4):
    """
    countin_bars(마디) -> sleep에 쓸 밀리초(ms)로 변환.
    샘플 기반으로 계산해 메트로놈 그리드/녹음 시작 정렬을 더 정확히 맞춤.
    """
    samples_per_beat = int(sample_rate * 60.0 / bpm)
    total_beats = int(countin_bars * beats_per_bar)
    total_samples = total_beats * samples_per_beat
    total_ms = int(total_samples / sample_rate * 1000)
    return total_ms, total_beats

# 메트로놈 사운드 생성
def generate_metronome_click(duration_ms=50, frequency=1000, sample_rate=44100):
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-10 * t)
    return (tone * envelope * 0.3).astype(np.float32)

def generate_countin_click(duration_ms=80, frequency=1200, sample_rate=44100):
    # 현재 구현에서는 별도로 사용하지 않지만, 필요 시 카운트인 클릭음을 구분하기 위해 유지
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-8 * t)
    return (tone * envelope * 0.5).astype(np.float32)

METRONOME_SOUND = generate_metronome_click()
# 첫 박자를 구분하고 싶을 경우 사용할 사운드(현재는 주석 처리된 로직이 존재)
DOWNBEAT_SOUND = generate_metronome_click(frequency=1200)

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
            # 박자 간격(샘플 수)이 지나면 카운터 리셋 및 비트 증가
            if sample_counter >= beat_interval_samples:
                sample_counter = 0
                current_beat = (current_beat + 1) % 4

            # 모든 4박자에서 소리 발생
            if sample_counter < len(METRONOME_SOUND):

                if current_beat == 0:
                    output_signal[i] += DOWNBEAT_SOUND[sample_counter]
                else:
                    output_signal[i] += METRONOME_SOUND[sample_counter]


            sample_counter += 1

    output_signal = np.clip(output_signal, -1.0, 1.0)
    for ch in range(outdata.shape[1]):
        outdata[:, ch] = output_signal

def create_waveform_with_metronome(audio_data, bpm, sample_rate):
    """파형과 심플 그리드 시각화"""
    duration = len(audio_data) / sample_rate
    time_axis = np.linspace(0, duration, len(audio_data))

    fig, ax = plt.subplots(figsize=(18, 7), dpi=100)

    # 파형 그리기
    ax.plot(time_axis, audio_data, color="#2E86DE", linewidth=0.5, alpha=0.8)
    ax.fill_between(time_axis, audio_data, alpha=0.3, color="#2E86DE")

    # 메트로놈 그리드 계산
    beat_interval = 60.0 / bpm

    # 4박자 단위 그리드 (빨간 실선/점선)
    beat_positions = np.arange(0, duration, beat_interval)
    for i, pos in enumerate(beat_positions):
        if i % 4 == 0:
            ax.axvline(pos, color="#FF4757", linestyle="-", linewidth=1.5, alpha=0.8)
        else:
            ax.axvline(pos, color="#FF6B6B", linestyle="--", linewidth=1.0, alpha=0.6)

    # 시각적 분석을 위한 8분음표 보조선 (소리는 나지 않지만 연주 타이밍 확인용)
    if CHROMATIC_ENABLED:
        chromatic_positions = np.arange(beat_interval / 2, duration, beat_interval)
        for pos in chromatic_positions:
            ax.axvline(pos, color="#70a1ff", linestyle=":", linewidth=0.8, alpha=0.3)

    # 스타일링
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel("Time (seconds)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Amplitude", fontsize=13, fontweight="bold")

    title = f"Guitar Performance Analysis | {bpm} BPM | 4-Beat Metronome"
    ax.set_title(title, fontsize=15, fontweight="bold", pad=20)

    ax.grid(True, alpha=0.2, linestyle="-", linewidth=0.5)
    ax.set_facecolor("#F8F9FA")

    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2E86DE", alpha=0.3, label="Guitar Signal"),
        plt.Line2D([0], [0], color="#FF4757", linestyle="-", linewidth=1.5, label="Downbeat (Beat 1)"),
        plt.Line2D([0], [0], color="#FF6B6B", linestyle="--", linewidth=1.0, label="Beats 2, 3, 4"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()
    return fig

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img_base64

def save_analysis_image(fig, filename=None):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"guitar_chromatic_{timestamp}.png"

    fig.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"✓ 이미지 저장: {filename}")
    return filename

def record_and_analyze():
    global recorded_data, metronome_active, current_beat, sample_counter, beat_interval_samples, is_recording
    recorded_data = []
    current_beat = 0
    sample_counter = 0
    is_recording = False

    # 1박에 해당하는 샘플 수 계산
    beat_interval_samples = int(SAMPLE_RATE * 60.0 / METRONOME_BPM)

    # 카운트인(마디) -> ms 계산
    countin_ms, countin_beats = bars_to_sleep_ms(
        COUNTIN_BARS, METRONOME_BPM, SAMPLE_RATE, BEATS_PER_BAR
    )

    print(f"{'='*70}")
    print(f"🎸 4비트 메트로놈 크로매틱 분석기 ({METRONOME_BPM} BPM)")
    print(f"{'='*70}")
    print(f"⏱️  카운트인: {COUNTIN_BARS} bar ({countin_beats} beats)")
    print(f"📊 녹음 시간: {RECORD_DURATION}초")
    print(f"🎵 설정: 모든 4박자 소리 출력 (8분음표 소리 제거)")
    print(f"{'='*70}\n")

    try:
        info = sd.query_devices(ASIO_DEVICE_ID)
        channels = min(info["max_input_channels"], info["max_output_channels"])

        with sd.Stream(
            device=ASIO_DEVICE_ID,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            channels=channels,
            callback=audio_callback,
        ):
            metronome_active = True

            print(f"🎼 카운트인 시작! ({COUNTIN_BARS} bar) 4비트 소리에 맞추어 준비하세요...")
            sd.sleep(countin_ms)

            # 녹음 시작을 강박 기준으로 명확히 정렬(권장)
            current_beat = 0
            sample_counter = 0

            print("\n🚀 녹음 시작! 크로매틱 연주 Go!\n")
            is_recording = True

            for i in range(RECORD_DURATION, 0, -1):
                bar = "█" * (RECORD_DURATION - i + 1) + "░" * (i - 1)
                print(f"  ⏱️  [{bar}] {i:2d}초 남음", end="\r")
                sd.sleep(1000)

            metronome_active = False
            is_recording = False

        print("\n\n✓ 녹음 완료! 분석 이미지 생성 중...")

        audio_array = np.array(recorded_data, dtype=np.float32)
        fig = create_waveform_with_metronome(audio_array, METRONOME_BPM, SAMPLE_RATE)

        filename = save_analysis_image(fig)
        img_base64 = fig_to_base64(fig)

        print("\n" + "=" * 70)
        print("📊 분석 준비 완료!")
        print("=" * 70)
        print(f"✅ 이미지 파일: {filename}")
        print("=" * 70)

        plt.show()

        return filename, img_base64

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    record_and_analyze()
