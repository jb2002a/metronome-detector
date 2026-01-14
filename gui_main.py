import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# 초기 기본값을 가져오기 위해 임포트 (파일이 없을 경우 대비)
try:
    import config
except ImportError:
    # 기본값 수동 정의
    class DummyConfig:
        ASIO_DEVICE_ID = 0
        SAMPLE_RATE = 44100
        BLOCK_SIZE = 64
        RECORD_DURATION = 10
        SOFTWARE_GAIN = 60.0
        METRONOME_BPM = 100
        COUNTIN_BARS = 2
        BEATS_PER_BAR = 4
        CHROMATIC_ENABLED = True
        CHROMATIC_BEATS = 4
        TOLERANCE = 0.03
        THRESHOLD = 0.25
        SILENCE_THRESHOLD = 0.1
    config = DummyConfig()

class MetronomeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🎸 Metronome Detector Launcher")
        self.root.geometry("550x850")
        self.root.configure(bg="#f5f5f5")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_styles()
        
        # 설정값 변수 초기화 (현재 config.py의 값 로드)
        self._init_vars()
        self._build_ui()
        
        self.process = None # 실행될 프로세스 객체

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

    def _add_field(self, parent, label, var, desc=""):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=4, padx=10)
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text=label, width=22).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var, font=("Consolas", 10)).pack(side=tk.RIGHT, expand=True, fill=tk.X)
        if desc:
            ttk.Label(frame, text=f"  💡 {desc}", style="Desc.TLabel").pack(side=tk.LEFT)

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=(20, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Metronome Launcher", font=("Malgun Gothic", 18, "bold"), foreground="#2e86de").pack()
        ttk.Label(header, text="설정 수정 후 분석을 시작합니다.", style="Desc.TLabel").pack()

        # 설정 영역 (스크롤 적용)
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        sf = ttk.Frame(canvas)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", width=510)
        canvas.configure(yscrollcommand=scrollbar.set)

        g1 = ttk.LabelFrame(sf, text=" 🎧 하드웨어 설정 ", padding=10)
        g1.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g1, "ASIO Device ID", self.asio_id_var, "ASIO 장치 번호")
        self._add_field(g1, "Sample Rate", self.sample_rate_var, "오인페 설정과 동일해야 함")
        self._add_field(g1, "Block Size", self.block_size_var, "오인페 설정과 동일해야 함")

        g2 = ttk.LabelFrame(sf, text=" 🎸 녹음 및 음악 설정 ", padding=10)
        g2.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g2, "Metronome BPM", self.bpm_var, "템포")
        self._add_field(g2, "Record Duration (s)", self.duration_var, "녹음 시간")
        self._add_field(g2, "Software Gain", self.gain_var, "기타 증폭")

        g3 = ttk.LabelFrame(sf, text=" 📊 분석 설정 ", padding=10)
        g3.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g3, "Chromatic Beats", self.chromatic_beats_var, "그리드 단위")
        self._add_field(g3, "Tolerance (s)", self.tolerance_var, "민감도")
        self._add_field(g3, "Threshold", self.threshold_var, "피크 임계값")
        self._add_field(g3, "Silence Threshold", self.silence_threshold_var, "무음 임계값")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 실시간 로그 중계창
        log_group = ttk.LabelFrame(self.root, text=" 📋 main.py 출력 실시간 중계 ", padding=5)
        log_group.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)
        self.log_area = scrolledtext.ScrolledText(log_group, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 실행 버튼
        self.run_button = ttk.Button(self.root, text="설정 저장 및 분석 시작", style="Run.TButton", command=self.save_and_run)
        self.run_button.pack(fill=tk.X, padx=15, pady=15)

    def save_config(self):
        """UI의 현재 값을 config.py 파일로 물리적으로 저장합니다."""
        config_content = f"""# config.py (Launcher에 의해 자동 생성됨)

ASIO_DEVICE_ID = {self.asio_id_var.get()}
SAMPLE_RATE = {self.sample_rate_var.get()}
BLOCK_SIZE = {self.block_size_var.get()}

RECORD_DURATION = {self.duration_var.get()}
SOFTWARE_GAIN = {self.gain_var.get()}

METRONOME_BPM = {self.bpm_var.get()}
COUNTIN_BARS = {config.COUNTIN_BARS}
BEATS_PER_BAR = {config.BEATS_PER_BAR}

CHROMATIC_ENABLED = {config.CHROMATIC_ENABLED}
CHROMATIC_BEATS = {self.chromatic_beats_var.get()}

TOLERANCE = {self.tolerance_var.get()}

THRESHOLD = {self.threshold_var.get()}
SILENCE_THRESHOLD = {self.silence_threshold_var.get()}
"""
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(config_content)

    def save_and_run(self):
        self.save_config() # 1. 설정 저장
        self.log_area.delete(1.0, tk.END) # 2. 로그창 초기화
        self.run_button.config(state=tk.DISABLED)
        
        # 3. 별도 스레드에서 main.py 실행 및 출력 중계
        thread = threading.Thread(target=self.relay_main_output, daemon=True)
        thread.start()

    def relay_main_output(self):
        """main.py를 서브프로세스로 실행하고 표준 출력을 GUI에 중계합니다."""
        try:
            # -u 옵션은 실시간 출력을 위해 필수입니다 (unbuffered)
            self.process = subprocess.Popen(
                [sys.executable, "-u", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )

            # 출력 스트림을 한 줄씩 읽어서 GUI에 표시
            for line in self.process.stdout:
                self.log_area.insert(tk.END, line)
                self.log_area.see(tk.END) # 항상 마지막 줄로 스크롤
            
            self.process.wait() # 프로세스 종료 대기
            
            if self.process.returncode == 0:
                self.log_area.insert(tk.END, "\n--- 분석 프로세스가 정상 종료되었습니다. ---\n")
            else:
                self.log_area.insert(tk.END, f"\n--- 프로세스가 종료되었습니다 (코드: {self.process.returncode}) ---\n")

        except Exception as e:
            messagebox.showerror("실행 오류", f"main.py 실행 중 오류 발생: {e}")
        finally:
            self.run_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = MetronomeLauncher(root)
    root.mainloop()