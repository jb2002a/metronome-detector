# test.py
# 테스트용 스크립트: ASIO 장치가 제대로 인식되는지 확인

import os

#반드시 ASIO를 활성화 시킨 후 sounddevice를 임포트해야 합니다.
os.environ["SD_ENABLE_ASIO"] = "1"

import sounddevice as sd

print(sd.query_hostapis())