---
title: "Git 브랜치(branch) 완전 이해하기: 초보자도 헷갈리지 않게 상세 설명"
date: 2026-03-16 00:00:00 +0900
categories: github
tags: [github, branch, git, git-branch, git-merge, git-beginner, vscode-git]
toc: true
toc_sticky: true
---

Git을 배우다 보면 가장 많이 듣는 말 중 하나가 **브랜치(branch)** 입니다.

처음에는 어렵게 느껴지지만, 브랜치 개념만 제대로 이해하면 Git이 훨씬 쉬워집니다.

이번 글에서는 Git 브랜치를 **왜 쓰는지**, **어떻게 만드는지**, **언제 써야 하는지**, **merge는 무엇인지**, **초보자가 자주 하는 실수는 무엇인지**까지 한 번에 정리합니다.

---

## 브랜치란 무엇인가?

브랜치는 말 그대로 **가지**입니다.

하나의 프로젝트에서 작업 흐름을 여러 갈래로 나누어 작업할 수 있게 해주는 기능입니다.

쉽게 말하면:

```plaintext
메인 코드는 그대로 두고
별도의 작업 공간에서 새로운 기능을 만들거나
실험하거나
버그를 수정할 수 있는 기능
```

입니다.

---

## 브랜치가 왜 필요할까?

브랜치를 모르면 보통 모든 작업을 `main`에서 바로 하게 됩니다.

하지만 이렇게 하면 문제가 생깁니다.

예를 들어:

* 로그인 기능을 추가하다가 오류가 생김
* 실험 코드가 main에 섞여 들어감
* 작업 도중 배포 가능한 안정 버전이 사라짐

브랜치를 쓰면 이런 문제를 줄일 수 있습니다.

즉:

```plaintext
안정적인 코드와
실험 중인 코드를
분리하는 도구
```

라고 보면 됩니다.

---

## 가장 쉬운 비유로 이해하기

현재 프로젝트가 책 한 권이라고 생각해 봅시다.

* `main` 브랜치 = 정식 원고
* `feature-login` 브랜치 = 로그인 기능을 수정하는 초안
* `fix-bug` 브랜치 = 버그만 고치는 별도 작업본

즉, 브랜치는 **원본을 건드리지 않고 복사본에서 작업하는 방식**에 가깝습니다.

---

## Git 브랜치의 핵심 장점

### 1. main 보호

안정적인 브랜치를 유지할 수 있습니다.

### 2. 기능별 분리

기능 추가, 버그 수정, 실험 작업을 나눌 수 있습니다.

### 3. 협업에 유리

여러 사람이 각자 다른 브랜치에서 작업할 수 있습니다.

### 4. 문제 발생 시 복구 쉬움

브랜치 단위로 작업을 되돌리거나 비교하기 쉽습니다.

---

## 기본 브랜치 이름: main

예전에는 기본 브랜치 이름으로 `master`를 많이 사용했지만,
지금은 보통 `main`을 사용합니다.

현재 브랜치 확인:

```bash
git branch
```

예:

```plaintext
* main
```

별표(`*`)는 **현재 내가 작업 중인 브랜치**를 뜻합니다.

---

## 브랜치 확인하기

현재 브랜치 목록 보기:

```bash
git branch
```

원격 브랜치까지 보기:

```bash
git branch -a
```

예:

```plaintext
* main
  feature-login
  remotes/origin/main
  remotes/origin/feature-login
```

---

## 브랜치 만들기

새 브랜치 생성:

```bash
git branch feature-login
```

이 명령은 브랜치만 만들고, 아직 이동하지는 않습니다.

---

## 브랜치 이동하기

브랜치 이동:

```bash
git checkout feature-login
```

이제 `feature-login` 브랜치에서 작업하게 됩니다.

---

## 브랜치 생성과 이동을 한 번에 하기

가장 많이 쓰는 방식입니다.

```bash
git checkout -b feature-login
```

뜻:

```plaintext
새 브랜치를 만들고
즉시 그 브랜치로 이동
```

---

## 최신 방식: switch 사용

요즘은 `checkout` 대신 더 명확한 명령도 자주 씁니다.

브랜치 생성 + 이동:

```bash
git switch -c feature-login
```

기존 브랜치로 이동:

```bash
git switch main
```

초보자 입장에서는 `checkout`보다 의미가 더 분명해서 이해하기 쉽습니다.

---

