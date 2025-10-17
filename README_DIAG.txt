
1) 가상환경 활성화 후(이미 설치되어 있으면 건너뛰어도 됨)
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt

2) 초간단 렌더링 테스트
   python hello.py
   => 'Kivy Hello ✓' 라벨이 보여야 정상

3) KV를 전혀 쓰지 않는 강제 표시 메인 실행
   python main.py
   => 로그인/회원가입 버튼이 있는 심플 UI가 반드시 떠야 함

4) 여전히 까만 화면이면
   - 드라이버/GL 백엔드 문제 가능성 높음
   - 아래처럼 ANGLE(D3D11) 강제 전환 시도:
       $env:KIVY_GL_BACKEND="angle_sdl2"
       python main.py
