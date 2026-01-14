<div align="center">
  <h1>🎸 Metronome Detector</h1>
  <p>메트로놈 박자에 맞춘 기타 연주의 리듬 정확도를 정밀하게 분석하고 시각화하는 도구입니다.</p>
</div>

<hr>

<h2>1. 프로그램 의도</h2>
<p>
  연주자가 설정된 BPM의 메트로놈에 맞춰 연습을 할 때, 실제 연주가 정박 그리드에서 얼마나 벗어나는지 객관적으로 확인하기 위해 제작되었습니다. 
  ASIO 드라이버를 통해 입력 지연을 최소화하며, 신호의 정적 상태 확인 후 피크를 감지하는 알고리즘을 통해 연주의 어택(Attack) 지점을 정확히 감지합니다.
</p>

<h2>2. 필수 사항 및 사용 라이브러리</h2>

<h3>✅ 시스템 요구 사항</h3>
<ul>
  <li><b>Python 버전:</b> Python 3.11 이상</li>
  <li><b>오디오 장치:</b> ASIO를 지원하는 오디오 인터페이스 필수</li>
  <li><b>운영체제:</b> Windows</li>
</ul>

<h3>📦 필수 라이브러리</h3>
<table width="100%">
  <thead>
    <tr>
      <th align="left">라이브러리</th>
      <th align="left">용도</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>numpy</code></td>
      <td>오디오 데이터 처리 및 수치 계산</td>
    </tr>
    <tr>
      <td><code>sounddevice</code></td>
      <td>ASIO 기반 저지연 녹음 및 재생</td>
    </tr>
    <tr>
      <td><code>matplotlib</code></td>
      <td>파형 시각화 및 분석 리포트 이미지 생성</td>
    </tr>
    <tr>
      <td><code>tkinter</code></td>
      <td>사용자 설정을 위한 GUI 런처 제공</td>
    </tr>
  </tbody>
</table>

<h2>3. 사용 방법</h2>
<ol>
  <li><b>프로그램 실행:</b> <code>gui_main.py</code>를 실행하여 런처 창을 엽니다.</li>
  <li><b>장치 확인:</b> 하단 로그 창에 출력되는 '시스템 오디오 장치 검색 결과'에서 본인의 ASIO 장치 ID를 확인합니다.</li>
  <li><b>설정 입력:</b> 장치 ID, BPM, 그리드 단위(Chromatic Beats) 등을 설정합니다.</li>
  <li><b>분석 시작:</b> '설정 저장 및 분석 시작' 버튼을 누릅니다. 카운트인 이후 녹음이 시작됩니다.</li>
  <li><b>결과 확인:</b> 녹음 종료 후 자동으로 파형 분석 결과가 화면에 출력되며, <code>images</code> 폴더에 PNG 파일로 저장됩니다.</li>
</ol>

<h2>4. UI 파라미터 설명</h2>

<h3>🎧 하드웨어 설정</h3>
<table width="100%">
  <thead>
    <tr>
      <th align="left">항목</th>
      <th align="left">상세 설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>ASIO Device ID</b></td>
      <td>오디오 인터페이스의 ASIO 고유 ID 번호입니다.</td>
    </tr>
    <tr>
      <td><b>Sample Rate</b></td>
      <td>오디오 샘플링 주파수입니다. 인터페이스 설정값과 일치해야 합니다.</td>
    </tr>
    <tr>
      <td><b>Block Size</b></td>
      <td>오디오 버퍼 크기입니다. 낮을수록 지연 시간이 줄어듭니다.</td>
    </tr>
  </tbody>
</table>

<h3>🎸 녹음 및 음악 설정</h3>
<table width="100%">
  <thead>
    <tr>
      <th align="left">항목</th>
      <th align="left">상세 설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Metronome BPM</b></td>
      <td>연습할 곡의 템포를 설정합니다.</td>
    </tr>
    <tr>
      <td><b>Record Duration (s)</b></td>
      <td>실제 녹음을 진행할 시간(초)입니다.</td>
    </tr>
    <tr>
      <td><b>Software Gain</b></td>
      <td>입력되는 기타 신호의 크기를 증폭시켜 분석 정확도를 높입니다.</td>
    </tr>
  </tbody>
</table>

<h3>📊 분석 알고리즘 설정</h3>
<table width="100%">
  <thead>
    <tr>
      <th align="left">항목</th>
      <th align="left">상세 설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Chromatic Beats</b></td>
      <td>분석할 그리드 단위입니다 (4: 4분음표, 8: 8분음표, 16: 16분음표).</td>
    </tr>
    <tr>
      <td><b>Tolerance (s)</b></td>
      <td>정박으로 판정할 수 있는 허용 오차 범위(초)입니다.</td>
    </tr>
    <tr>
      <td><b>Threshold</b></td>
      <td>음의 시작(Attack)으로 판단할 최소 신호 크기입니다.</td>
    </tr>
    <tr>
      <td><b>Silence Threshold</b></td>
      <td>무음으로 판단할 신호 크기입니다. 노이즈 레벨에 맞춰 설정합니다.</td>
    </tr>
  </tbody>
</table>

<h2>5. 분석 결과 해석</h2>
<ul>
  <li><b style="color: #2E86DE;">Blue Signal:</b> 녹음된 실제 기타 입력 파형입니다.</li>
  <li><b style="color: #FF0000;">Red Solid Line:</b> 메트로놈의 마디 시작(강박) 지점입니다.</li>
  <li><b style="color: #F18B8B;">Pink Solid Line:</b> 메트로놈의 박자 및 세부 그리드 지점입니다.</li>
  <li><b style="color: #2ECC71;">Green Dashed Line:</b> 프로그램이 감지한 연주 시작(Attack) 지점입니다.</li>
  <li><b style="color: #ff0000;">Red 'X' Mark:</b> 설정된 Tolerance 범위를 벗어난 리듬 오차 지점입니다.</li>
</ul>