## 브랜치를 만든 뒤 실제로 무엇이 달라지나?

브랜치를 새로 만들면, 현재 시점의 코드 상태를 기준으로 새로운 작업 흐름이 생깁니다.

예를 들어 `main`에서 `feature-login`을 만들면:

```plaintext
main과 feature-login은 처음엔 같은 상태
이후부터 각자 다른 commit 이력을 가질 수 있음
```

즉, 처음엔 같지만 작업을 시작하면 달라집니다.

---

## 브랜치에서 작업하는 기본 흐름

예시:

```bash
git switch -c feature-login
## 코드 수정
git add .
git commit -m "로그인 UI 추가"
```

이 commit은 `feature-login` 브랜치에만 기록됩니다.

`main`에는 아직 반영되지 않습니다.

---

## main으로 돌아가기

```bash
git switch main
```

또는:

```bash
git checkout main
```

이동하면 `main` 기준 파일 상태로 돌아옵니다.

즉, 브랜치마다 작업 내용이 다를 수 있습니다.

---

## merge란 무엇인가?

브랜치에서 작업을 끝낸 뒤, 그 결과를 다른 브랜치에 합치는 것을 **merge(병합)** 라고 합니다.

예를 들어:

* `feature-login`에서 로그인 기능 개발 완료
* 이 작업을 `main`에 반영하고 싶음

이때 merge를 사용합니다.

---

## merge 기본 사용법

먼저 `main`으로 이동:

```bash
git switch main
```

그 다음 feature 브랜치 합치기:

```bash
git merge feature-login
```

뜻:

```plaintext
feature-login에서 작업한 내용을
main에 반영
```

---

## merge는 어느 브랜치에서 해야 하나?

초보자가 가장 많이 헷갈리는 부분입니다.

기준:

```plaintext
합쳐질 대상 브랜치로 먼저 이동한 뒤
거기서 merge 한다
```

즉,

`feature-login`을 `main`에 넣고 싶다면:

```bash
git switch main
git merge feature-login
```

입니다.

---

## merge 후 브랜치는 사라지나?

아니요. merge를 해도 브랜치는 자동 삭제되지 않습니다.

필요하면 직접 삭제해야 합니다.

```bash
git branch -d feature-login
```

강제 삭제:

```bash
git branch -D feature-login
```

주의:

`-D`는 merge 안 된 내용도 강제로 지울 수 있으므로 조심해야 합니다.

---

## 브랜치 이름은 어떻게 짓는 게 좋을까?

초보자도 이름 규칙을 정하면 관리가 훨씬 쉬워집니다.

추천 예시:

```plaintext
feature-login
feature-payment
fix-login-error
hotfix-order-bug
docs-readme
refactor-order-service
```

보통 많이 쓰는 접두어:

* `feature/` : 기능 추가
* `fix/` : 일반 버그 수정
* `hotfix/` : 급한 운영 버그 수정
* `docs/` : 문서 수정
* `refactor/` : 구조 개선

예:

```bash
git switch -c feature/login
```

---

## 브랜치를 언제 만들어야 하나?

다음 상황이면 브랜치를 따는 것이 좋습니다.

### 기능 추가

새 기능 개발

### 버그 수정

기존 기능에 영향 줄 수 있는 수정

### 실험 작업

실패 가능성이 있는 시도

### 문서 수정 분리

코드와 문서 변경을 나누고 싶을 때

초보자 기준으로는:

```plaintext
의미 있는 작업 단위마다 브랜치 하나
```

라고 생각하면 됩니다.

---

## 브랜치를 안 쓰면 생기는 문제

예를 들어 모든 작업을 `main`에서만 하면:

* 기능 A 작업 중인데 버그 수정 B도 섞임
* 중간 상태가 불안정한데 바로 main에 반영됨
* 어떤 commit이 어떤 작업인지 구분 어려움

결국 관리가 어려워집니다.

---

## 협업에서 브랜치가 중요한 이유

협업에서는 거의 필수입니다.

예를 들어:

* A 개발자: `feature-login`
* B 개발자: `feature-payment`
* C 개발자: `fix-header-bug`

각자 분리된 브랜치에서 작업한 뒤,
검토 후 `main`으로 합칩니다.

이 방식이 훨씬 안전합니다.

---

## 원격 브랜치란?

지금까지 설명한 것은 로컬 브랜치 중심입니다.

