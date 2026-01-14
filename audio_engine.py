# audio_engine.py
import numpy as np
import config
from utils import generate_sine_wave

# 주의: 여기서 sounddevice를 import 하지만, 
# main.py에서 이미 환경변수를 설정한 후 호출되므로 ASIO가 적용됩니다.

class AudioHandler:
    def __init__(self):
        self.recorded_data = []
        self.is_recording = False
        self.metronome_active = False
        
        self.current_beat = 0
        self.sample_counter = 0
        self.beat_interval_samples = int(config.SAMPLE_RATE * 60.0 / config.METRONOME_BPM)
        
        # 소리 생성 (Sine Wave)
        self.metronome_sound = generate_sine_wave(50, 1000, config.SAMPLE_RATE) * 0.3
        self.downbeat_sound = generate_sine_wave(50, 1200, config.SAMPLE_RATE) * 0.3

    def reset_state(self):
        self.recorded_data = []
        self.current_beat = 0
        self.sample_counter = 0
        self.is_recording = False

    def callback(self, indata, outdata, frames, time_info, status):
        if status:
            print(status)

        guitar_input = indata[:, 0]
        amplified = np.clip(guitar_input * config.SOFTWARE_GAIN, -1.0, 1.0)

        if self.is_recording:
            self.recorded_data.extend(amplified)

        output_signal = amplified.copy()

        if self.metronome_active:
            for i in range(frames):
                if self.sample_counter >= self.beat_interval_samples:
                    self.sample_counter = 0
                    self.current_beat = (self.current_beat + 1) % config.BEATS_PER_BAR

                sound = self.downbeat_sound if self.current_beat == 0 else self.metronome_sound
                
                if self.sample_counter < len(sound):
                    output_signal[i] += sound[self.sample_counter]

                self.sample_counter += 1

        output_signal = np.clip(output_signal, -1.0, 1.0)
        for ch in range(outdata.shape[1]):
            outdata[:, ch] = output_signal

    def get_recorded_array(self):
        return np.array(self.recorded_data, dtype=np.float32)