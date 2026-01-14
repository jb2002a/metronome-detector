# utils.py
import numpy as np

def bars_to_sleep_ms(countin_bars, bpm, sample_rate, beats_per_bar=4):
    """
    마디(bars) 수를 밀리초(ms)로 변환합니다.
    샘플 레이트를 기준으로 계산하여 오차를 줄입니다.
    """
    samples_per_beat = int(sample_rate * 60.0 / bpm)
    total_beats = int(countin_bars * beats_per_bar)
    total_samples = total_beats * samples_per_beat
    total_ms = int(total_samples / sample_rate * 1000)
    return total_ms, total_beats

def generate_sine_wave(duration_ms, frequency, sample_rate, decay_factor=10):
    """
    감쇠하는 사인파(메트로놈 클릭음)를 생성합니다.
    """
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)
    tone = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-decay_factor * t)
    return (tone * envelope).astype(np.float32)