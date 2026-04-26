---
title: "ssh-keygen 두 PC 간 비밀번호 없는 접속 설정"
date: 2026-04-27
categories: [Linux, DevOps]
tags: [ssh, ssh-keygen, 인증, 서버관리, 보안]
---

두 PC 간 **비밀번호 없이 SSH 접속하는 방법**

---

## 🔑 전체 흐름

| | PC A | PC B |
| --- | --- | --- |
| PC A에서 key 생성 | ssh-keygen -t rsa -b 4096 -C "key_of_PC_A"  |  |
| 생성된 개인키 | ~/.ssh/id_rsa | |
| 생성된 공개키 | ~/.ssh/id_rsa.pub | |
| 공개키를 PC B에 등록 | ssh-copy-id -i ~/.ssh/id_rsa.pub ID_of_PC_B@IP_of_PC_B  | |
| PC B 권한 설정 | | chmod 700 ~/.ssh
| PC B 권한 설정 | | chmod 600 ~/.ssh/authorized_keys |
| 접속 테스트 | ssh ID_of_PC_B@IP_of_PC_B | |


## 1️⃣ PC A에서 SSH 키 생성

```bash
ssh-keygen -t rsa -b 4096 -C "key_of_PC_A"
````

옵션 설명:

* `-t rsa` : RSA 방식 사용
* `-b 4096` : 키 길이 (보안 강화)
* `-C` : 식별용 주석

생성 결과:

```bash
~/.ssh/id_rsa        (개인키)
~/.ssh/id_rsa.pub    (공개키)
```

---

## 2️⃣ 공개키를 PC B로 전달

### 방법 1 (권장)

```bash
ssh-copy-id user@server_ip  // 공개키를 PC B로 전달
ssh-copy-id -i ~/.ssh/id_rsa.pub user@server_ip  // 키 파일을 명시하는 방법
```

예:

```bash
ssh-copy-id ubuntu@192.168.0.10
```

---

### 방법 2 (수동)

```bash
cat ~/.ssh/id_rsa.pub
```

출력된 내용을 복사 후 PC B에서:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
```

붙여넣기 후 저장


## 3️⃣ PC B 권한 설정 (매우 중요)

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

권한이 틀리면 SSH 접속이 거부될 수 있음

---

## 4️⃣ 접속 테스트

PC A에서 실행:

```bash
ssh user@server_ip
```

👉 비밀번호 없이 접속되면 성공

---

## 🔐 보안 강화 (선택)

PC B의 SSH 설정 파일 수정:

```bash
sudo nano /etc/ssh/sshd_config
```

다음 옵션 변경:

```bash
PasswordAuthentication no
PubkeyAuthentication yes
```

적용:

```bash
sudo systemctl restart ssh
```

---

## ⚠️ 자주 발생하는 문제

### 1. Permission denied (publickey)

* authorized_keys 권한 문제
* SSH 설정 문제
* 사용자 계정 불일치

---

### 2. 여전히 비밀번호 요구

* 키가 복사되지 않음
* 다른 키 사용 중 (`~/.ssh/config` 확인)

---

