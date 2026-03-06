---
title: "Windows 작업 스케줄러 등록 자동화 (Python 프로그램 예약 실행 실전 가이드)"
date: 2026-03-06 00:00:00 +0900
categories: [python, automation]
tags: [python, windows, task scheduler, automation, schtasks, scheduling]
toc: true
toc_sticky: true
---

Python 자동화 프로그램이나 exe를 만들고 나면
다음 단계는 보통 **정해진 시간에 자동 실행**입니다.

예를 들면:

- 매일 오전 8시 자동 실행
- 장 시작 전 자동 로그인
- 특정 시각 데이터 수집
- 매일 백업 실행

Windows에서는 **작업 스케줄러(Task Scheduler)** 를 사용하면 됩니다.

이번 글에서는:

- 수동 등록
- 명령어 등록 (`schtasks`)
- Python에서 자동 등록
- 관리자 권한 포함 실행

까지 실전 기준으로 정리합니다.

---

## 1️⃣ Windows 작업 스케줄러란?

Windows 기본 기능으로:

> 특정 시간 / 특정 조건에서 프로그램 자동 실행

가능합니다.

실행 대상:

- `.exe`
- `.bat`
- `.cmd`
- `.ps1`

모두 가능

---

## 2️⃣ 가장 기본 등록 (수동)

실행:

```text
작업 스케줄러 → 작업 만들기
````

설정:

### 일반 탭

* 이름 입력
* "가장 높은 수준의 권한으로 실행" 체크

### 트리거

* 매일
* 특정 시간

### 동작

프로그램 시작:

```text
C:\myapp\main.exe
```

---

## 3️⃣ 명령어로 등록 (schtasks)

Windows 기본 명령:

```bash
schtasks /create /tn "MyAutoJob" /tr "C:\myapp\main.exe" /sc daily /st 08:00
```

설명:

* `/tn` 작업 이름
* `/tr` 실행 파일
* `/sc` 주기
* `/st` 시간

---

## 4️⃣ 관리자 권한 포함 등록

```bash
schtasks /create ^
 /tn "MyAutoJob" ^
 /tr "C:\myapp\main.exe" ^
 /sc daily ^
 /st 08:00 ^
 /rl highest
```

✔ `/rl highest` = 관리자 권한

자동화 프로그램에서는 거의 필수입니다.

---

## 5️⃣ Python에서 자동 등록하기

```python
import subprocess

cmd = [
    "schtasks",
    "/create",
    "/tn", "MyAutoJob",
    "/tr", r"C:\myapp\main.exe",
    "/sc", "daily",
    "/st", "08:00",
    "/rl", "highest"
]

subprocess.run(cmd, check=True)
```

---

## 6️⃣ 기존 작업 삭제

```bash
schtasks /delete /tn "MyAutoJob" /f
```

✔ `/f` = 확인 없이 삭제

Python:

```python
import subprocess

subprocess.run([
    "schtasks",
    "/delete",
    "/tn", "MyAutoJob",
    "/f"
])
```

---

## 7️⃣ 작업 존재 여부 확인

```bash
schtasks /query /tn "MyAutoJob"
```

Python:

```python
import subprocess

result = subprocess.run(
    ["schtasks", "/query", "/tn", "MyAutoJob"],
    capture_output=True,
    text=True
)

print(result.stdout)
```

---

## 8️⃣ 로그인 여부와 무관하게 실행

작업 스케줄러 설정에서:

✔ "사용자 로그온 여부와 관계없이 실행"

선택 가능

이 경우:

* 백그라운드 실행 가능
* 서버형 자동화 가능

---

## 9️⃣ exe + 관리자 권한 + 예약 실행 조합 (실전 최강 구조)

추천 구조:

```text
main.exe
 └ 작업 스케줄러 등록
    └ highest 권한
```

즉:

```text
PC 켜짐 → 예약 시간 도달 → 자동 실행
```

---

## 🔟 실전 예제 (매일 오전 7시30분)

```python
import subprocess

subprocess.run([
    "schtasks",
    "/create",
    "/tn", "StockMorningJob",
    "/tr", r"C:\stock\main.exe",
    "/sc", "daily",
    "/st", "07:30",
    "/rl", "highest"
])
```

---

## 🔥 pyautogui 자동화에서 중요한 점

주의:

작업 스케줄러는 화면 없는 상태에서는
GUI 자동화가 실패할 수 있습니다.

즉:

❌ 잠금 화면 상태 → pyautogui 실패
❌ 원격 종료 상태 → 실패

필수 조건:

✔ 로그인 상태 유지
✔ 화면 켜짐

---

## 🚨 가장 흔한 실패 원인

### 1) 경로 공백

```text
C:\Program Files\...
```

→ 반드시 따옴표 처리

---

### 2) 상대경로 사용

항상 절대경로 사용

---

### 3) 관리자 권한 누락

`/rl highest` 필수

---

## 마무리

Windows 작업 스케줄러는
Python 자동화 프로그램을 실전 운영 단계로 올려주는 핵심 도구입니다.

특히:

* pyautogui
* HTS 자동화
* 데이터 수집
* 백업

모두 예약 실행 구조가 안정성을 높입니다.

---
