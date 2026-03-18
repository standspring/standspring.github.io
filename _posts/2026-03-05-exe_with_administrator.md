---
title: "Windows에서 관리자 권한으로 실행되는 exe 만드는 방법 (Python 자동화 프로그램 배포)"
date: 2026-03-05 00:00:00 +0900
categories: [python, windows]
tags: [python, exe, windows, administrator, pyinstaller, uac, privilege-elevation]
toc: true
toc_sticky: true
---

Python으로 만든 자동화 프로그램을 exe로 배포했는데
실행하면 이런 문제가 생기는 경우가 많습니다.

- 특정 프로그램 창 활성화 실패
- 관리자 권한 프로그램 클릭 불가
- 키 입력 전달 안 됨
- UAC 보호된 창 접근 실패

특히 `pyautogui`, `pygetwindow`, UI 자동화 계열은
**대상 프로그램이 관리자 권한이면 내 exe도 관리자 권한이어야 합니다.**

즉:

> 일반 exe → 관리자 프로그램 제어 실패
> 관리자 exe → 정상 동작

---

## 1️⃣ 왜 관리자 권한이 필요한가?

Windows는 보안상:

**낮은 권한 프로세스가 높은 권한 프로세스를 제어하지 못하도록 막습니다.**

예:

- 삼성증권 HTS
- 일부 기업 업무 프로그램
- 설정창
- 레지스트리 접근

이런 프로그램은 관리자 권한으로 실행되는 경우가 많습니다.

---

## 2️⃣ Python 코드에서 관리자 권한 요청하기

가장 많이 쓰는 방법:

```python
import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1
    )
    sys.exit()
```

---

### 동작 원리

현재 관리자 권한이 아니면:

✔ UAC 팝업 발생
✔ 관리자 권한으로 자기 자신 재실행

즉:

현재 프로세스 종료 → 관리자 권한 새 프로세스 시작

---

## 3️⃣ exe 배포 시 그대로 적용 가능

PyInstaller 빌드 후에도 그대로 동작합니다.

```bash
pyinstaller --onefile main.py
```

---

## 4️⃣ exe 상태에서 sys.executable 의미

exe로 빌드되면:

```python
sys.executable
```

은:

```text
main.exe
```

를 가리킵니다.

즉 관리자 권한 재실행이 그대로 가능합니다.

---

## 5️⃣ 콘솔창 없는 GUI 프로그램에서 사용

```python
import ctypes
import sys

def elevate():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        None,
        None,
        1
    )
    sys.exit()
```

프로그램 시작 직후 호출:

```python
elevate()
```

---

## 6️⃣ 아예 exe 자체를 항상 관리자 권한으로 실행시키기

PyInstaller만으로는 기본 지원이 약합니다.

실전에서는:

### manifest 파일 사용

`app.manifest`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
```

---

### 빌드 시 적용

```bash
pyinstaller --onefile --manifest app.manifest main.py
```

---

### 결과

exe 실행 즉시:

✔ 항상 UAC 팝업 발생
✔ 관리자 권한 실행 보장

---

## 7️⃣ 어떤 방식이 더 좋은가?

### 코드 방식

장점:

* 조건부 실행 가능
* 코드 안에서 제어 가능

추천 상황:

* 일부 기능만 관리자 필요할 때

---

### manifest 방식

장점:

* 항상 안정적

추천 상황:

* pyautogui 자동화
* HTS 자동화
* 업무툴 배포

---

## 8️⃣ pyautogui 자동화에서 매우 중요한 이유

예를 들어:

```python
win.activate()
pyautogui.click()
```

안 되는 경우 대부분:

대상 창이 관리자 권한

즉 내 프로그램도 관리자 권한이어야 합니다.

---

## 9️⃣ 관리자 권한 확인 로그 추가

```python
print(ctypes.windll.shell32.IsUserAnAdmin())
```

출력:

```text
True
```

면 정상

---

## 🔟 실전 추천 구조

```python
elevate()

focus_window(win)
wait_and_click("buy.png")
```

프로그램 시작 즉시 권한 확보 후 자동화 시작

---

## 🔥 배포 시 추천 빌드

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --icon=icon.ico ^
  --manifest app.manifest ^
  main.py
```

---

## 🚨 주의사항

관리자 권한 exe는:

* 백신 민감도 증가
* 사용자 UAC 허용 필요
* 네트워크 접근 정책 영향 가능

---

## 마무리

Windows 자동화 프로그램에서 관리자 권한은 선택이 아니라 필수인 경우가 많습니다.

특히:

* pyautogui
* pygetwindow
* UIA
* HTS 자동화

는 대부분 관리자 권한 여부가 성공률을 좌우합니다.

---
