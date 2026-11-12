---
title: "Windows PyGetWindow 사용법: PyAutoGUI 대상 창 찾기·활성화·좌표 고정"
description: "Windows에서 PyGetWindow로 대상 창을 찾아 복구·활성화하고 크기와 위치를 고정합니다. 이미지 검색 및 예약 실행과 연결할 때 확인할 점도 설명합니다."
date: "2026-03-01 00:00:00 +0900"
categories: [python, automation]
tags: [python, pyautogui, pygetwindow, automation, windows, hts, 자동화, window-control]
image:
  path: /assets/img/2026-03-01-pyautogui_pygetwindow_guide-handwritten-hero.webp
  alt: "Windows PyGetWindow 사용법: PyAutoGUI 대상 창 찾기·활성화·좌표 고정의 핵심 개념과 흐름"
---
![PyAutoGUI and PyGetWindow GUI automation workflow](/assets/img/2026-03-01-pyautogui-pygetwindow-guide.png)

`pyautogui`만으로도 클릭/입력 자동화는 가능하지만, 실전(특히 HTS/업무 프로그램 자동화)에서는
**"어떤 창을 대상으로 자동화하느냐"** 가 핵심입니다.

이때 유용한 조합이:

- `pygetwindow`: 창 목록 조회 / 특정 창 찾기 / 이동 / 크기조절 / 활성화
- `pyautogui`: 활성화된 창을 대상으로 클릭 / 키보드 입력 / 스크린샷

즉, **창 선택/정렬은 pygetwindow**, **실제 조작은 pyautogui**가 담당합니다.

아래 예제는 `Win32Window`를 사용하는 **Windows용 코드**입니다. PyAutoGUI 입력은 현재 포커스를 가진 창으로 전달되며, 라이브러리가 입력 대상을 특정 창에 고정해 주는 것은 아닙니다. 대상 제목과 화면을 먼저 확인하세요.

---

## 1) 설치

```bash
pip install pyautogui pygetwindow
```

> `pyautogui.locateOnScreen(..., confidence=...)` 를 쓰려면 OpenCV도 설치하세요.

```bash
pip install opencv-python
```

---

## 2) 기본 안전 설정 (필수)

자동화는 실수하면 마우스가 의도와 다르게 움직이거나, 원치 않는 곳에 입력할 수 있어요.
아래 두 줄은 거의 필수로 넣어두는 걸 추천합니다.

```python
import pyautogui

pyautogui.FAILSAFE = True   # 주 모니터 모서리에서 FailSafeException 발생
pyautogui.PAUSE = 0.2       # 각 동작 사이 0.2초 쉬기
```

---

## 3) 현재 열려있는 창 목록 확인

`pygetwindow.getAllWindows()` 로 전체 창을 볼 수 있어요.

```python
import pygetwindow as gw

for w in gw.getAllWindows():
    title = (w.title or "").strip()
    if title:
        print(title)
```

창 제목이 너무 길거나 공백이 섞이는 경우가 많으니 `.strip()` 습관이 좋습니다.

---

## 4) 특정 창 찾기 (키워드 매칭)

예: "POP", "HTS", "삼성" 같은 키워드로 HTS 창을 찾아서 제어하기

```python
import pygetwindow as gw

def find_window_by_keywords(keywords: list[str]):
    for w in gw.getAllWindows():
        title = (w.title or "").strip()
        if not title:
            continue
        if any(k in title for k in keywords):
            return w
    return None

win = find_window_by_keywords(["POP", "HTS", "삼성"])
print(win.title if win else "창을 찾지 못했습니다.")
```

---

## 5) 창 활성화 / 최소화 복구 / 앞으로 가져오기

자동화에서 제일 중요한 단계입니다.
`pyautogui`는 기본적으로 **현재 활성화된 화면**을 기준으로 동작하니까요.

```python
import time
import pygetwindow as gw

def focus_window(win: gw.Win32Window) -> None:
    # 최소화 상태면 복구
    if win.isMinimized:
        win.restore()
        time.sleep(0.2)

    # 창 활성화(앞으로)
    win.activate()
    time.sleep(0.2)
```

---

## 6) 창 위치/크기 고정 (좌표 자동화 안정화)

해상도/모니터 배치가 달라지거나, 창이 조금만 움직여도 좌표 기반 자동화는 깨집니다.
그래서 보통 **좌표 자동화 전에 창을 항상 동일한 위치/크기로 고정**합니다.

