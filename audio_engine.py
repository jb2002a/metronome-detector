# audio_engine.py
import numpy as np
import config
from utils import generate_sine_wave


class AudioHandler:
    def __init__(self):
        # 리스트 대신 NumPy 배열을 미리 할당 (메모리 관리 최적화)
        max_samples = int(config.SAMPLE_RATE * (config.RECORD_DURATION + 2)) # 여유분 포함
        self.recorded_data = np.zeros(max_samples, dtype=np.float32)
        self.write_ptr = 0  # 데이터를 기록할 위치 포인터
        
        self.is_recording = False
        self.metronome_active = False
        
        self.current_beat = 0
        self.sample_counter = 0
        self.beat_interval_samples = int(config.SAMPLE_RATE * 60.0 / config.METRONOME_BPM)
        
        # 소리 생성 (Sine Wave)
        self.metronome_sound = generate_sine_wave(50, 1000, config.SAMPLE_RATE) * 0.3
        self.downbeat_sound = generate_sine_wave(50, 1200, config.SAMPLE_RATE) * 0.3

    def reset_state(self):
        # 포인터 초기화
        self.write_ptr = 0
        self.recorded_data.fill(0) # 배열 내용 초기화
        self.current_beat = 0
        self.sample_counter = 0
        self.is_recording = False

    def callback(self, indata, outdata, frames, time_info, status):
        if status:
            print(status)

        guitar_input = indata[:, 0]
        amplified = np.clip(guitar_input * config.SOFTWARE_GAIN, -1.0, 1.0)

        if self.is_recording:
            # 리스트 extend 대신 배열 구간에 직접 할당
            end_ptr = self.write_ptr + frames
            if end_ptr <= len(self.recorded_data):
                self.recorded_data[self.write_ptr:end_ptr] = amplified
                self.write_ptr = end_ptr

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
        # [수정] 실제 기록된 범위만 슬라이싱하여 반환
        return self.recorded_data[:self.write_ptr].copy()