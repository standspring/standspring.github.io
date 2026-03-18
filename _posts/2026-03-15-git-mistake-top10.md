---
title: "Git 초보자가 가장 많이 하는 실수 TOP10 (처음 시작하면 거의 다 겪는 문제들)"
date: 2026-03-15 00:00:00 +0900
categories: github
tags: [github, vcs, git, mistake, git-tips, troubleshooting]
toc: true
toc_sticky: true
---

Git은 처음 배울 때 명령어보다 **작동 원리** 때문에 더 헷갈립니다.

특히 초보자는 비슷한 실수를 반복합니다.

이번 글에서는 **Git 입문자가 가장 자주 하는 실수 10가지**를 실제 많이 발생하는 순서대로 정리합니다.

---

## 1. add 없이 commit 하려고 함

가장 흔한 실수입니다.

```bash
git commit -m "수정 완료"
```

그런데 아무 것도 commit 되지 않습니다.

왜냐하면 Git은 반드시 먼저 stage 해야 합니다.

정상 순서:

```bash
git add .
git commit -m "수정 완료"
```

핵심:

```plaintext
수정 → add → commit
```

---

## 2. git status 확인 안 함

초보자는 상태 확인 없이 바로 명령어를 입력합니다.

하지만 Git에서는 항상 먼저 상태를 보는 습관이 중요합니다.

```bash
git status
```

이 명령 하나로:

* 어떤 파일이 수정됐는지
* add 되었는지
* commit 대상인지
* branch 상태가 어떤지

전부 확인할 수 있습니다.

---

## 3. git add . 남발

편해서 자주 쓰지만 위험합니다.

```bash
git add .
```

문제:

원하지 않는 파일까지 들어갈 수 있습니다.

예:

* 테스트 파일
* 로그 파일
* 설정 파일
* .env

추천:

```bash
git add main.py
```

정확히 필요한 파일만 add

---

## 4. .gitignore 안 만들어서 불필요한 파일 업로드

초보자가 매우 자주 겪습니다.

예:

```plaintext
__pycache__/
.env
.vscode/
*.log
```

.gitignore 없으면 이런 파일도 GitHub에 올라갑니다.

최소 기본:

```plaintext
__pycache__/
.env
*.log
```

---

## 5. commit 메시지를 너무 대충 씀

이런 메시지:

```plaintext
수정
업데이트
완료
```

나중에 보면 무엇을 바꿨는지 모릅니다.

좋은 예:

```plaintext
로그인 버튼 클릭 버그 수정
자동 로그인 로직 추가
README 설치 방법 작성
```

---

## 6. main 브랜치에서 바로 계속 작업

초보자는 모든 작업을 main에서 합니다.

하지만 추천 방식:

```bash
git checkout -b feature-login
```

브랜치 분리 후 작업

이유:

문제 생겨도 main 보호 가능

---

## 7. pull 전에 push 해서 충돌 발생

원격 저장소가 먼저 바뀌었으면 push 실패합니다.

오류 예:

```plaintext
failed to push some refs
```

먼저:

```bash
git pull
```

그 다음:

```bash
git push
```

기본 습관:

```plaintext
작업 시작 전 pull
작업 끝난 후 push
```

---

## 8. checkout 과 reset 차이 모름

둘 다 되돌리는 것 같지만 다릅니다.

### checkout

파일 수정 취소

```bash
git checkout -- main.py
```

### reset

stage 취소

```bash
git reset HEAD main.py
```

잘못 쓰면 데이터 날아갑니다.

---

## 9. remote 연결 상태 확인 안 함

GitHub 연결 후 push 안 될 때 많습니다.

확인:

```bash
git remote -v
```

정상 예:

```plaintext
origin https://github.com/아이디/저장소.git
```

---

## 10. commit 너무 늦게 함

초보자는 수정 많이 하고 한 번에 commit 합니다.

문제:

* 추적 어려움
* rollback 어려움
* conflict 증가

좋은 습관:

작게 수정하고 자주 commit

```bash
git commit -m "매수 주문 함수 분리"
```

---

## Git 초보자 추천 습관

항상 이 순서:

```plaintext
→ status
→ pull
→ edit
→ add
→ commit
→ push
```

---

## 진짜 중요한 핵심

Git은 명령어보다:

```plaintext
현재 상태를 이해하는 도구
```

입니다.

그래서:

```bash
git status
```

를 가장 자주 써야 합니다.

---
