import os
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd

print("--- 사용 가능한 Host API 목록 ---")
print(sd.query_hostapis())