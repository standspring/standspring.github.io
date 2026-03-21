---
title: "Git local 브랜치와 remote 브랜치 차이 완전 정리: 예시로 이해하는 브랜치 동작 방식"
date: 2026-03-22
categories: [Git, GitHub]
tags: [git, github, branch, remote-branch, local-branch, git-push, git-pull, git-beginner]
description: "Git에서 local 브랜치와 remote 브랜치가 무엇이 다른지, origin/main과 main은 어떻게 다른지, push·pull·fetch 시 어떤 일이 일어나는지 예시와 함께 상세히 설명합니다."
slug: git-local-branch-vs-remote-branch
---

Git을 공부하다 보면 이런 표현을 자주 보게 됩니다.

- `main`
- `feature/login`
- `origin/main`
- `origin/feature/login`

처음 보면 다 비슷해 보이는데, 실제로는 의미가 꽤 다릅니다.

특히 초보자는 아래에서 많이 헷갈립니다.

- **local 브랜치와 remote 브랜치 차이**
- `main` 과 `origin/main` 차이
- `push` 하면 정확히 무엇이 올라가는지
- `pull` 하면 왜 브랜치가 맞춰지는지
- 브랜치를 만들었는데 왜 GitHub에 안 보이는지

이번 글에서는 이 부분을 **예시 중심으로** 자세히 정리합니다.

---

## 먼저 결론부터: local 브랜치와 remote 브랜치

가장 짧게 요약하면 이렇습니다.

### local 브랜치

내 PC 안에 있는 브랜치

예:

```bash
main
feature/login
feature/payment
````

내가 직접 만들고, 내 컴퓨터에서 작업하고, commit 하는 대상입니다.

### remote 브랜치

원격 저장소(GitHub 등)에 있는 브랜치

예:

```bash
origin/main
origin/feature/login
```

인터넷 상의 저장소 상태를 가리키는 브랜치입니다.

---

## 아주 쉬운 비유

이렇게 생각하면 이해가 쉽습니다.

* **local 브랜치** = 내 노트북 안의 작업본
* **remote 브랜치** = GitHub에 올라가 있는 온라인 작업본

즉,

```plaintext
local = 내 컴퓨터 기준
remote = GitHub 기준
```

입니다.

---

## 왜 둘을 나눠서 관리할까?

Git은 원래 **분산 버전 관리 시스템**입니다.

즉, 작업을 꼭 인터넷에 연결된 상태에서만 하는 것이 아니라
**각자 자기 컴퓨터에서 독립적으로 작업**할 수 있게 설계되어 있습니다.

그래서:

* 내 컴퓨터 안의 브랜치 상태
* GitHub에 올라간 브랜치 상태

를 따로 관리합니다.

이 둘이 항상 자동으로 같아지는 것은 아닙니다.

---

## 예시 1: 가장 기본적인 상황

내 프로젝트에 현재 이런 브랜치가 있다고 해봅시다.

### local 브랜치 목록

```bash
git branch
```

출력:

```plaintext
* main
  feature/login
