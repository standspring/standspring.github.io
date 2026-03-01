---
title: pyautogui 이미지 인식 기반 자동화 고급편 (실전 안정화 전략)
date: "2026-03-01 21:00:00 +0900"
categories: [Python, Automation]
tags: [python, pyautogui, opencv, automation, image-recognition, rpa]
---

# pyautogui 이미지 인식 기반 자동화 고급편

좌표 기반 자동화는 빠르지만 치명적인 단점이 있습니다.

- 해상도 바뀌면 깨짐
- 창 위치 바뀌면 오작동
- UI 조금만 바뀌어도 실패

그래서 실전에서는 **이미지 인식 기반 자동화**를 사용합니다.

이번 글에서는 단순 `locateOnScreen()`을 넘어서
**실전에서 안정적으로 사용하는 고급 전략**을 정리합니다.

---

# 1️⃣ 기본 준비

## 설치

```bash
pip install pyautogui opencv-python
```

> `confidence` 옵션은 OpenCV 설치가 필수입니다.

---

# 2️⃣ 기본 이미지 인식 구조

```python
import pyautogui

location = pyautogui.locateOnScreen("button.png", confidence=0.9)

if location:
    pyautogui.click(location)
```

하지만 이 코드는 실전에서 거의 그대로 쓰기 어렵습니다.

왜냐하면:

- 못 찾으면 None
- 찾는 동안 느림
- 여러 개면 첫 번째만 반환
- 화면 전체 검색 → 매우 느림

이제부터 고급 전략으로 개선합니다.

---

# 3️⃣ 검색 영역 제한 (속도 5~10배 향상)

전체 화면 대신 **특정 영역만 검색**하면 속도가 극적으로 빨라집니다.

```python
region = (100, 200, 800, 600)

location = pyautogui.locateOnScreen(
    "button.png",
    region=region,
    confidence=0.9
)
```

💡 실전 팁
창 위치를 `pygetwindow`로 고정한 뒤
그 창 내부 좌표만 region으로 지정하세요.

---

# 4️⃣ center() 사용해서 정확히 클릭

```python
location = pyautogui.locateOnScreen("button.png", confidence=0.9)

if location:
    x, y = pyautogui.center(location)
    pyautogui.click(x, y)
```

직접 `click(location)` 하지 말고
**반드시 center()를 거쳐 클릭하는 습관**이 좋습니다.

---

# 5️⃣ 여러 개 찾기 (locateAllOnScreen)

같은 버튼이 여러 개 있을 경우:

```python
matches = list(pyautogui.locateAllOnScreen("item.png", confidence=0.9))

for m in matches:
    x, y = pyautogui.center(m)
    pyautogui.click(x, y)
```

---

# 6️⃣ 안정적인 "기다림 로직" 만들기

실전 자동화는 반드시 **대기 로직**이 필요합니다.

❌ 잘못된 방식:

```python
pyautogui.click("button.png")
```

✅ 올바른 방식:

```python
import time

def wait_and_click(image, timeout=10, confidence=0.9):
    start = time.time()

    while time.time() - start < timeout:
        location = pyautogui.locateOnScreen(image, confidence=confidence)
        if location:
            x, y = pyautogui.center(location)
            pyautogui.click(x, y)
            return True
        time.sleep(0.3)

    return False
```

사용:

```python
if not wait_and_click("confirm.png"):
    raise RuntimeError("확인 버튼을 찾지 못했습니다.")
```

---

# 7️⃣ 그레이스케일 모드로 속도 향상

```python
location = pyautogui.locateOnScreen(
    "button.png",
    confidence=0.9,
    grayscale=True
)
```

✔ 속도 증가
✔ 색상 변화에 덜 민감

---

# 8️⃣ 이미지 캡처 잘 만드는 법 (성공률의 70%)

이미지가 잘못되면 자동화는 실패합니다.

### ✅ 좋은 이미지 조건

- 버튼만 정확히 크롭
- 여백 최소화
- 텍스트만 따로 자르지 말 것 (배경 일부 포함)
- 해상도 동일 환경에서 캡처

### ❌ 피해야 할 것

- hover 상태 캡처
- 클릭 후 색상 바뀐 상태
- 그림자 포함

---

# 9️⃣ 예외 처리 + 로그 구조 (실전용)

```python
import logging

logging.basicConfig(level=logging.INFO)

def safe_click(image):
    location = pyautogui.locateOnScreen(image, confidence=0.9)
    if not location:
        logging.error(f"{image} not found")
        return False

    x, y = pyautogui.center(location)
    pyautogui.click(x, y)
    logging.info(f"{image} clicked")
    return True
```

---

# 🔟 실전 구조 예시 (HTS 자동화 흐름)

```python
focus_window(win)
wait_and_click("buy_tab.png")
wait_and_click("order_button.png")
wait_and_click("confirm.png")
```

**핵심은 좌표가 아니라 상태 기반 자동화**입니다.

- 버튼이 보이면 클릭
- 안 보이면 기다림
- timeout 시 예외 발생

---

# 🚨 실전에서 가장 중요한 3가지

1. 창 위치 고정
2. region 제한
3. timeout 대기 로직

이 세 가지만 지켜도 오작동 확률이 크게 줄어듭니다.

---

# 🔥 마무리

이미지 인식 기반 자동화는
단순 매크로가 아니라 **RPA 수준의 자동화**로 가는 첫 단계입니다.

좌표 자동화는 빠르지만 깨지기 쉽고,
이미지 기반 자동화는 느리지만 안정적입니다.

실전에서는:

> 좌표 + 이미지 혼합 전략
> (창 고정 → region 제한 → 이미지 인식 → center 클릭)

이 구조가 가장 안정적입니다.

---
