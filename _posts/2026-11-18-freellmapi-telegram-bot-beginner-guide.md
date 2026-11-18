---
title: "FreeLLMAPI 텔레그램 연동: Windows 초보자를 위한 개인 AI 봇 만들기"
description: "PC에 설치한 FreeLLMAPI를 텔레그램 봇에 연결합니다. BotFather 봇 생성, Python 실행 환경, 토큰과 통합 키 설정, 내 사용자 ID 등록, 첫 질문과 오류 해결까지 따라 합니다."
date: 2026-11-18 09:58:25 +0900
categories: [Development, AI]
tags: [FreeLLMAPI, Telegram, 텔레그램봇, Python, Windows, API, 생성형AI]
toc: true
toc_sticky: true
image:
  path: /assets/img/2026-11-18-freellmapi-telegram-bot-beginner-guide-handwritten-hero.png
  alt: "휴대폰 텔레그램을 PC의 Python 봇과 FreeLLMAPI에 연결해 개인 AI에게 질문하는 구성"
---

PC에 FreeLLMAPI를 설치했다면, 휴대폰 텔레그램에서도 그 API에 질문을 보낼 수 있다. 집 밖에서 메시지를 보내면 집에 있는 PC가 AI 답변을 받아 텔레그램으로 돌려주는 방식이다.

**필요한 것은 텔레그램 봇 하나와 PC에서 실행할 작은 Python 프로그램이다.** 이 글에서는 Windows PC에 FreeLLMAPI가 설치되어 있다는 전제로, 봇 만들기부터 첫 답변 확인까지 진행한다. 아직 FreeLLMAPI 자체가 준비되지 않았다면 [FreeLLMAPI 설치와 첫 API 호출]({% post_url 2026-11-16-freellmapi-install-and-usage-guide %})부터 확인하자.

예제는 **내 계정의 개인 채팅에서만 AI 요청을 허용**한다. 사진·음성·파일 처리는 포함하지 않으며, 질문마다 독립적으로 답한다. 앞에서 나눈 대화를 기억하거나 PC 파일을 수정하고 명령을 실행하는 기능은 없다.

## 1. 무엇을 연결하는지 먼저 이해하기

![휴대폰 질문이 텔레그램을 거쳐 PC의 Python 봇과 FreeLLMAPI로 전달되고 AI 답변이 돌아오는 흐름](/assets/img/2026-11-18-freellmapi-telegram-bot-beginner-guide-flow.png)
_Python 봇과 FreeLLMAPI는 같은 PC에서 실행한다. 휴대폰은 텔레그램에 접속하면 된다._

역할은 다음과 같다.

| 구성 요소 | 하는 일 |
|---|---|
| 휴대폰 텔레그램 | 질문을 보내고 답변을 읽는 창구 |
| 텔레그램 봇 | 내가 만든 봇 이름으로 메시지를 주고받는 계정 |
| PC의 Python 프로그램 | 봇에게 온 메시지를 받아 FreeLLMAPI에 요청하고 답변을 돌려줌 |
| PC의 FreeLLMAPI | 등록된 제공업체 키와 사용 가능한 모델로 AI 요청을 처리 |