```

### remote 브랜치 목록

```bash
git branch -r
```

출력:

```plaintext
origin/main
```

이 상황은 무슨 뜻일까요?

#### 의미

* 내 컴퓨터에는 `main`, `feature/login` 브랜치가 있음
* GitHub에는 아직 `main`만 있음
* `feature/login`은 **로컬에만 존재**
* 아직 GitHub에는 올라가지 않음

즉, 브랜치를 로컬에서 만들었다고 해서
자동으로 remote에 생기지는 않습니다.

---

## local 브랜치를 만들면 왜 GitHub에 바로 안 보일까?

예를 들어 내가 이렇게 실행했다고 합시다.

```bash
git switch -c feature/login
```

이 명령은

```plaintext
내 컴퓨터 안에서만
feature/login 브랜치를 만든 것
```

입니다.

아직 GitHub에는 아무 변화가 없습니다.

그래서 GitHub 사이트에 들어가도 안 보입니다.

GitHub에 브랜치를 보이게 하려면 `push` 해야 합니다.

```bash
git push -u origin feature/login
```

이제 remote에도 `feature/login`이 생깁니다.

---

## `main` 과 `origin/main`은 왜 다른가?

이건 정말 중요합니다.

### `main`

내 로컬 컴퓨터 안의 `main` 브랜치

### `origin/main`

원격 저장소 `origin`에 있는 `main` 브랜치를 Git이 로컬에 기록해 둔 참조 정보

쉽게 말해:

```plaintext
main = 내가 현재 로컬에서 작업하는 main
origin/main = GitHub 쪽 main이 마지막으로 확인된 상태
```

입니다.

---

## `origin`은 무엇인가?

보통 GitHub 저장소를 연결하면 원격 저장소 이름이 `origin`으로 등록됩니다.

확인:

```bash
git remote -v
```

예:

```plaintext
origin  https://github.com/username/my-project.git (fetch)
origin  https://github.com/username/my-project.git (push)
```

즉 `origin/main`은

```plaintext
origin 이라는 원격 저장소의 main 브랜치
```

를 뜻합니다.

---

## 예시 2: local main과 origin/main이 서로 다른 경우

다음 상황을 보겠습니다.

### 현재 상태

내 로컬 `main`은 commit이 하나 더 있음.

```plaintext
local main:        A --- B --- C
origin/main:       A --- B
```

이 뜻은:

* 내 컴퓨터의 `main`은 `C`까지 작업됨
* GitHub의 `main`은 아직 `B`까지만 반영됨

즉, 내가 로컬에서 commit 했지만 아직 push 안 한 상태입니다.

이때 `git status`를 보면 이런 식으로 나올 수 있습니다.

```plaintext
Your branch is ahead of 'origin/main' by 1 commit.
```

의미:

```plaintext
내 local 브랜치가 remote보다 1 commit 앞서 있다
```

이 상태에서는 `git push` 하면 됩니다.

---

## 예시 3: 반대로 remote가 더 앞선 경우

이번에는 다른 PC나 협업자가 먼저 GitHub에 push 했다고 가정해봅시다.

```plaintext
local main:        A --- B
origin/main:       A --- B --- C
```

이 뜻은:

* GitHub에는 `C`까지 올라감
* 내 컴퓨터는 아직 그걸 반영하지 못함

이 상태에서는 `git status`에 이런 느낌의 메시지가 보일 수 있습니다.

```plaintext
Your branch is behind 'origin/main' by 1 commit.
```

이때는 보통:

```bash
git pull
```

또는 먼저 상태만 업데이트하려면:

```bash
git fetch
```

를 사용합니다.

---

## `fetch`와 `pull`이 여기서 왜 중요한가?

local 브랜치와 remote 브랜치 차이를 이해하려면
`fetch`와 `pull` 차이도 알아야 합니다.

### `git fetch`

원격 저장소 상태를 가져와서
`origin/main`, `origin/feature/login` 같은 **remote 추적 정보만 업데이트**합니다.

즉:

* 내 작업 파일은 안 바뀜
* 내 local 브랜치도 자동 병합 안 됨
* 대신 remote 상태를 최신으로 알게 됨

### `git pull`

보통은:

```plaintext
fetch + merge
```

입니다.

즉:

* 원격 상태를 가져오고
* 그 내용을 현재 local 브랜치에 반영

합니다.

---

## 예시 4: fetch를 하면 무슨 일이 생기나?

현재 내 상태:

```plaintext
local main:        A --- B
origin/main:       A --- B
```

그런데 누군가 GitHub에 `C`를 push 했습니다.

아직 내 컴퓨터는 그 사실을 모릅니다.

이때:

```bash
git fetch
```

를 하면 상태가 이렇게 됩니다.

```plaintext
local main:        A --- B
origin/main:       A --- B --- C
```

핵심은 이것입니다.

* `origin/main`은 최신 상태로 갱신됨
* 하지만 내 `main`은 그대로임

즉, fetch는 **remote 상태만 최신화**합니다.

그 다음 차이를 확인할 수 있습니다.

```bash
git log main..origin/main --oneline
```

그러면 원격에만 있는 commit을 볼 수 있습니다.

---

## 예시 5: pull을 하면 무슨 일이 생기나?

같은 상황에서:

```bash
git pull
```

을 하면 보통 이렇게 됩니다.

```plaintext
local main:        A --- B --- C
origin/main:       A --- B --- C
```

즉:

* 원격 상태를 가져오고
* 현재 local 브랜치에도 합침

그래서 local과 remote가 다시 맞춰집니다.

---

## remote 브랜치는 실제로 로컬에도 존재하나?

엄밀하게 말하면 Git은 원격 브랜치 정보를
로컬 저장소 안에 **참조 정보 형태**로 들고 있습니다.

그래서 `origin/main` 같은 이름을 로컬에서 볼 수 있습니다.

하지만 이것은 일반 local 브랜치처럼
내가 직접 checkout 해서 자유롭게 commit 하는 대상은 아닙니다.

즉:

* `main` = 내가 작업하는 브랜치
* `origin/main` = 원격 브랜치의 상태를 추적하는 정보

라고 보면 됩니다.

---

## 예시 6: remote 브랜치에서 local 브랜치 만들기

GitHub에만 있는 브랜치를 가져와서
내 로컬 작업 브랜치로 만들 수도 있습니다.

예를 들어 원격에 `feature/chat` 브랜치가 있다고 합시다.

```bash
git branch -r
```

출력:

```plaintext
origin/main
origin/feature/chat
```

그런데 local에는 아직 없습니다.

이때:

```bash
git switch -c feature/chat origin/feature/chat
```

또는 상황에 따라 더 간단히:

```bash
git switch feature/chat
```

를 하면
remote 브랜치를 기반으로 local 브랜치를 만들고 연결할 수 있습니다.

이제부터는 내 local `feature/chat`에서 작업할 수 있습니다.

---

## tracking branch란 무엇인가?

local 브랜치와 remote 브랜치가 연결된 관계를
보통 **tracking** 이라고 부릅니다.

예를 들어:

* local 브랜치: `main`
* 추적 대상 remote 브랜치: `origin/main`

이렇게 연결되어 있으면 `git status`가 비교를 해주고,
`git pull`, `git push`도 더 편해집니다.

확인:

```bash
git branch -vv
```

예:

```plaintext
* main           a1b2c3d [origin/main] update README
  feature/login  e4f5g6h [origin/feature/login] login UI added
