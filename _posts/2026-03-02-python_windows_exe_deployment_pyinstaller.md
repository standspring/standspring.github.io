---
title: "Python 프로그램을 Windows에서 exe로 배포하는 방법 (PyInstaller 완전 정리)"
date: 2026-03-02 00:00:00 +0900
categories: [Python, Deployment]
tags: [python, exe, windows, pyinstaller, packaging, distribution]
toc: true
toc_sticky: true
---

# Python 프로그램을 Windows에서 exe로 배포하는 방법

Python으로 만든 자동화 프로그램(예: pyautogui 매크로, HTS 자동화, 내부 업무툴 등)을
**설치 없이 실행파일(.exe) 형태로 배포**하고 싶다면?

가장 많이 사용하는 도구는 바로 **PyInstaller**입니다.

이 글에서는:

- 단일 exe 만들기
- 콘솔창 숨기기
- 아이콘 적용
- 외부 파일 포함
- 배포 시 주의사항

까지 한 번에 정리합니다.

---

## 1️⃣ PyInstaller 설치

```bash
pip install pyinstaller
```

설치 확인:

```bash
pyinstaller --version
```

---

## 2️⃣ 가장 기본 exe 만들기

예시 파일:

```python
# main.py
print("Hello World")
input("Press Enter to exit...")
```

빌드:

```bash
pyinstaller main.py
```

빌드가 끝나면:

```
dist/
 └── main/
     └── main.exe
```

폴더째로 배포해야 합니다.

---

## 3️⃣ 단일 exe 파일로 만들기 (실전용)

폴더가 아니라 **파일 하나로 만들기**:

```bash
pyinstaller --onefile main.py
```

결과:

```
dist/
 └── main.exe
```

✔ 배포가 훨씬 편함
⚠ 실행 속도는 약간 느릴 수 있음

---

## 4️⃣ 콘솔창 숨기기 (GUI 프로그램용)

pyautogui 같은 GUI 자동화 프로그램은 콘솔창이 필요 없는 경우가 많습니다.

```bash
pyinstaller --onefile --noconsole main.py
```

또는

```bash
pyinstaller --onefile --windowed main.py
```

---

## 5️⃣ 아이콘 적용하기

아이콘 파일 준비:

```
icon.ico
```

빌드:

```bash
pyinstaller --onefile --icon=icon.ico main.py
```

⚠ PNG는 안 되고 반드시 `.ico` 파일이어야 합니다.

---

## 6️⃣ 외부 파일 포함하기 (이미지, 설정파일 등)

예: 자동화에 필요한 `button.png` 포함

```bash
pyinstaller --onefile --add-data "button.png;." main.py
```

Windows에서는 구분자로 `;` 사용
(mac/Linux는 `:`)

코드에서는 이렇게 접근:

```python
import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

image_path = resource_path("button.png")
```

이걸 안 하면 exe에서 이미지 인식이 실패합니다.

---

## 7️⃣ pyautogui / OpenCV 포함 시 주의사항

이미지 인식 자동화 프로그램은
OpenCV, Pillow, numpy 등 의존성이 많습니다.

문제 발생 시:

```bash
pyinstaller --onefile --hidden-import=cv2 main.py
```

또는

```bash
pyinstaller --onefile --collect-all opencv-python main.py
```

---

## 8️⃣ spec 파일로 고급 설정하기

처음 빌드하면 `.spec` 파일이 생성됩니다.

```
main.spec
```

이 파일을 수정하면:

- 포함 파일 세부 제어
- 빌드 옵션 고정
- 반복 빌드 자동화

가능합니다.

빌드:

```bash
pyinstaller main.spec
```

---

## 9️⃣ 백신 오탐 문제 해결

자동화 프로그램은 종종 백신에서 오탐합니다.

해결 방법:

- 최신 PyInstaller 사용
- UPX 비활성화:

```bash
pyinstaller --onefile --noupx main.py
```

- 코드 서명 (기업 배포 시 필수)

---

## 🔟 배포 체크리스트

✔ 관리자 권한 필요한가?
✔ 외부 이미지 파일 포함했는가?
✔ OpenCV hidden-import 처리했는가?
✔ 콘솔창 숨김 설정했는가?
✔ 바이러스 오탐 테스트했는가?

---

## 🔥 실전 추천 빌드 명령어 (자동화 프로그램 기준)

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --icon=icon.ico ^
  --noupx ^
  --collect-all opencv-python ^
  main.py
```

---

## 💡 exe 자동 업데이트는?

간단한 방법:

- GitHub Releases 사용
- 시작 시 버전 체크 후 다운로드
- 또는 Inno Setup으로 설치 프로그램 제작

---

## 마무리

Python 프로그램을 exe로 만드는 것은 어렵지 않지만,
**외부 리소스 포함과 의존성 처리**가 핵심입니다.

자동화 프로그램(특히 pyautogui + OpenCV)은
테스트 → 빌드 → 테스트 과정을 꼭 반복하세요.

---
