---
title: "삼성증권 HTS 자동 매매 구현기"
date: 2026-03-07 00:00:00 +0900
categories: [python, automation]
tags: [python, 삼성증권, 자동매매, automation]
toc: true
toc_sticky: true
---

삼성증권 HTS를 이용해 자동 매매를 구현할 때 가장 먼저 떠오르는 방법은 화면 좌표를 기반으로 클릭하는 방식이다.
하지만 실제 운영 환경에서는 단순 좌표 자동화만으로는 안정성을 확보하기 어렵다.

이 글에서는 삼성증권 HTS 자동 매매를 구현하면서 사용한 구조와, 실제로 겪었던 문제들을 코드 예시와 함께 정리한다.

---

## 1. 왜 API 대신 HTS 자동화를 선택했는가

삼성증권은 일반 개인 트레이더 대상으로 Open API 를 제공하지 않습니다.

수수료 혜택으로 증권사를 옮길수는 없었으니, 삼성증권에서 어떻게든 자동화를 해보려고 시작했다.

초기 구현은 가장 빠른 방식인 PyAutoGUI부터 시작했다.

```python
import pyautogui

pyautogui.moveTo(1674, 1042)
pyautogui.click()
```


하지만 이 방식은 다음 문제가 있다.

- 창 위치가 달라지면 실패
- 해상도 변경 시 오동작
- 팝업 발생 시 잘못 클릭 가능

따라서 좌표는 최후 수단으로만 사용한다.

---

## 2. 전체 구조

자동 매매 흐름은 다음처럼 나뉜다.

1. HTS 실행 확인
2. 주문 창 열기/찾기
3. 매수 / 매도 탭 선택
4. 종목 선택
5. 매수 구분 선택
6. 수량/단가 입력
7. 비밀번호 입력
8. 주문 버튼 실행
9. 결과 로그 저장

핵심은 다음 두 가지를 분리하는 것이다.

---

## 3. HTS 실행 혹은 실행 여부 확인

우선 python 에서 어떻게 특정 프로그램이 실행되고 있는지 확인하는 방법으로는 `pygetwindow` 와 `pywinauto`가 있다.

둘 다 윈도우 창을 다루지만 목적이 다르다.

---

### pygetwindow는 "창 단위 제어"

`pygetwindow`는 말 그대로 **현재 열린 윈도우 창(Window) 자체를 찾고 이동하는 라이브러리**다.

대표적으로 가능한 것:

* 창 제목 찾기
* 창 존재 여부 확인
* 창 활성화
* 창 이동
* 창 크기 변경

예를 들어 HTS 실행 여부 확인은 아주 잘 맞는다.

```python
import pygetwindow as gw

windows = gw.getWindowsWithTitle("삼성증권")

if windows:
    print("HTS 실행 중")
else:
    print("HTS 없음")
```

즉:

#### pygetwindow가 잘하는 것

✅ 창이 떠 있는가
✅ 현재 활성화 가능한가
✅ 앞으로 가져오기

---

### pywinauto는 "창 내부 요소 제어"

`pywinauto`는 창 내부의 버튼, 탭, 입력창까지 접근한다.

즉:

* 버튼 클릭
* 탭 선택
* Edit 입력
* Control 탐색

예:

```python id="pwa001"
from pywinauto import Desktop

dlg = Desktop(backend="uia").window(title_re=".*삼성증권.*")
btn = dlg.child_window(title="매수주문", control_type="Button")
btn.click_input()
```

---

### 핵심 차이

`pygetwindow` 는 집 주소 찾기
`pywinauto` 는 집 안 들어가서 스위치 누르기

`pygetwindow`
창까지만 본다.
> "삼성증권 창이 있나?"

`pywinauto`
창 안까지 본다.
> "삼성증권 창 안에 매수주문 버튼 있나?"

---

### HTS 자동매매에서 실제 역할 분담

추천 구조는 이렇다.

##### pygetwindow

초기 상태 체크
* 삼성증권 실행 여부
* 창 활성화
* 최상단 올리기

##### pywinauto

주문 단계
* 탭 찾기
* 버튼 찾기
*입력창 찾기

---

### 왜 pygetwindow부터 쓰기 쉬웠나

이유는 단순하다.

HTS 자동화 초기에 가장 먼저 필요한 건:

**"실행되어 있나?"**

이거다.

그래서 pygetwindow가 빠르고 단순했다.

---

**하지만 결국 pywinauto가 필요해지는 이유**