GitHub 같은 원격 저장소에도 브랜치가 있습니다.

로컬 브랜치를 원격에 올리기:

```bash
git push -u origin feature-login
```

이후부터는:

```bash
git push
```

만으로도 같은 브랜치에 push 되는 경우가 많습니다.

---

## 원격 브랜치 확인하기

```bash
git branch -a
```

또는:

```bash
git branch -r
```

* `-a` : 로컬 + 원격 모두
* `-r` : 원격만

---

## 다른 브랜치 내용을 가져오고 싶을 때

가장 일반적인 방식은 merge입니다.

예:

```bash
git switch main
git merge feature-login
```

또는 현재 브랜치에서 다른 브랜치의 변경사항을 반영할 수도 있습니다.

---

## merge conflict란?

브랜치를 합칠 때 같은 파일의 같은 부분을 서로 다르게 수정하면 **충돌(conflict)** 이 발생할 수 있습니다.

예:

* `main`에서도 `app.py` 수정
* `feature-login`에서도 같은 줄 수정

이 상태에서 merge 하면 Git이 자동으로 어느 쪽이 맞는지 판단하지 못합니다.

이것이 merge conflict입니다.

---

## conflict가 생기면 어떻게 보이나?

파일 안에 이런 표시가 들어갑니다.

```plaintext
<<<<<<< HEAD
main의 내용
=======
feature-login의 내용
>>>>>>> feature-login
```

이때 해야 할 일:

1. 어떤 내용을 남길지 결정
2. 충돌 표시 삭제
3. 파일 저장
4. 다시 add 및 commit

---

## 초보자가 알아두면 좋은 브랜치 명령어 정리

### 현재 브랜치 확인

```bash
git branch
```

### 브랜치 생성

```bash
git branch feature-login
```

### 브랜치 이동

```bash
git switch feature-login
```

### 생성 + 이동

```bash
git switch -c feature-login
```

### 브랜치 병합

```bash
git switch main
git merge feature-login
```

### 브랜치 삭제

```bash
git branch -d feature-login
```

### 원격으로 브랜치 업로드

```bash
git push -u origin feature-login
```

---

## 초보자가 자주 하는 브랜치 실수

### 1. main에서 계속 작업

브랜치 분리 없이 모든 작업 수행

### 2. 브랜치만 만들고 이동 안 함

```bash
git branch feature-login
```

만 하고 아직 `main`에서 작업하는 경우가 많습니다.

### 3. merge 방향 헷갈림

합쳐질 대상 브랜치로 먼저 이동해야 합니다.

### 4. merge 후 브랜치 자동 삭제된다고 착각

직접 삭제해야 합니다.

### 5. 이름을 너무 애매하게 지음

`test1`, `new`, `temp` 같은 이름은 나중에 혼란을 만듭니다.

---

## 초보자에게 추천하는 브랜치 실전 흐름

예를 들어 로그인 기능 추가라면:

```bash
git switch main
git pull
git switch -c feature-login
## 코드 수정
git add .
git commit -m "로그인 기능 추가"
git push -u origin feature-login
```

작업 완료 후:

```bash
git switch main
git pull
git merge feature-login
git push
```

필요 없으면 삭제:

```bash
git branch -d feature-login
```

---

## GitHub에서 Pull Request와 브랜치

협업에서는 보통 브랜치를 push한 뒤,
GitHub에서 **Pull Request(PR)** 를 만들어 `main`에 합칩니다.

즉 흐름은 보통 이렇습니다.

```plaintext
브랜치 생성
→ 작업
→ commit
→ push
→ Pull Request 생성
→ 리뷰
→ merge
```

혼자 작업할 때는 로컬에서 바로 merge 해도 되지만,
협업에서는 PR 방식이 일반적입니다.

---

## 브랜치는 복잡한 기능이 아니라 안전장치다

초보자는 브랜치를 어려운 고급 기능처럼 느끼기 쉽습니다.

하지만 실제로는:

```plaintext
작업을 분리해서
안전하게 관리하기 위한 기본 도구
```

입니다.

오히려 브랜치를 안 쓰는 것이 더 위험합니다.

---

## 정리

Git 브랜치는 다음 한 줄로 기억하면 됩니다.

```plaintext
main은 안정 버전
브랜치는 별도 작업 공간
작업이 끝나면 merge로 합친다
```

이 흐름만 익히면 Git이 훨씬 쉬워집니다.

---
