---
title: "Ubuntu 서비스 등록 방법 (systemd 완전 정리)"
date: 2026-04-04
categories: [Linux, Ubuntu]
tags: [ubuntu, systemd, service, linux, devops]
description: "Ubuntu에서 systemd를 이용해 서비스를 등록하고 자동 실행하는 방법을 초보자도 이해할 수 있도록 자세히 설명합니다."
---

Ubuntu에서 프로그램을 **자동 실행 서비스로 등록**하려면 `systemd`를 사용합니다.
서버 운영, 백엔드 실행, 봇 자동화 등에 필수적인 작업입니다.

---

## 📌 1. systemd란?

- Ubuntu의 기본 서비스 관리 시스템
- 부팅 시 자동 실행, 재시작, 상태 관리 가능
- `systemctl` 명령어로 제어

---

## 📁 2. 서비스 파일 위치

서비스 파일은 아래 경로에 생성합니다:

```bash
/etc/systemd/system/
````

예:

```bash
sudo nano /etc/systemd/system/myapp.service
```

---

## 🧾 3. 서비스 파일 작성

### 기본 구조

```ini
[Unit]
Description=My Python App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /app/main.py
WorkingDirectory=/app
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```

---

## 🔍 항목 설명

### 🔹 [Unit]

* `Description`: 서비스 설명
* `After`: 어떤 서비스 이후 실행할지 (보통 network)

---

### 🔹 [Service]

* `ExecStart`: 실행 명령어
* `WorkingDirectory`: 실행 위치
* `Restart`: 자동 재시작 옵션
* `User`: 실행 사용자

---

### 🔹 [Install]

* `WantedBy`: 부팅 시 어떤 타겟에서 실행할지

---

## ⚙️ 4. 환경변수 설정 (중요🔥)

여러 줄 선언 가능합니다:

```ini
[Service]
Environment="TZ=Asia/Seoul"
Environment="PATH=/usr/local/bin:/usr/bin"
```

또는 파일로 관리:

```ini
EnvironmentFile=/etc/myapp.env
```

---

## ▶️ 5. 서비스 적용 및 실행

### systemd 리로드

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
```

---

### 서비스 시작

```bash
sudo systemctl start myapp
```

---

### 부팅 시 자동 실행

```bash
sudo systemctl enable myapp
```

---

## 🔄 6. 상태 확인 및 로그

### 상태 확인

```bash
sudo systemctl status myapp
```

---

### 로그 확인 (중요🔥)

```bash
journalctl -u myapp -f
```

---

## 🛑 7. 서비스 중지 및 재시작

```bash
sudo systemctl stop myapp
sudo systemctl restart myapp
```

---

## 🧪 8. 실전 예제 (Python 서버)

```ini
[Unit]
Description=FastAPI Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/app
ExecStart=/usr/bin/python3 main.py
Restart=always

Environment="TZ=Asia/Seoul"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

---

## 🚨 9. 자주 발생하는 문제

### ❌ 실행이 안 될 때

* 경로 문제 (`which python3` 확인)
* 권한 문제
* WorkingDirectory 누락

---

### ❌ 환경변수 적용 안 될 때

* `Environment=` 따옴표 필수
* 여러 줄로 선언 가능

---

### ❌ 코드 변경 반영 안됨

```bash
sudo systemctl daemon-reload
sudo systemctl restart myapp
```

---

## 💡 10. 꿀팁

* 로그는 무조건 `journalctl` 확인
* `Restart=always`는 거의 필수
* Python은 절대경로 사용 추천

---

## ✅ 정리

| 항목        | 설명                            |
| ----------- | ------------------------------- |
| 서비스 등록 | `/etc/systemd/system/*.service` |
| 실행        | `systemctl start`               |
| 자동 실행   | `systemctl enable`              |
| 로그 확인   | `journalctl -u 서비스명`        |
| 환경변수    | `Environment=` 여러 줄 가능     |

---

## 🚀 마무리

Ubuntu 서비스 등록은 서버 운영의 기본입니다.
한 번 제대로 설정해두면 **재부팅에도 자동 실행 + 안정적인 운영**이 가능합니다.

---