좌표 기반만 쓰면 위험하기 때문.

예:

* 해외매수 탭 상태 확인 필요
* 버튼 활성 상태 확인 필요
* 팝업 창 구분 필요

이건 pygetwindow가 못 한다.

---

**성능 차이도 있음**

`pygetwindow` 빠름

`pywinauto` 느리지만 정밀함

---

### 실전 추천 조합

1. pygetwindow → HTS 존재 확인
2. pygetwindow → 활성화
3. pywinauto → 주문창 요소 찾기
4. pyautogui → 최종 입력 보조

---

### 삼성증권 프로그램 실행 여부 체크

프로그램 타이틀에 POP 또는 삼성 으로 된 것이 있는지 확인하고, 있으면 활성화

```python
import pygetwindow
def is_HTS_running():
    for w in pygetwindow.getAllWindows():
        if w.title and ("POP" in w.title or "삼성" in w.title):
            w.activate()
            return True
    return False
```

### 삼성증권 프로그램이 실행된 상태가 아니라면

subprocess 로 hts 를 실행
```python
import subprocess

subprocess.Popen(r"C:\삼성증권\POPHTSN\pophts.exe")
```

### 로그인

처음 실행시키면, 인증서 비밀번호를 입력하는 로그인 절차를 진행해야한다.

HTS를 실행시키더라도, 현재 시점에 어떤 창이 활성화 된 것인지 알 수 없으므로, 인증서 비밀번호 입력하는 칸을 활성화해야한다.

버튼을 어떻게 찾느냐는 `pyautogui` 또는 `cv2`를 이용할 수 있다.

앞서 설명한바와 같이, 좌표 방식은 오류 가능성이 높으므로 이미지 인식 기반 탐색을 이용한다.


#### 이미지 인식 기반 좌표 반환

아래 함수를 이용해서, 원하는 버튼이 어디 있는지 좌표를 반환받을 수 있다.
template_path는 사전에 캡처해놓은 버튼 이미지 위치이다.

```python
import cv2
import numpy as np

def locate_center(template_path: Path, confidence: float = CONF_DEFAULT):
    # 현재 전체 화면을 캡처 (PIL Image 반환)
    screen = np.array(pyautogui.screenshot())

    # PyAutoGUI는 RGB 형식이므로 OpenCV용 BGR 형식으로 변환
    screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # 템플릿 이미지 파일 읽기 (찾고 싶은 버튼 이미지)
    templ = _read_template(template_path)

    # 화면(screen_bgr) 안에서 템플릿(templ)과 가장 유사한 위치 탐색
    # TM_CCOEFF_NORMED는 정규화된 상관계수 방식 (1에 가까울수록 유사)
    res = cv2.matchTemplate(screen_bgr, templ, cv2.TM_CCOEFF_NORMED)

    # 매칭 결과 중 최소값/최대값과 위치 추출
    # max_val = 가장 유사한 정도
    # max_loc = 가장 유사한 좌측 상단 좌표
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # 최고 유사도가 기준(confidence)보다 낮으면 실패 처리
    if max_val < confidence:
        return None, float(max_val)

    # 템플릿 높이(th), 너비(tw) 추출
    th, tw = templ.shape[:2]

    # max_loc는 좌측 상단 좌표이므로 중심 좌표 계산
    center_x = max_loc[0] + tw // 2
    center_y = max_loc[1] + th // 2

    # 중심 좌표와 유사도 반환
    return (int(center_x), int(center_y)), float(max_val)
```

해당 좌표에서 오른쪽으로 얼마간 offset을 주고 클릭을 하면, 비밀번호를 입력하는 칸을 선택할 수 있다.

![삼성증권 로그인창](/assets/img/2026-03-07-login.png)

클릭은 `pyautogui.click()`을 이용한다. 텍스트 입력은 `pyautogui.write()` 를 이용한다.

```python
pyautogui.click(x + x_offset, y + y_offset)
pyautogui.write(text, interval=0.02)
```

비밀번호를 입력하고 나면, 확인 버튼을 찾아서 클릭한다.
이로써 HTS를 실행하고 로그인까지 하였다.

이후 절차는 이와 유사하다. 원하는 버튼을 찾는다 -> 클릭한다 -> 입력한다 의 반복이라고 볼 수 있다.


---

다음 글에서 주문창 열기부터, 유사하게 하는데도 안되서 다른 방법으로 구현했던 부분도 기술하겠다.
