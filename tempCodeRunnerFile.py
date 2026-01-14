import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ASIO 활성화를 위해 sounddevice 임포트 전 환경변수 설정
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd

# 기존 설정 모듈 및 실행 로직 임포트
import config
from main import run_analysis_process

class StdoutRedirector:
    """터미널 출력을 Tkinter Text 위젯으로 전달하는 클래스"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END) # 자동 스크롤

    def flush(self):
        pass

class MetronomeDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎸 Metronome Detector v2.0")
        self.root.geometry("550x900")
        self.root.configure(bg="#f5f5f5")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_styles()
        
        # 설정값 변수 초기화
        self._init_vars()
        self._build_ui()
        
        # 표준 출력(print)을 GUI 로그 창으로 리다이렉트
        sys.stdout = StdoutRedirector(self.log_area)

    def _setup_styles(self):
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabelframe", background="#f5f5f5", relief="flat", borderwidth=1)
        self.style.configure("TLabelframe.Label", font=("Malgun Gothic", 11, "bold"), background="#f5f5f5")
        self.style.configure("TLabel", background="#f5f5f5", font=("Malgun Gothic", 10))
        self.style.configure("Desc.TLabel", foreground="#666666", font=("Malgun Gothic", 9))
        self.style.configure("Run.TButton", font=("Malgun Gothic", 12, "bold"), foreground="white", background="#2e86de")
        self.style.map("Run.TButton", background=[('active', '#341f97'), ('disabled', '#cccccc')])

    def _init_vars(self):
        self.asio_id_var = tk.IntVar(value=config.ASIO_DEVICE_ID)
        self.sample_rate_var = tk.IntVar(value=config.SAMPLE_RATE)
        self.block_size_var = tk.IntVar(value=config.BLOCK_SIZE)
        self.duration_var = tk.IntVar(value=config.RECORD_DURATION)
        self.gain_var = tk.DoubleVar(value=config.SOFTWARE_GAIN)
        self.bpm_var = tk.IntVar(value=config.METRONOME_BPM)
        self.chromatic_beats_var = tk.IntVar(value=config.CHROMATIC_BEATS)
        self.tolerance_var = tk.DoubleVar(value=config.TOLERANCE)
        self.threshold_var = tk.DoubleVar(value=config.THRESHOLD)
        self.silence_threshold_var = tk.DoubleVar(value=config.SILENCE_THRESHOLD)

    def _get_asio_info(self):
        try:
            host_apis = sd.query_hostapis()
            for api in host_apis:
                if api['name'] == 'ASIO':
                    return f"사용 가능 ASIO ID: {api['devices']}"
        except: pass
        return "ASIO 장치를 찾을 수 없음"

    def _add_field(self, parent, label, var, desc=""):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=4, padx=10)
        
        top_row = ttk.Frame(frame)
        top_row.pack(fill=tk.X)
        
        ttk.Label(top_row, text=label, width=22).pack(side=tk.LEFT)
        ttk.Entry(top_row, textvariable=var, font=("Consolas", 10)).pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        if desc:
            ttk.Label(frame, text=f"  💡 {desc}", style="Desc.TLabel").pack(side=tk.LEFT)

    def _build_ui(self):
        # 상단 타이틀
        header = ttk.Frame(self.root, padding=(20, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Metronome Detector", font=("Malgun Gothic", 18, "bold"), foreground="#2e86de").pack()

        # 설정 영역 (스크롤 가능)
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=510)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 하드웨어 설정 그룹
        g1 = ttk.LabelFrame(self.scrollable_frame, text=" 🎧 하드웨어 설정 ", padding=10)
        g1.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g1, "ASIO Device ID", self.asio_id_var, self._get_asio_info())
        self._add_field(g1, "Sample Rate", self.sample_rate_var, "오인페 설정과 동일해야 함")
        self._add_field(g1, "Block Size", self.block_size_var, "오인페 설정과 동일해야 함")

        # 음악 설정 그룹
        g2 = ttk.LabelFrame(self.scrollable_frame, text=" 🎸 녹음 및 음악 설정 ", padding=10)
        g2.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g2, "Metronome BPM", self.bpm_var, "연습 템포")
        self._add_field(g2, "Record Duration (s)", self.duration_var, "크로매틱 연습 시간")
        self._add_field(g2, "Software Gain", self.gain_var, "기타 입력 증폭")

        # 분석 설정 그룹
        g3 = ttk.LabelFrame(self.scrollable_frame, text=" 📊 분석 알고리즘 설정 ", padding=10)
        g3.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g3, "Chromatic Beats", self.chromatic_beats_var, "그리드 단위 (4/8/16분음표)")
        self._add_field(g3, "Tolerance (s)", self.tolerance_var, "민감도 (정박 오차 범위)")
        self._add_field(g3, "Threshold", self.threshold_var, "어택 감지 임계값")
        self._add_field(g3, "Silence Threshold", self.silence_threshold_var, "무음 판단 임계값")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 실시간 로그 출력창 (Error 수정: pack에서 height 제거)
        log_group = ttk.LabelFrame(self.root, text=" 📋 실시간 실행 로그 ", padding=5)
        log_group.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)
        
        # ScrolledText 자체의 height 속성을 사용하여 높이 조절 (텍스트 줄 수 기준)
        self.log_area = scrolledtext.ScrolledText(log_group, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 실행 버튼
        self.run_button = ttk.Button(self.root, text="분석 시작 (Record & Analyze)", style="Run.TButton", command=self.start_thread)
        self.run_button.pack(fill=tk.X, padx=15, pady=15)

    def update_config(self):
        """UI 입력값을 config 모듈 전역 변수에 반영"""
        config.ASIO_DEVICE_ID = self.asio_id_var.get()
        config.SAMPLE_RATE = self.sample_rate_var.get()
        config.BLOCK_SIZE = self.block_size_var.get()
        config.RECORD_DURATION = self.duration_var.get()
        config.SOFTWARE_GAIN = self.gain_var.get()
        config.METRONOME_BPM = self.bpm_var.get()
        config.CHROMATIC_BEATS = self.chromatic_beats_var.get()
        config.TOLERANCE = self.tolerance_var.get()
        config.THRESHOLD = self.threshold_var.get()
        config.SILENCE_THRESHOLD = self.silence_threshold_var.get()

    def start_thread(self):
        """UI 프리징 방지를 위해 스레드에서 분석 로직 실행"""
        self.log_area.delete(1.0, tk.END) # 기존 로그 삭제
        self.run_button.config(state=tk.DISABLED)
        self.update_config()
        
        thread = threading.Thread(target=self.execute_main)
        thread.daemon = True
        thread.start()

    def execute_main(self):
        try:
            # main.py의 분석 로직 직접 실행
            run_analysis_process()
        finally:
            self.run_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = MetronomeDetectorGUI(root)
    root.mainloop()