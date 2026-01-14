<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Metronome Detector README</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1 { color: #2e86de; border-bottom: 2px solid #2e86de; padding-bottom: 10px; }
        h2 { color: #341f97; margin-top: 30px; border-left: 5px solid #341f97; padding-left: 10px; }
        h3 { color: #576574; }
        code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: Consolas, monospace; }
        pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #2e86de; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .highlight { color: #e84118; font-weight: bold; }
        .feature-list { list-style-type: square; }
    </style>
</head>
<body>

    <h1>🎸 Metronome Detector</h1>
    <p><strong>Metronome Detector</strong>는 메트로놈 박자에 맞춘 기타 연주의 리듬 정확도를 정밀하게 분석하고 시각화하는 도구입니다.</p>

    <h2>1. 프로그램 의도</h2>
    <p>연주자가 설정된 BPM의 메트로놈에 맞춰 크로매틱 등의 연습을 할 때, 실제 연주가 정박 그리드에서 얼마나 벗어나는지 객관적으로 확인하기 위해 제작되었습니다. 저지연(ASIO) 녹음 기술을 활용하여 입력 오차를 최소화하고, 파형 분석 알고리즘을 통해 연주의 어택(Attack) 지점을 자동으로 감지합니다.</p>

    <h2>2. 필수 사항 및 사용 라이브러리</h2>
    <h3>시스템 요구 사항</h3>
    <ul class="feature-list">
        <li><strong>Python 버전:</strong> Python 3.11 이상</li>
        <li><strong>오디오 장치:</strong> ASIO 드라이버를 지원하는 오디오 인터페이스 권장</li>
        <li><strong>운영체제:</strong> Windows (ASIO 환경변수 설정 포함)</li>
    </ul>

    <h3>주요 라이브러리</h3>
    <table>
        <thead>
            <tr>
                <th>라이브러리</th>
                <th>용도</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>numpy</code></td>
                <td>오디오 데이터 처리 및 수치 계산</td>
            </tr>
            <tr>
                <td><code>sounddevice</code></td>
                <td>ASIO 기반 저지연 오디오 입력 및 출력 스트리밍</td>
            </tr>
            <tr>
                <td><code>matplotlib</code></td>
                <td>분석 결과 파형 및 리듬 그리드 시각화</td>
            </tr>
            <tr>
                <td><code>tkinter</code></td>
                <td>사용자 설정을 위한 GUI 환경 제공</td>
            </tr>
        </tbody>
    </table>

    <h2>3. 사용 방법</h2>
    <ol>
        <li><strong>프로그램 실행:</strong> <code>gui_main.py</code>를 실행하여 설정 화면을 엽니다.</li>
        <li><strong>오디오 장치 확인:</strong> 하단 로그 창에 출력되는 ASIO 장치 목록에서 본인의 장치 ID를 확인하여 입력합니다.</li>
        <li><strong>파라미터 설정:</strong> BPM, 녹음 시간, 민감도 등을 연습 목적에 맞게 수정합니다.</li>
        <li><strong>연습 시작:</strong> '설정 저장 및 분석 시작' 버튼을 누르면 2마디의 카운트인(Count-in) 후에 녹음이 시작됩니다.</li>
        <li><strong>결과 확인:</strong> 녹음이 끝나면 분석 그래프가 화면에 출력되며, <code>/images</code> 폴더에 분석 결과가 PNG 파일로 자동 저장됩니다.</li>
    </ol>

    <h2>4. UI 파라미터 상세 설명</h2>

    <h3>🎧 하드웨어 설정</h3>
    <table>
        <thead>
            <tr>
                <th>파라미터</th>
                <th>설명</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>ASIO Device ID</strong></td>
                <td>시스템에서 인식된 오디오 인터페이스의 고유 ID 번호입니다.</td>
            </tr>
            <tr>
                <td><strong>Sample Rate</strong></td>
                <td>오디오 샘플링 속도(예: 44100Hz)로, 인터페이스 설정과 일치해야 합니다.</td>
            </tr>
            <tr>
                <td><strong>Block Size</strong></td>
                <td>오디오 버퍼 크기입니다. 값이 작을수록 지연시간이 줄어들지만 CPU 부하가 늘어납니다.</td>
            </tr>
        </tbody>
    </table>

    <h3>🎸 녹음 및 음악 설정</h3>
    <table>
        <thead>
            <tr>
                <th>파라미터</th>
                <th>설명</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Metronome BPM</strong></td>
                <td>연습하고자 하는 메트로놈의 템포(Beats Per Minute)입니다.</td>
            </tr>
            <tr>
                <td><strong>Record Duration (s)</strong></td>
                <td>총 녹음 시간(초 단위)입니다.</td>
            </tr>
            <tr>
                <td><strong>Software Gain</strong></td>
                <td>입력되는 기타 신호를 소프트웨어적으로 증폭시킵니다. 파형이 너무 작게 보일 때 조절합니다.</td>
            </tr>
        </tbody>
    </table>

    <h3>📊 분석 알고리즘 설정</h3>
    <table>
        <thead>
            <tr>
                <th>파라미터</th>
                <th>설명</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Chromatic Beats</strong></td>
                <td>분석할 박자 단위입니다. (4: 4분음표, 8: 8분음표, 16: 16분음표 그리드 생성)</td>
            </tr>
            <tr>
                <td><strong>Tolerance (s)</strong></td>
                <td>정박 판정 허용 오차(초)입니다. 감지된 연주가 이 범위 안에 있으면 정박으로 간주합니다.</td>
            </tr>
            <tr>
                <td><strong>Threshold</strong></td>
                <td>피크 감지 임계값입니다. 이 값 이상의 신호가 들어올 때 연주 시작(Attack)으로 판단합니다.</td>
            </tr>
            <tr>
                <td><strong>Silence Threshold</strong></td>
                <td>무음 판단 임계값입니다. 노이즈 레벨보다 약간 높게 설정하여 다음 음의 감지를 준비합니다.</td>
            </tr>
        </tbody>
    </table>

    <h2>5. 분석 결과 해석</h2>
    <ul class="feature-list">
        <li><span style="color: #2E86DE; font-weight: bold;">Blue Signal:</span> 실제 녹음된 기타의 입력 파형입니다.</li>
        <li><span style="color: #FF0000; font-weight: bold;">Red Solid Line:</span> 마디의 시작(강박) 지점입니다.</li>
        <li><span style="color: #F18B8B; font-weight: bold;">Pink Solid Line:</span> 일반 박자(약박) 및 세부 그리드 지점입니다.</li>
        <li><span style="color: #2ECC71; font-weight: bold;">Green Dashed Line:</span> 프로그램이 감지한 연주 시작 지점(Attack)입니다.</li>
        <li><span class="highlight">Red 'X' Mark:</span> 설정된 Tolerance 범위를 벗어나 그리드와 어긋난 연주 지점입니다.</li>
    </ul>

</body>
</html>