```python
import time
import pygetwindow as gw

def set_window_geometry(win: gw.Win32Window, left=0, top=0, width=1400, height=900) -> None:
    win.moveTo(left, top)
    time.sleep(0.1)
    win.resizeTo(width, height)
    time.sleep(0.1)
```

---

## 7) (실전) 창 제어 + 창 영역만 캡처 저장

아래는 `pygetwindow`로 HTS 창을 찾고 → 포커스/정렬하고 → 그 창 영역만 캡처하는 예제입니다.

```python
from pathlib import Path
import time
import pygetwindow as gw
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

def find_window_by_keywords(keywords: list[str]):
    for w in gw.getAllWindows():
        title = (w.title or "").strip()
        if not title:
            continue
        if any(k in title for k in keywords):
            return w
    return None

def focus_window(win: gw.Win32Window) -> None:
    if win.isMinimized:
        win.restore()
        time.sleep(0.2)
    win.activate()
    time.sleep(0.2)

def set_window_geometry(win: gw.Win32Window, left=0, top=0, width=1400, height=900) -> None:
    win.moveTo(left, top)
    time.sleep(0.1)
    win.resizeTo(width, height)
    time.sleep(0.1)

def screenshot_window(win: gw.Win32Window, path: Path) -> None:
    left, top = win.left, win.top
    width, height = win.width, win.height
    img = pyautogui.screenshot(region=(left, top, width, height))
    img.save(str(path))

def main():
    win = find_window_by_keywords(["POP", "HTS", "삼성"])
    if not win:
        raise RuntimeError("대상 창을 찾지 못했습니다.")

    focus_window(win)
    set_window_geometry(win, left=10, top=10, width=1500, height=950)

    out = Path("hts_capture.png")
    screenshot_window(win, out)
    print("saved:", out.resolve())

if __name__ == "__main__":
    main()
```

---

## 8) (실전) 클릭/입력 자동화까지 연결하기

창을 포커스한 뒤에는 `pyautogui`로 클릭/입력하면 됩니다.

```python
import pyautogui

# 예시: (x, y) 좌표 클릭 후 주문 수량 입력하고 Enter
pyautogui.click(1200, 750)
pyautogui.write("10")
pyautogui.press("enter")
```

> 좌표는 반드시 **창 크기/위치를 고정한 뒤** 잡으세요.

---

## 9) 흔한 문제 & 팁

### 1) `activate()`가 안 먹히는 경우

- 관리자 권한(UAC) 프로그램은 일반 권한 파이썬에서 포커스가 막힐 수 있습니다.
- 해결: 파이썬/터미널을 관리자 권한으로 실행해보기

권한 상승이 포커스 성공을 보장하지는 않습니다. 최소화 복구, 대상 창 확인, 대화형 세션과 권한을 나누어 점검하고 [관리자 권한 요청 방식]({% post_url 2026-03-05-exe_with_administrator %})을 필요한 경우에만 적용합니다.

### 2) 멀티모니터에서 좌표가 틀어지는 경우

- 창을 항상 같은 모니터(예: 주 모니터 좌상단)로 이동시키고 시작하기
- `moveTo(0,0)` 고정 전략이 효과적

### 3) 이미지 인식이 불안정한 경우

- `confidence=0.9` 같은 옵션 사용(OpenCV 필요)
- 버튼 PNG는 “크롭을 타이트하게”, 배경 변화가 적은 부분 위주로

---

## 마무리

`pyautogui`는 **조작**, `pygetwindow`는 **대상 창 제어**를 담당합니다.
이 조합만 갖춰도 자동화 안정성이 확 올라가고, “창 찾기 → 정렬 → 캡처/클릭/입력” 같은 실전 흐름이 만들어집니다.

이미지가 보이는데 검색되지 않으면 [PyAutoGUI 이미지 인식 진단]({% post_url 2026-03-01-pyautogui_image_recognition_advanced %})을 확인합니다. 직접 실행은 되는데 예약 실행만 실패하면 [작업 스케줄러의 계정·로그온 조건]({% post_url 2026-03-06-task_scheduler %})을 점검합니다.

## 참고 자료

- [PyGetWindow 공식 문서](https://pygetwindow.readthedocs.io/en/latest/)
- [PyAutoGUI 공식 문서](https://pyautogui.readthedocs.io/en/latest/)