```

이 뜻은:

* `main`은 `origin/main`을 추적
* `feature/login`은 `origin/feature/login`을 추적

하고 있다는 의미입니다.

---

## `git push -u origin feature/login`에서 `-u`는 왜 쓰나?

이 명령을 많이 보게 됩니다.

```bash
git push -u origin feature/login
```

여기서 `-u`는
이 local 브랜치가 앞으로 어떤 remote 브랜치를 기본 추적할지 설정합니다.

즉 처음 한 번 이렇게 해두면, 다음부터는 보통:

```bash
git push
git pull
```

만으로도 연결된 remote 브랜치를 기준으로 동작합니다.

초보자 입장에서는 거의 이렇게 기억하면 됩니다.

```plaintext
새 브랜치를 처음 원격에 올릴 때는 -u 붙이기
```

---

## 예시 7: local 브랜치 이름과 remote 브랜치 이름이 꼭 같아야 하나?

꼭 같을 필요는 없습니다.

예를 들어:

```bash
git push origin feature/login:feature/login-v2
```

이렇게 하면

* local 브랜치 이름은 `feature/login`
* remote 브랜치 이름은 `feature/login-v2`

가 됩니다.

하지만 초보자라면 헷갈리기 쉬우므로
보통은 같은 이름을 쓰는 것이 좋습니다.

---

## 브랜치를 삭제할 때도 local과 remote가 다르다

이 부분도 자주 헷갈립니다.

### local 브랜치 삭제

```bash
git branch -d feature/login
```

이건 내 컴퓨터에서만 삭제됩니다.

### remote 브랜치 삭제

```bash
git push origin --delete feature/login
```

이건 GitHub에서 삭제됩니다.

즉, 둘은 별개입니다.

local에서 지웠다고 GitHub에서 자동 삭제되지 않고,
GitHub에서 지웠다고 local에서 자동 삭제되지도 않습니다.

---

## 예시 8: local에는 있는데 remote에는 없는 브랜치

상황:

```plaintext
local:
  main
  feature/login

remote:
  origin/main
```

의미:

* `feature/login`은 아직 내 PC에만 있음
* 협업자는 이 브랜치를 볼 수 없음
* GitHub에서도 Pull Request를 만들 수 없음

해결:

```bash
git push -u origin feature/login
```

---

## 예시 9: remote에는 있는데 local에는 없는 브랜치

상황:

```plaintext
local:
  main

remote:
  origin/main
  origin/feature/payment
