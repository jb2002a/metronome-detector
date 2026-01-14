import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
import config

# 이미지를 저장할 폴더명
OUTPUT_DIR = "images"

def create_waveform_with_metronome(audio_data, detected_indices=None):
    """
    음성 파형을 시각화하고 메트로놈 가이드 라인과 감지된 피크 지점을 표시합니다.
    그리드와 어긋난 연주 지점에는 그래프 하단에 'X' 표시를 추가합니다.
    """
    duration = len(audio_data) / config.SAMPLE_RATE
    time_axis = np.linspace(0, duration, len(audio_data))
    bpm = config.METRONOME_BPM

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(18, 7), dpi=100)

    # 1. 오디오 파형 그리기
    ax.plot(time_axis, audio_data, color="#2E86DE", linewidth=0.5, alpha=0.8, label="Guitar Signal")
    ax.fill_between(time_axis, audio_data, alpha=0.3, color="#2E86DE")

    # 2. 메트로놈 박자 및 그리드 생성
    beat_interval = 60.0 / bpm
    beat_positions = np.arange(0, duration, beat_interval)
    
    # 전체 그리드 위치 저장 (정박 + 서브디비전)
    target_grid_positions = list(beat_positions)

    # 기본 메트로놈 박자 표시 
    for i, pos in enumerate(beat_positions):
        # 강박
        if i % config.BEATS_PER_BAR == 0:
            ax.axvline(pos, color="#FF0000", linestyle="-", linewidth=1.5, alpha=0.8, label="Bar Start" if i == 0 else "")
        # 약박
        else:
            ax.axvline(pos, color="#F18B8B", linestyle="-", linewidth=1.2, alpha=0.6, label="Beat" if i == 1 else "")

    # 설정된 음표 단위(4, 8, 16 등)에 따른 세부 그리드 표시
    if config.CHROMATIC_ENABLED:
        subdivisions = config.CHROMATIC_BEATS / 4
        chromatic_interval = beat_interval / subdivisions
        chromatic_positions = np.arange(0, duration, chromatic_interval)
        
        for pos in chromatic_positions:
            if not any(np.isclose(pos, beat_positions, atol=1e-5)):
                ax.axvline(pos, color="#ff0000", linestyle="-", linewidth=1.2, alpha=0.6)
                target_grid_positions.append(pos)
    
    target_grid_positions = np.sort(target_grid_positions)

    # 3. Attack 지점 표시 및 어긋남 검사
    if detected_indices is not None and len(detected_indices) > 0:
        # 허용 오차 설정 (30ms)
        tolerance = 0.03 
        
        first_mark = True
        first_x_mark = True

        for idx in detected_indices:
            peak_time = idx / config.SAMPLE_RATE
            
            # 현재 연주 지점이 그리드 중 하나와 근접한지 확인
            is_on_grid = any(np.abs(target_grid_positions - peak_time) < tolerance)

            # 연주 시작 지점 표시 (초록 점선)
            ax.axvline(peak_time, color="#2ECC71", linestyle="--", linewidth=1.2, alpha=0.9, 
                       label="Detected Attack" if first_mark else "")
            first_mark = False

            # 그리드와 어긋난 경우 'X' 표시 추가 (하단 y=-0.6 위치)
            if not is_on_grid:
                ax.text(peak_time, -0.6, 'X', color='red', fontsize=15, fontweight='bold', 
                        ha='center', va='center')
                
                # 범례를 위한 가짜 아티스트(Proxy Artist)
                if first_x_mark:
                    ax.plot([], [], 'rx', label="Off-Grid", markersize=10, markeredgewidth=2)
                    first_x_mark = False

    # 그래프 스타일 설정
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.1, 1.1)
    ax.set_title(f"Guitar Analysis | {bpm} BPM | {config.CHROMATIC_BEATS}th Notes", fontsize=15, fontweight="bold")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude")
    ax.grid(True, alpha=0.2)
    
    # 범례 표시
    ax.legend(loc="upper right", frameon=True, shadow=True)
    
    plt.tight_layout()
    return fig

def save_analysis_image(fig):
    # images 폴더가 없으면 생성합니다.
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 '{OUTPUT_DIR}' 폴더 생성됨")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"guitar_chromatic_{timestamp}.png"
    
    # 폴더 경로와 파일명을 합쳐 전체 경로를 만듭니다.
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    
    # 전체 경로를 반환합니다.
    return filepath