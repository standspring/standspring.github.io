---
title: "컴퓨터를 매일 특정 시간에 자동 부팅시키는 BIOS 설정법"
date: 2026-03-18 00:00:00 +0900
categories: bios
tags: [bios, automation, rtc, power-on, bios 자동 부팅, rtc alarm 설정, power on by rtc, 컴퓨터 자동 켜기, uefi, wake-on-rtc]
toc: true
toc_sticky: true
---

컴퓨터를 **매일 아침 특정 시간에 자동으로 켜고 싶을 때**,
Windows 작업 스케줄러만으로는 해결되지 않는다.

왜냐하면 **전원이 꺼진 상태(S5)** 에서는 운영체제가 동작하지 않기 때문이다.

이럴 때 사용하는 기능이 바로 BIOS/UEFI 안의 **RTC Alarm 기능**이다.

RTC는 **Real-Time Clock (실시간 시계)** 를 의미하며,
메인보드가 내장 시계를 이용해 지정한 시각에 전원을 넣는다.

---

## 1. BIOS 자동 전원 기능 이름

제조사마다 이름이 다르다.

대표적으로 아래 이름으로 표시된다.

- Power On By RTC
- Resume By Alarm
- RTC Alarm Power On
- Wake Up Event Setup
- Automatic Power On

즉 이름은 달라도 핵심은 같다.

👉 정해진 시간에 전원 공급

---

## 2. BIOS 진입 방법

컴퓨터 전원을 켜자마자 아래 키를 연타한다.

- DEL
- F2
- 일부 노트북은 F10 / ESC

메인보드 브랜드별 예:

- ASUS → DEL / F2
- MSI → DEL
- Gigabyte → DEL
- ASRock → DEL / F2

---

## 3. BIOS에서 찾는 메뉴 위치

대부분 여기 중 하나에 있다.

### ASUS 계열

Advanced → APM Configuration

찾아야 하는 항목:

- Power On By RTC
- Enabled

추가 설정:

- Hour
- Minute
- Second

![ASUS BIOS](/assets/img/2026-03-18-bios1.jpg)

![ASUS BIOS RTC](/assets/img/2026-03-18-bios2.jpg)

---

### MSI 계열

Settings → Advanced → Wake Up Event Setup

항목:

- Resume By RTC Alarm

설정:

- Every Day
- Hour / Minute / Second

---

### Gigabyte 계열

Power Management → Resume By Alarm

---

## 4. Every Day / 특정 날짜 차이

여기서 가장 많이 헷갈린다.

보통 BIOS는 두 방식 제공:

### Every Day

매일 반복 실행

### Fixed Date

특정 날짜 1회 실행

매일 자동 부팅하려면 반드시 **Every Day** 선택

---

## 5. 저장 방법

설정 후 반드시 저장

- F10 → Save & Exit

저장 안 하면 적용 안 된다.

---

## 6. 반드시 확인해야 하는 조건

자동 부팅이 안 되는 가장 흔한 이유:

### 전원 멀티탭 OFF 상태

메인보드 대기전원이 살아 있어야 한다.

즉:

- 멀티탭 OFF ❌
- 파워 스위치 OFF ❌

---

### CMOS 배터리 문제

배터리가 약하면 RTC 시간이 유지되지 않는다.

보통 사용하는 배터리:

- CR2032

---

### ERP 설정이 켜져 있으면 안 됨

ERP가 켜져 있으면 대기전원 차단됨.

BIOS 메뉴:

- ERP Ready → Disabled

---

## 7. Windows 절전과 차이

많은 사람이 혼동한다.

### BIOS RTC

완전 종료 상태에서도 가능

### Windows 작업 스케줄러

절전 상태에서만 깨우기 가능

즉:

👉 완전 종료 자동 부팅 = BIOS 필수

---

## 8. 추천 실사용 조합

실제로 가장 많이 쓰는 조합:

### BIOS

매일 08:50 자동 부팅

### Windows 작업 스케줄러

09:00 프로그램 실행

예:

- 자동매매 프로그램
- 백업 프로그램
- 원격접속 준비

---
