import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ASIO 활성화를 위해 라이브러리 임포트 전 환경변수 설정
os.environ["SD_ENABLE_ASIO"] = "1"
try:
    import sounddevice as sd
except ImportError:
    sd = None

# 초기 기본값을 가져오기 위해 임포트
try:
    import config
except ImportError:
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
        self.root.title("Metronome Detector Launcher")
        self.root.geometry("550x900")
        self.root.configure(bg="#f5f5f5")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_styles()
        
        # 설정값 변수 초기화
        self._init_vars()
        self._build_ui()
        
        self.process = None
        
        # 시작 시 장치 목록 출력
        self.root.after(100, self.check_and_print_devices)

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

    def check_and_print_devices(self):
        """현재 시스템의 ASIO 장치 목록을 로그 창에 출력합니다."""
        self.log_area.insert(tk.END, "--- 시스템 오디오 장치 검색 결과 ---\n")
        if sd is None:
            self.log_area.insert(tk.END, "[오류] sounddevice 라이브러리를 로드할 수 없습니다.\n")
            return

        try:
            devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            
            asio_found = False
            for i, dev in enumerate(devices):
                api_info = host_apis[dev['hostapi']]
                if api_info['name'] == 'ASIO':
                    self.log_area.insert(tk.END, f"ID {i:2d}: [ASIO] {dev['name']}\n")
                    asio_found = True
            
            if not asio_found:
                self.log_area.insert(tk.END, "[경고] 인식된 ASIO 장치가 없습니다. 드라이버 설치를 확인하세요.\n")
            
        except Exception as e:
            self.log_area.insert(tk.END, f"[오류] 장치 목록 조회 중 에러 발생: {e}\n")
        
        self.log_area.insert(tk.END, "-----------------------------------\n\n")
        self.log_area.see(tk.END)

    def _add_field(self, parent, label, var, desc=""):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=4, padx=10)
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text=label, width=22).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var, font=("Consolas", 10)).pack(side=tk.RIGHT, expand=True, fill=tk.X)
        if desc:
            ttk.Label(frame, text=f"- {desc}", style="Desc.TLabel").pack(side=tk.LEFT)

    def _add_dropdown(self, parent, label, var, values, desc=""):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=4, padx=10)
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text=label, width=22).pack(side=tk.LEFT)
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly", font=("Consolas", 10))
        cb.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        if desc:
            ttk.Label(frame, text=f"- {desc}", style="Desc.TLabel").pack(side=tk.LEFT)

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=(20, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Metronome Launcher", font=("Malgun Gothic", 18, "bold"), foreground="#2e86de").pack()
        ttk.Label(header, text="설정 수정 후 분석을 시작합니다.", style="Desc.TLabel").pack()

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        sf = ttk.Frame(canvas)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", width=510)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 1. 하드웨어 설정
        g1 = ttk.LabelFrame(sf, text=" 하드웨어 설정 ", padding=10)
        g1.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g1, "ASIO Device ID", self.asio_id_var, "아래 로그 창에서 확인한 ID 번호를 입력하세요")
        self._add_dropdown(g1, "Sample Rate", self.sample_rate_var, [44100, 48000, 88200, 96000], "인터페이스 설정과 동일해야 함")
        self._add_dropdown(g1, "Block Size", self.block_size_var, [32, 64, 128, 256, 512, 1024], "인터페이스 설정과 동일해야 함")

        # 2. 녹음 및 음악 설정
        g2 = ttk.LabelFrame(sf, text=" 녹음 및 음악 설정 ", padding=10)
        g2.pack(fill=tk.X, padx=15, pady=5)
        self._add_field(g2, "Metronome BPM", self.bpm_var, "템포")
        self._add_field(g2, "Record Duration (s)", self.duration_var, "녹음 시간")
        self._add_field(g2, "Software Gain", self.gain_var, "기타 증폭")

        # 3. 분석 설정
        g3 = ttk.LabelFrame(sf, text=" 분석 설정 ", padding=10)
        g3.pack(fill=tk.X, padx=15, pady=5)
        self._add_dropdown(g3, "Chromatic Beats", self.chromatic_beats_var, [4, 8, 16], "그리드 단위 (4/8/16분음표)")
        self._add_field(g3, "Tolerance (s)", self.tolerance_var, "민감도")
        self._add_field(g3, "Threshold", self.threshold_var, "피크 임계값")
        self._add_field(g3, "Silence Threshold", self.silence_threshold_var, "무음 임계값")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 로그 중계창
        log_group = ttk.LabelFrame(self.root, text=" 실행 로그 및 장치 정보 ", padding=5)
        log_group.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)
        self.log_area = scrolledtext.ScrolledText(log_group, height=14, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 실행 버튼
        self.run_button = ttk.Button(self.root, text="설정 저장 및 분석 시작", style="Run.TButton", command=self.save_and_run)
        self.run_button.pack(fill=tk.X, padx=15, pady=15)

    def save_config(self):
        """UI의 값을 config.py 파일로 물리적으로 저장합니다."""
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
        try:
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(config_content)
        except Exception as e:
            messagebox.showerror("저장 오류", f"config.py 저장 중 오류 발생: {e}")

    def save_and_run(self):
        self.save_config()
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "[정보] 설정을 저장했습니다.\n")
        self.run_button.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.relay_main_output, daemon=True)
        thread.start()

    def relay_main_output(self):
        """main.py를 서브프로세스로 실행하고 표준 출력을 GUI에 중계합니다."""
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )

            for line in self.process.stdout:
                self.log_area.insert(tk.END, line)
                self.log_area.see(tk.END)
            
            self.process.wait()
            
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