```

의미:

* 누군가 GitHub에 `feature/payment`를 올려둠
* 내 컴퓨터에는 아직 작업 브랜치가 없음

해결:

```bash
git switch -c feature/payment origin/feature/payment
```

이제 local에서도 그 브랜치로 작업 가능합니다.

---

## 예시 10: 협업에서 가장 많이 보는 흐름

실제 협업에서 자주 있는 흐름입니다.

### 1단계: 내가 local 브랜치 생성

```bash
git switch main
git pull
git switch -c feature/login
```

### 2단계: 내 local 브랜치에서 작업

```bash
git add .
git commit -m "로그인 기능 추가"
```

현재 상태:

```plaintext
local:
  main
  feature/login

remote:
  origin/main
```

아직 GitHub에는 `feature/login`이 없음

### 3단계: remote에 브랜치 업로드

```bash
git push -u origin feature/login
```

현재 상태:

```plaintext
local:
  main
  feature/login

remote:
  origin/main
  origin/feature/login
```

### 4단계: GitHub에서 Pull Request 생성

이제 GitHub에서
`feature/login` → `main` 으로 PR 생성 가능

### 5단계: merge 후 브랜치 정리

merge 완료 후:

* remote 브랜치 삭제 가능
* local 브랜치도 삭제 가능

```bash
git branch -d feature/login
git push origin --delete feature/login
```

---

## `git branch`, `git branch -r`, `git branch -a` 차이

이 세 개는 꼭 구분해야 합니다.

### local 브랜치만 보기

```bash
git branch
```

### remote 브랜치만 보기

```bash
git branch -r
```

### 둘 다 보기

```bash
git branch -a
```

예시:

```plaintext
* main
  feature/login
  remotes/origin/main
  remotes/origin/feature/login
```

여기서:

* `main`, `feature/login` = local
* `remotes/origin/...` = remote 추적 정보

입니다.

---

## 초보자가 가장 많이 헷갈리는 포인트

### 1. 브랜치 만들면 GitHub에도 생긴다고 생각함

아닙니다.
local에서 만든 것일 뿐입니다.

`push` 해야 remote에 생깁니다.

### 2. `main` 과 `origin/main`이 같은 것이라고 생각함

비슷하지만 다릅니다.

* `main` = 내 작업 브랜치
* `origin/main` = 원격 상태를 추적하는 정보

### 3. remote 브랜치를 바로 수정한다고 생각함

실제로는 local 브랜치에서 작업하고,
그 결과를 push 해서 remote를 갱신합니다.

### 4. local 삭제와 remote 삭제를 같은 것으로 생각함

서로 완전히 별개입니다.

---

## local 브랜치와 remote 브랜치 관계를 한 문장으로 정리

아래 한 줄로 기억하면 됩니다.

```plaintext
local 브랜치에서 작업하고, push로 remote 브랜치에 반영하며, pull/fetch로 remote 상태를 다시 가져온다
```

---

## 초보자 기준 추천 실전 흐름

기능 개발 시작할 때:

```bash
git switch main
git pull
git switch -c feature/login
```

작업 후:

```bash
git add .
git commit -m "로그인 기능 추가"
git push -u origin feature/login
```

main 반영 전:

```bash
git switch main
git pull
```

필요 시 merge 또는 PR 진행

---

## 정리

Git에서 local 브랜치와 remote 브랜치는 이름이 비슷해서 헷갈리지만, 역할이 다릅니다.

### local 브랜치

* 내 컴퓨터에서 직접 작업
* commit 수행
* 실제 수정 대상

### remote 브랜치

* GitHub 같은 원격 저장소 상태
* 공유용 기준점
* 협업과 백업의 기준

핵심은 이것입니다.

```plaintext
작업은 local에서 하고
공유는 remote로 한다
```

이 개념만 정확히 잡으면
`push`, `pull`, `fetch`, `origin/main` 같은 표현이 훨씬 자연스럽게 이해됩니다.

---

## FAQ

### local 브랜치를 만들었는데 GitHub에 왜 안 보이나?

local에서만 만든 상태이기 때문입니다.

```bash
git push -u origin 브랜치명
```

으로 올려야 GitHub에 보입니다.

### origin/main은 실제 브랜치인가?

원격 브랜치 자체라기보다,
원격 브랜치 상태를 로컬에서 추적하는 참조 정보라고 이해하면 가장 쉽습니다.

### remote 브랜치에서 바로 commit 할 수 있나?

보통은 local 브랜치에서 작업하고 commit 한 뒤 push 합니다.

### fetch만 하고 pull 안 하면 어떻게 되나?

원격 상태 정보만 최신으로 갱신되고,
내 현재 local 브랜치 파일 내용은 바로 바뀌지 않습니다.

---