FreeLLMAPI는 OpenAI 호환 API를 제공한다. 이 글의 프로그램은 그 형식의 `/v1/chat/completions`에 요청하며, 모델 이름은 `auto`로 지정한다. 주소와 통합 키 사용법은 [공식 저장소의 API 예제](https://github.com/tashfeenahmed/freellmapi#using-the-api)를 기준으로 한다.

### 집 밖에서 쓰려면 공유기 설정이 필요한가?

이 글에서는 **롱 폴링(long polling)**을 사용한다. PC가 텔레그램 서버에 새 메시지를 요청하고 기다렸다가 받아오는 방식이다. 외부에서 PC로 직접 접속하는 서버를 열지 않으므로, 이 구성을 위해 공유기 포트 포워딩이나 공개 도메인을 마련할 필요가 없다. FreeLLMAPI의 `3001` 포트를 인터넷에 공개할 필요도 없다. [텔레그램 메시지 수신 방식](https://core.telegram.org/bots/api#getupdates)

대신 다음 조건이 필요하다.

- PC가 켜져 있고 인터넷에 연결되어 있어야 한다.
- FreeLLMAPI와 Python 봇이 모두 실행 중이어야 한다.
- PC에서 텔레그램 서버와 사용하는 AI 제공업체에 접속할 수 있어야 한다.

휴대폰과 PC는 같은 와이파이에 있을 필요가 없다. PC가 절전 상태에 들어가거나 인터넷이 끊기면 그동안 새 질문을 처리할 수 없다.

## 2. 준비물과 서로 다른 세 가지 값

먼저 FreeLLMAPI 대시보드의 Playground에서 짧은 질문이 정상 처리되는지 확인한다. 여기서 답변이 안 나온다면 텔레그램을 붙이기 전에 제공업체 키와 모델 설정부터 해결해야 한다.

![봇 토큰은 텔레그램 연결에, 통합 API 키는 FreeLLMAPI 인증에, 사용자 ID는 본인 확인에 사용하는 구분](/assets/img/2026-11-18-freellmapi-telegram-bot-beginner-guide-credentials.png)
_세 값은 발급받는 곳과 사용하는 목적이 다르다._

| 필요한 값 | 어디서 확인하나? | 예제의 설정 이름 |
|---|---|---|
| 텔레그램 봇 토큰 | BotFather가 새 봇을 만들 때 알려 줌 | `TELEGRAM_BOT_TOKEN` |
| FreeLLMAPI 통합 API 키 | FreeLLMAPI의 Keys 화면 또는 앱의 키 복사 기능 | `FREELLMAPI_API_KEY` |
| 내 텔레그램 사용자 ID | 이 글의 프로그램을 실행한 뒤 내 봇에 `/id` 전송 | `ALLOWED_TELEGRAM_USER_ID` |

**Groq나 Google에서 발급받은 제공업체 키를 통합 API 키 자리에 넣지 않는다.** 제공업체 키는 FreeLLMAPI에 등록하고, Python에는 FreeLLMAPI 통합 키를 넣는다.

사용자 ID는 전화번호나 `@사용자이름`, 봇의 ID가 아니다. **봇에 메시지를 보내는 내 계정의 숫자 ID**다. 이 글에서는 별도의 ID 조회 봇을 이용하지 않고 직접 만든 봇에서 확인한다.

토큰과 API 키는 비밀번호처럼 보관한다. 실제 값을 블로그 댓글, 공개 저장소, 화면 캡처에 올리지 않는다. 질문 내용은 텔레그램과 선택된 AI 제공업체를 거치므로 비밀번호 같은 비밀정보를 질문에 넣지 않는다.

## 3. BotFather에서 내 봇 만들기

1. 텔레그램에서 공식 [@BotFather](https://t.me/BotFather)를 연다.
2. **시작**을 누르고 `/newbot`을 보낸다.
3. 봇의 표시 이름을 정한다. 예를 들어 `나의 AI 도우미`처럼 입력한다.
4. 봇의 사용자 이름을 정한다. 일반적인 봇 이름은 `bot`으로 끝나야 한다. 예를 들어 `my_private_ai_demo_bot` 같은 형식이다. 이미 사용 중인 이름이면 다른 이름을 고른다.
5. 생성이 끝나면 BotFather가 알려 주는 **봇 토큰**을 따로 보관한다.
6. 함께 받은 `t.me/...` 링크로 내 봇의 대화창을 열어 둔다.

이 시점에는 봇에게 메시지를 보내도 AI 답변이 오지 않는다. 이름과 토큰만 만든 상태이며, 실제로 메시지를 처리할 Python 프로그램은 아직 실행하지 않았기 때문이다. 토큰 발급 절차와 보관 원칙은 [텔레그램 공식 입문 안내](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)에서 확인할 수 있다.

기존에 다른 서비스에 연결한 봇 대신, 이번 실습용 봇을 새로 만들면 중복 실행이나 웹훅 설정 충돌을 줄일 수 있다.

## 4. Windows에서 Python 준비하기

### Python이 설치되어 있는지 확인

Windows 시작 메뉴에서 **PowerShell**을 열고 다음 명령을 입력한다. 코드 블록 안의 명령만 복사하면 된다.

```powershell
py --version
```

`Python 3.12.x`처럼 버전이 나오면 실행기를 사용할 수 있다. 예제 문법은 Python 3.10 이상을 기준으로 한다. 설치되어 있지 않다면 [Python 공식 Windows 다운로드](https://www.python.org/downloads/windows/)에서 지원 중인 Python 3 버전을 설치하고, PowerShell 창을 새로 열어 다시 확인한다.

`py`는 안 되지만 `python --version`이 된다면, 아래에서 `py -m venv` 명령의 `py`만 `python`으로 바꾸면 된다.

### 작업 폴더와 가상환경 만들기

다음 명령은 내 사용자 폴더 아래에 `freellmapi-telegram` 폴더를 만든다. 이미 같은 이름의 프로젝트가 있다면 새 이름을 사용한다.

```powershell
$botFolder = Join-Path $env:USERPROFILE 'freellmapi-telegram'
New-Item -ItemType Directory -Path $botFolder -Force | Out-Null
Set-Location -LiteralPath $botFolder
py -m venv .venv
```

**가상환경**은 이 봇에 필요한 Python 패키지를 따로 설치하는 폴더다. 이 글에서는 가상환경을 활성화하는 대신 `.venv` 안의 Python을 직접 실행한다. 따라서 `Activate.ps1` 실행 정책을 변경할 필요가 없다.

## 5. 예제 파일 받기와 패키지 설치

[예제 ZIP 내려받기](/assets/code/freellmapi-telegram-bot/freellmapi-telegram-bot.zip)

ZIP을 풀고 다음 세 파일을 방금 만든 `freellmapi-telegram` 폴더로 옮긴다. ZIP 안의 파일을 직접 실행하지 말고 압축을 해제한다.

- `telegram_bot.py`: 메시지를 처리하는 프로그램
- `requirements.txt`: 설치할 패키지 목록
- `settings.env.example`: 설정 파일의 빈 양식

ZIP에는 `.env`와 가상환경을 Git에 올리지 않도록 하는 `.gitignore`도 들어 있다. Windows의 숨김 파일 표시 설정에 따라 보이는 모양은 다를 수 있다.

최종 폴더 구조는 다음과 같다.

```text
freellmapi-telegram/
├─ .venv/
├─ telegram_bot.py
├─ requirements.txt
├─ settings.env.example
└─ .gitignore
```

PowerShell이 이 폴더를 가리키는 상태에서 필요한 패키지를 설치한다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt`의 내용은 다음과 같다. 예제는 `python-telegram-bot` 22.8 이상, 23 미만을 대상으로 한다. 이름이 비슷한 `telegram` 패키지를 별도로 설치하지 않는다.

```text
python-telegram-bot>=22.8,<23.0
httpx>=0.28,<0.29
python-dotenv>=1.0,<2.0
```

`python-telegram-bot`은 텔레그램 메시지 수신과 전송을 담당하고, `httpx`는 FreeLLMAPI에 요청을 보낸다. `python-dotenv`는 별도 설정 파일을 읽는다. [텔레그램 라이브러리 기본 예제](https://docs.python-telegram-bot.org/en/stable/examples.echobot.html), [HTTPX 비동기 요청](https://www.python-httpx.org/async/), [python-dotenv 안내](https://bbc2.github.io/python-dotenv/)

## 6. .env 파일에 주소와 키 입력하기

같은 PowerShell 창에서 양식을 복사하고 메모장으로 연다. 이미 `.env`가 있다면 복사 명령은 실행하지 않고 기존 파일을 연다.

```powershell
Copy-Item -LiteralPath settings.env.example -Destination .env
notepad .env
```

내용을 다음처럼 채우고 저장한다. `PASTE_...` 부분을 실제 값으로 바꾸며, 마지막 사용자 ID는 **첫 실행에서는 비워 둔다.**

```dotenv
TELEGRAM_BOT_TOKEN=PASTE_YOUR_BOT_TOKEN_HERE
FREELLMAPI_BASE_URL=http://127.0.0.1:3001/v1
FREELLMAPI_API_KEY=PASTE_YOUR_UNIFIED_KEY_HERE
FREELLMAPI_MODEL=auto
ALLOWED_TELEGRAM_USER_ID=
```

| 항목 | 입력 방법 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather가 발급한 토큰 전체 |
| `FREELLMAPI_BASE_URL` | 기본값 그대로 사용. 앱의 포트를 바꿨다면 `3001`을 해당 값으로 변경 |
| `FREELLMAPI_API_KEY` | FreeLLMAPI에서 복사한 통합 키 전체 |
| `FREELLMAPI_MODEL` | 처음에는 `auto` 그대로 사용 |
| `ALLOWED_TELEGRAM_USER_ID` | 첫 실행 후 `/id`로 확인해서 입력 |

`127.0.0.1`은 **이 프로그램이 실행되는 PC 자신**을 가리킨다. 휴대폰의 IP나 집의 공인 IP로 바꾸지 않는다. 예제는 Python과 FreeLLMAPI를 같은 Windows PC에서 실행하는 구성이다. Docker를 사용한다면 FreeLLMAPI의 포트가 Windows 쪽에 연결되어 있어야 한다.

주소 끝에는 `/v1`까지만 쓴다. 프로그램이 뒤에 `/chat/completions`를 붙이므로 전체 요청 경로를 중복해서 넣지 않는다.

탐색기의 **보기 → 표시 → 파일 확장명**을 켜서 파일이 `.env.txt`가 아닌 `.env`인지 확인한다. 양식을 복사한 뒤 `notepad .env`로 열면 확장명 실수를 줄일 수 있다. 설정은 프로그램 시작 시 읽으므로 수정 후에는 봇을 재시작한다. 같은 이름의 환경 변수가 이미 설정되어 있다면 그 값이 `.env`보다 우선한다.

## 7. 첫 실행: 내 사용자 ID 등록하기

PowerShell에서 실행한다.

```powershell
.\.venv\Scripts\python.exe telegram_bot.py
```

사용자 ID가 비어 있으면 터미널에 다음 **안내 문구**가 표시된다.

```text
ID 확인 모드: 텔레그램에서 /id를 보내세요. | 종료: Ctrl+C
```

1. 휴대폰에서 **내가 만든 봇**의 개인 대화창을 연다. BotFather 대화창이 아니다.
2. 시작 버튼을 누르거나 `/id`를 보낸다.
3. 봇이 돌려준 `내 사용자 ID: ...`의 숫자를 확인한다.
4. PC의 PowerShell에서 `Ctrl+C`로 프로그램을 종료한다.
5. `notepad .env`로 설정을 열고 마지막 줄에 그 숫자를 넣는다.

예를 들어 숫자가 `123456789`였다면 다음 형태다. 아래 숫자는 설명용이므로 실제로 받은 값으로 바꾼다.

```dotenv
ALLOWED_TELEGRAM_USER_ID=123456789
```

저장하고 다시 실행한다.

```powershell
.\.venv\Scripts\python.exe telegram_bot.py
```

이번에는 터미널에 `AI 질문 모드 | 종료: Ctrl+C`가 표시된다. 이 문구는 **설정 파일을 읽고 실행을 시작했다는 뜻**이며, 실제 AI 요청 성공 여부는 다음 단계에서 확인한다.

ID가 비어 있을 때는 `/id`와 초기 안내만 제공하고 **아무에게도 AI 요청을 허용하지 않는다.** ID를 넣은 뒤에는 그 사용자와의 개인 대화에서만 일반 질문을 처리한다. `/id`는 누구에게나 자기 자신의 ID만 알려 주며, AI 호출은 하지 않는다.

## 8. 첫 질문을 보내고 결과 확인하기

내 봇에 `/start`를 보내 준비 안내를 확인한 다음, 짧은 질문을 보낸다.

```text
파이썬의 리스트와 튜플 차이를 초보자에게 세 문장으로 설명해 줘.
```

정상적인 처리 순서는 다음과 같다.

1. 봇이 `답변을 준비하고 있습니다.`라고 알린다.
2. PC의 Python 프로그램이 FreeLLMAPI에 요청한다.
3. FreeLLMAPI가 사용 가능한 AI 모델의 응답을 받는다.
4. 봇이 답변을 텔레그램으로 전송한다.

첫 안내 메시지만 왔다면 텔레그램 연결과 사용자 확인은 된 것이다. **AI 연결까지 성공했는지는 실제 답변이 도착했는지로 판단**한다. 필요하면 FreeLLMAPI 대시보드의 요청 기록도 함께 살핀다.

집 밖 연결을 확인하려면 PC를 켜 둔 상태에서 휴대폰 와이파이를 끄고 모바일 데이터로 같은 봇에 새 질문을 보내면 된다. 인터넷 연결이 가능한 환경에서 시험한다.

### 이 예제의 동작 범위

- 질문은 4,000자 이하로 제한한다.
- AI 요청에는 매번 현재 질문만 담는다. `방금 답을 더 짧게 해 줘`처럼 앞 대화를 전제로 한 질문은 의도대로 처리되지 않을 수 있다.
- 출력은 `max_tokens=768`로 제한하므로 긴 답변은 중간에서 끝날 수 있다. 짧게 답하도록 질문하는 편이 좋다.
- 긴 답변은 1,500자씩 나누어 일반 텍스트로 전송한다. Markdown 서식을 해석하지 않아 코드 기호도 그대로 보인다.
- 시작할 때 이전에 대기 중이던 메시지는 버린다. 프로그램을 켠 다음 새 질문을 보낸다.
- 기본 설정으로 요청을 하나씩 처리한다. 답변을 기다리는 동안 질문을 연달아 많이 보내지 않는다.

메시지 분할은 [텔레그램 `sendMessage` 길이 제한](https://core.telegram.org/bots/api#sendmessage)을 고려한 것이다. 이전 메시지를 버리는 설정은 라이브러리의 [`drop_pending_updates`](https://docs.python-telegram-bot.org/en/stable/telegram.ext.application.html#telegram.ext.Application.run_polling)를 사용한다. 실제 계정이나 사용자 PC에서 봇을 대신 만들거나 실행한 결과를 제시하는 글은 아니며, 검증 범위는 아래에 따로 적었다.

## 9. 코드에서 꼭 알아둘 부분

전체 코드를 처음부터 직접 작성할 필요는 없다. [Python 파일](/assets/code/freellmapi-telegram-bot/telegram_bot.py)을 열면 다음 두 지점이 핵심이다.

### 내 계정인지 먼저 확인한다

```python
def authorized(update, config):
    return bool(
        config["owner"]
        and update.effective_chat
        and update.effective_chat.type == "private"
        and update.effective_user
        and update.effective_user.id == config["owner"]
    )
```

일반 질문을 처리하기 전에 이 함수를 호출한다. 설정한 숫자 ID와 발신자 ID가 일치하고, 개인 대화일 때만 FreeLLMAPI에 요청한다. 봇 사용자 이름을 다른 사람이 알더라도 이 예제의 AI 호출을 사용할 수 없게 하는 부분이다.

### FreeLLMAPI로 현재 질문을 보낸다

```python
response = await client.post(
    config["base"] + "/chat/completions",
    headers={"Authorization": "Bearer " + config["key"]},
    json={
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "한국어로 이해하기 쉽게 답하세요."},
            {"role": "user", "content": text},
        ],
        "max_tokens": 768,
        "stream": False,
    },
)
```

`model`은 `.env`의 `auto` 값을 사용한다. 특정 모델을 쓰려면 대시보드에서 사용 가능한 **정확한 모델 ID**를 확인한 뒤 `FREELLMAPI_MODEL`을 바꾸고 재시작한다. 모델 목록이나 무료 한도는 바뀔 수 있으므로 예전 모델 이름을 그대로 복사하지 않는 편이 좋다.

전체 파일에는 연결·응답 시간 제한, HTTP 오류 처리와 메시지 분할도 들어 있다. 로컬 FreeLLMAPI 요청은 환경의 프록시 설정을 사용하지 않도록 구성했다. [HTTPX 시간 제한 문서](https://www.python-httpx.org/advanced/timeouts/)

## 10. 자주 막히는 지점

| 증상 | 먼저 확인할 것 |
|---|---|
| `py`를 찾을 수 없음 | Python 설치 후 PowerShell을 새로 열고 확인. `python --version`도 확인 |
| `No module named telegram` | `.venv` 안의 Python으로 `pip install -r requirements.txt`를 실행했는지 확인 |
| 설정 오류가 나오며 종료 | `.env` 위치·확장명, 봇 토큰, 통합 키, 숫자 사용자 ID 확인 |
| `/id`에도 답이 없음 | 봇 실행 상태, BotFather가 아닌 내 봇의 대화창인지, 토큰과 인터넷 연결 확인 |
| `/id`는 되지만 일반 질문에 무응답 | ID가 비어 있는지, 내 사용자 ID를 넣었는지, 수정 뒤 재시작했는지 확인 |
| 준비 메시지 뒤 연결 실패 | FreeLLMAPI 실행 상태와 `127.0.0.1:3001`, `/v1` 주소 확인 |
| FreeLLMAPI HTTP 401·403 | 통합 키를 다시 확인. 제공업체 오류일 수도 있으므로 대시보드 기록도 확인 |
| FreeLLMAPI HTTP 404 | 주소 중복, 포트, 모델 ID와 설치 버전의 API 경로 확인 |
| FreeLLMAPI HTTP 429·5xx | 제공업체 한도·장애, 등록된 키 상태와 사용 가능한 모델 확인 |
| 응답 시간 초과 | Playground에서 같은 질문을 시험하고 더 짧은 질문이나 다른 모델 사용 |
| `Conflict` 오류 | 같은 봇 토큰으로 실행 중인 다른 프로그램을 종료하고 한 개만 실행 |
| PC를 켜 두었는데 밖에서 답이 안 옴 | PC 절전, Python 종료, FreeLLMAPI 종료, 네트워크 제한 여부 확인 |

봇 토큰이 틀리면 `InvalidToken` 같은 시작 오류가 날 수 있다. 토큰은 봇 이름이나 `t.me` 주소가 아니라 BotFather가 발급한 문자열 전체다.

롱 폴링과 웹훅은 동시에 사용할 수 없다. 이 예제의 `run_polling()`은 시작 과정에서 기존 웹훅을 제거하므로, **다른 서비스가 사용하는 봇을 가져오면 그 연동이 중단될 수 있다.** 실습용 새 봇을 권하는 이유다. [라이브러리의 시작·종료 순서](https://docs.python-telegram-bot.org/en/stable/telegram.ext.application.html#telegram.ext.Application.run_polling)

토큰을 공개했다면 BotFather에서 해당 봇의 토큰을 폐기·재발급하고 `.env`도 교체한다. FreeLLMAPI 통합 키를 공개한 경우에도 해당 키를 교체한다. 오류를 다른 사람에게 보여 줄 때는 토큰과 키를 지운다.

## 11. 다음 날 다시 실행하는 방법

패키지 설치와 봇 생성은 매번 할 필요가 없다. FreeLLMAPI를 실행한 뒤 PowerShell에서 작업 폴더로 이동해 프로그램을 켜면 된다.

```powershell
Set-Location -LiteralPath (Join-Path $env:USERPROFILE 'freellmapi-telegram')
.\.venv\Scripts\python.exe telegram_bot.py
```

PowerShell 창을 닫거나 `Ctrl+C`를 누르면 봇은 종료된다. 처음에는 이 수동 방식으로 충분히 동작을 확인한 뒤, 필요할 때 Windows 작업 스케줄러나 상시 실행 서버를 검토하면 된다. 여기서는 시작 프로그램 등록이나 PC의 절전 설정을 자동으로 변경하지 않는다.

무료 모델을 사용하더라도 제공업체별 이용 조건과 호출 한도는 적용된다. PC를 계속 켜 두는 전력 사용도 고려해야 한다.

## 예제 파일과 검증 범위

- [한 번에 받기: 예제 ZIP](/assets/code/freellmapi-telegram-bot/freellmapi-telegram-bot.zip)
- [전체 Python 코드](/assets/code/freellmapi-telegram-bot/telegram_bot.py)
- [패키지 목록](/assets/code/freellmapi-telegram-bot/requirements.txt)
- [설정 양식](/assets/code/freellmapi-telegram-bot/settings.env.example)

이 글은 2026년 11월 18일 확인한 공식 자료를 바탕으로 작성했다. 예제의 문법·의존성 호환성과 가상 응답을 이용한 사용자 제한·API 요청·오류 처리를 로컬에서 확인했다. 실제 텔레그램 계정의 토큰이나 AI 제공업체 키를 사용한 종단 간 통신 시험은 수행하지 않았다. 독자는 7~8단계에서 본인의 계정과 PC로 실제 수신·추론·답변을 확인해야 한다.
