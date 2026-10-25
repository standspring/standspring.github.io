---
title: "Jev AI 의사결정 모델: LLM과의 차이와 Python 연동 방법"
description: "TypeSafe AI의 Jev가 state와 질문을 받아 Choice·Score·Noul로 판단하는 방식을 알아봅니다. LLM과의 차이, 확률과 confidence의 의미, Python API 예제와 자동 분류 설계 시 주의점을 정리합니다."
date: 2026-10-25 00:00:00 +0900
categories: [Development, AI]
tags: [Jev, TypeSafe, AI, DecisionModel, LLM, Python, Automation]
toc: true
toc_sticky: true
---

# Jev AI 의사결정 모델: LLM과의 차이와 Python 연동 방법

## 들어가며

고객 문의를 담당 팀으로 보내거나, 검색한 문서가 질문과 관련 있는지 판별할 때 필요한 결과는 짧다. `billing`, `technical` 같은 분류 하나면 다음 코드를 실행할 수 있다.

**Jev는 TypeSafe AI가 개발한 의사결정 모델이다. 입력 상태와 정해진 질문을 받아, 프로그램에서 사용할 선택값·점수·확률을 반환한다.** 답변 문장이나 코드를 작성하는 대신 소프트웨어 안의 작은 판단을 담당한다. ([공식 소개](https://docs.typesafe.ai/introduction))

![고객 문의와 질문을 Jev에 전달하고, 구조화된 판단 결과를 애플리케이션의 정책 코드로 보내 자동 분류 또는 검토로 연결하는 그림](/assets/img/2026-10-25-jev-decision-flow.png)

*그림 1. Jev는 판단 결과를 제공하고, 애플리케이션이 실행 조건을 결정한다. 공식 API 개념을 바탕으로 직접 제작한 설명도이며, 제품 화면 캡처나 내부 신경망 구조도가 아니다.*

이 글은 **2026년 10월 25일 확인한 공식 문서**를 기준으로 작성했다. API 키 없이 실행하는 예제와 실제 API를 호출하는 경로를 함께 제공한다. 실제 Jev 추론 결과를 측정한 벤치마크는 아니다.

## 문제 상황

고객 문의 자동 분류를 만든다고 하자.

```text
입력: "이번 달 요금이 두 번 결제됐습니다. 확인 부탁드립니다."
필요한 결과: billing
```

자유 형식의 답변을 요청하면 설명에서 분류값을 추출해야 한다. 구조화 출력 기능을 사용하면 이 형식 문제를 줄일 수 있지만, 다음 문제는 남는다.

- 형식이 올바른 결과도 내용은 틀릴 수 있다.
- 문의가 두 주제를 동시에 다루면 한 팀을 고르기 어렵다.
- 자동 처리해도 되는 경우와 검토가 필요한 경우를 구분해야 한다.
- 모델을 바꿨을 때 이전의 분기 기준이 계속 유효한지 확인해야 한다.

따라서 목표는 JSON 하나를 얻는 데서 끝나지 않는다. **질문과 후보를 정의하고, 불확실한 결과를 처리할 경로까지 만드는 것**이 필요하다.

## 원인 분석

### 1. Jev의 System One은 무엇인가?

TypeSafe는 빠르고 범위가 좁은 판단을 소프트웨어에 제공하는 모델을 **System One**이라고 부른다. 이름은 Daniel Kahneman이 대중화한 빠른 직관적 사고인 System 1에서 가져왔다. 인간의 사고 과정을 그대로 구현했다는 의미로 받아들이면 안 된다. ([System One 개념](https://docs.typesafe.ai/concepts/system-one))

공식 발표는 Jev를 새로운 모델 구조, 병렬 샘플러, **RLCD(Reinforcement Learning for Calibrated Decisions)**라는 학습 방법을 사용하는 모델로 설명한다. RLCD의 목표는 결과와 맞도록 확률을 보정한 판단이다. 다만 이 발표만으로 내부 레이어 구성이나 학습 방법 전체를 재현할 수는 없다. 공개되지 않은 파라미터 수나 구현 세부를 추측해 확정할 필요도 없다. ([Jev 출시 발표](https://typesafe.ai/blog/introducing-system-one-models-and-jev))

### 2. LLM과는 무엇이 다른가?

| 비교 항목 | 일반적인 생성형 LLM 사용 | Jev 사용 |
|---|---|---|
| 대표적인 작업 | 답변·요약·코드 작성, 추론 | 분류·평가·조건 판별 |
| 결과 공간 | 자유로운 텍스트 또는 제한된 구조화 출력 | 질문 유형과 후보로 정의한 값 |
| 설명문 생성 | 가능 | 판단 이유를 설명하는 문장은 생성하지 않음 |
| 불확실성 처리 | 제품·모델에 따라 별도 구성 | 확률, 유형에 따른 confidence 제공 |
| 앱에서의 역할 | 작성기, 추론기, 도구 호출 판단 등 | 좁은 판단을 수행하는 구성 요소 |

LLM도 JSON Schema나 도구 호출로 구조화된 결과를 제공할 수 있다. “LLM은 JSON을 못 만든다”가 차이의 핵심은 아니다. Jev는 **판단 자체를 위한 인터페이스와 학습 목표**를 내세운다. TypeSafe의 성능·속도 우위 주장은 해당 작업과 비교 조건에 한정해서 봐야 한다. 모든 작업에서 모든 LLM보다 우수하다는 뜻은 아니다. ([출시 발표의 비교 설명](https://typesafe.ai/blog/introducing-system-one-models-and-jev))

예를 들어 문의의 담당 팀을 고르는 데 Jev를 사용하고, 답변 초안 작성에는 생성형 LLM을 연결할 수 있다. 정규식으로 정확히 처리할 수 있는 주문번호 형식 검사나 숫자 계산은 일반 코드에 맡기는 편이 명확하다.

### 3. state와 questions를 구분한다

Jev 요청에는 다음 개념이 들어간다.

```text
state      = 판단 대상과 필요한 근거
questions  = 무엇을 판단할지, 어떤 후보·기준을 사용할지
model      = 요청을 처리할 모델 ID 또는 별칭
```

`state`에는 문자열뿐 아니라 JSON 객체나 배열도 전달할 수 있다. 예를 들어 문의 본문과 상품 유형을 넣고, `questions`에 담당 팀과 상담원 연결 요청 여부를 각각 정의한다. 응답의 `answers`에서는 요청에 사용한 질문 ID로 결과를 찾는다. ([HTTP API 명세](https://docs.typesafe.ai/api/system-one))

같은 요청의 여러 질문은 동일한 상태를 대상으로 독립적으로 평가된다. 따라서 두 번째 질문이 첫 번째 질문의 답을 읽는다고 가정하면 안 된다. 앞선 결과가 꼭 필요하다면 코드에서 조합하거나 후속 요청을 만든다. ([공식 소개의 질문 평가 방식](https://docs.typesafe.ai/introduction))

### 4. Choice·Score·Noul의 차이

![Choice는 정해진 후보 중 하나를 선택하고, Score는 순서가 있는 기준으로 점수를 평가하며, Noul은 참일 확률을 반환한다. 네 후보 중 최대 확률 0.85는 confidence 0.80에 해당한다.](/assets/img/2026-10-25-jev-primitives-confidence.png)

*그림 2. 텍스트 판단에 사용하는 세 가지 질문 유형과 Choice confidence 계산 예시. 수치는 설명을 위해 만든 값이다.*

| 유형 | 적합한 질문 | 주요 응답 |
|---|---|---|
| **Choice** | 이 문의는 어느 팀으로 보낼까? | `choice`, `probabilities`, `confidence` |
| **Score** | 이 장애의 심각도는 어느 정도일까? | `score`, `probabilities`, `confidence` |
| **Noul** | 사용자가 상담원 연결을 요청했을까? | `noul` |

**Choice**는 순서가 없는 후보 중 하나를 선택한다. `criteria`는 후보 ID와 설명을 담는 객체다. `billing`, `technical`, `account`, `other`처럼 후보를 정의할 수 있다. 정답이 어느 후보에도 속하지 않을 가능성이 있으면 `other`와 같은 경로가 유용하다. ([Choice 문서](https://docs.typesafe.ai/primitives/choice))

**Score**는 순서가 있는 단계 설명으로 평가한다. 예를 들어 `criteria`가 `경미한 표시 문제`, `우회 가능한 기능 장애`, `우회 불가능한 업무 중단`이라는 세 단계라면, 기준 위치는 0·1·2다. 반환값은 `1.4`처럼 중간값일 수도 있다. 업무가 사용하는 1~5등급과 자동으로 같아지는 것은 아니므로 변환 규칙을 정해야 한다. ([Score 문서](https://docs.typesafe.ai/primitives/score))

**Noul**은 예·아니요 질문에 대해 **예일 확률을 0~1로 반환**한다. `0.97`은 예 쪽에, `0.03`은 아니요 쪽에 가깝고, `0.5` 근처는 불확실하다. 별도의 `confidence` 필드는 없다. 따라서 `noul=0.03`을 “모델이 자신 없어 한다”로 읽으면 안 된다. ([Noul 문서](https://docs.typesafe.ai/primitives/noul))

이 글은 텍스트 판단을 중심으로 설명한다. 문서에는 실험적 이미지 입력과 Box도 별도로 있으므로, 세 유형이 API 전체의 모든 기능이라고 해석하지는 말자. ([이미지 입력 문서](https://docs.typesafe.ai/images))

### 5. probability와 confidence는 같은 값이 아니다

Choice의 `probabilities`는 후보별 확률이고, `confidence`는 그 분포에서 계산한 요약값이다. 공식 문서의 Choice 공식은 다음과 같다.

```text
n = 후보 수
p_max = 선택된 후보의 확률
confidence = (p_max - 1/n) / (1 - 1/n)
```

후보가 네 개이고 확률이 `[0.85, 0.05, 0.05, 0.05]`라면 confidence는 `0.80`이다. `confidence=0.80` 자체를 “이 답이 맞을 확률 80%”라고 읽으면 안 된다. Score는 순서가 있는 단계에 맞춰 다른 계산식을 사용한다. ([Confidence 문서](https://docs.typesafe.ai/confidence))

확률의 **보정(calibration)**은 여러 예측을 모아 확인하는 성질이다. 예를 들어 참일 확률을 0.8로 예측한 사례군의 실제 참 비율이 약 80%인지 살펴본다. 하나의 응답이 반드시 맞는다는 보장은 아니다. ([System One의 보정 설명](https://docs.typesafe.ai/concepts/system-one))

## 해결 방법

### 1. 판단과 실행 정책을 나눈다

이 글의 예제에서는 Jev가 담당 팀과 상담원 연결 요청 여부를 판단한다. 코드는 다음 규칙을 적용한다.

1. 담당 팀이 `other`면 검토로 보낸다.
2. Choice confidence가 `0.80`보다 낮으면 검토로 보낸다.
3. 상담원 연결 요청 확률이 `0.30` 이상이면 검토로 보낸다.
4. 나머지는 선택된 팀으로 자동 분류한다.

여기서 “자동 분류”는 큐 이름을 정하는 단계다. 문의에 대한 답변 작성이나 결제 취소 같은 작업을 수행하지 않는다. `0.80`과 `0.30`은 **분기 동작을 설명하기 위한 예시 기준**이다. 운영 기준은 실제 문의의 오분류율과 자동 분류 비율을 비교해 정해야 한다.

### 2. 넓은 질문을 작은 질문으로 바꾼다

“이 고객을 어떻게 처리해야 하나?”에는 의도 파악, 정책 해석, 권한 검사와 답변 작성이 섞여 있다. 다음처럼 쪼개면 결과를 코드와 연결하기 쉽다.

```text
Choice: 문의의 주요 담당 팀은?
Noul: 상담원 연결을 명시적으로 요청했는가?
Score: 장애가 업무에 미치는 영향은 어느 단계인가?
```

중복 결제 금액이나 날짜 간격은 코드에서 계산하고, 필요한 사실을 상태에 넣는다. 정해진 권한·금액 조건도 코드로 검사한다. TypeSafe 역시 좁은 질문과 코드 조합을 권장한다. ([공식 소개의 질문 분해 설명](https://docs.typesafe.ai/introduction))

### 3. 모델과 비용 기준을 기록한다

확인 시점의 공식 문서에는 `jev-1.14.0`과 `jev-1.13.0`이 안내되어 있으며, `jev-latest`는 `jev-1.14.0`을 가리킨다. 입력 가격은 **100만 토큰당 0.042달러**, 출력 토큰은 무료다. ([모델·가격 문서](https://docs.typesafe.ai/models))

예를 들어 요청의 전체 과금 입력이 평균 1,000토큰이면 10만 건의 입력 비용은 다음과 같다.

```text
100,000건 × 1,000토큰 = 100,000,000토큰
100,000,000 / 1,000,000 × $0.042 = $4.20
```

세금·환율·재시도 비용 등은 제외한 계산이다. 질문과 기준도 입력에 포함되므로 본문 길이만으로 비용을 계산하지 말고, 실제 응답의 `usage`로 확인하자. 별칭은 새 버전으로 이동할 수 있으므로 평가할 때는 모델 ID를 고정하고 응답의 `model`도 기록한다. ([모델 문서의 별칭 설명](https://docs.typesafe.ai/models))

## 예제

### 1. Python 표준 라이브러리로 호출하기

다음 코드를 `jev_route.py`로 저장한다. **Python 3.10 이상**, 외부 패키지 없이 실행할 수 있다. `--demo`는 아래의 고정 데이터를 사용하며 네트워크를 호출하지 않는다. 옵션 없이 실행하면 공식 API에 요청한다. 요청·응답 형식은 [HTTP API 명세](https://docs.typesafe.ai/api/system-one)를 기준으로 작성했다.

```python
import argparse
import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TEAMS = {"billing", "technical", "account", "other"}


def unit(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a number")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Expected a finite number in [0, 1]")
    return value


def route(result):
    team = result["answers"]["department"]
    human = result["answers"]["human_requested"]
    if team["type"] != "choice" or human["type"] != "noul":
        raise ValueError("Unexpected answer type")
    label = team["choice"]
    if label not in TEAMS:
        raise ValueError("Unknown department")
    confidence = unit(team["confidence"])
    human_p = unit(human["noul"])
    if label == "other" or confidence < 0.80 or human_p >= 0.30:
        return "review"
    return f"auto:{label}"


def ask():
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise ValueError("Set TYPESAFE_API_KEY or use --demo")
    payload = {
        "model": "jev-1.14.0",
        "state": {"message": "이번 달 요금이 두 번 결제됐습니다. 확인 부탁드립니다."},
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "Select the primary team for this message.",
                "criteria": {
                    "billing": "Charges, invoices, payment or refund issues",
                    "technical": "Bugs, errors or integration failures",
                    "account": "Login, password or profile issues",
                    "other": "None fits, or multiple teams are equally relevant",
                },
            },
            "human_requested": {
                "type": "noul",
                "instructions": "Does the customer explicitly ask to speak to a human agent?",
            },
        },
    }
    request = Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def demo_result(label, confidence, human_p):
    # Synthetic policy inputs, not outputs measured from Jev.
    return {"answers": {
        "department": {"type": "choice", "choice": label,
                       "confidence": confidence},
        "human_requested": {"type": "noul", "noul": human_p},
    }}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        cases = [
            ("clear", demo_result("billing", 0.92, 0.05)),
            ("uncertain", demo_result("billing", 0.20, 0.05)),
            ("human", demo_result("technical", 0.96, 0.95)),
            ("other", demo_result("other", 0.99, 0.02)),
        ]
        for name, result in cases:
            print(f"{name}: {route(result)}")
        return
    try:
        result = ask()
        decision = route(result)
        print(json.dumps({"model": result["model"], "decision": decision,
                          "answers": result["answers"],
                          "usage": result.get("usage")}, ensure_ascii=False))
    except HTTPError as exc:
        print(f"review: HTTP {exc.code}")
    except (URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        print(f"review: {type(exc).__name__}")


if __name__ == "__main__":
    main()
```

`demo_result()`에는 분기 검사에 필요한 필드만 넣었다. 실제 Choice 응답에는 후보별 `probabilities`도 포함된다. 예제의 검증은 분기에 사용하는 타입·후보·수치 범위를 확인하는 수준이다. 운영용으로 확장할 때는 전체 응답 스키마와 오류 전달 방식도 정하자.

### 2. API 키 없이 분기 동작 확인

Windows PowerShell, Linux, macOS에서 다음 명령을 실행할 수 있다. 환경에 따라 `python` 대신 `python3`를 사용한다.

```bash
python jev_route.py --demo
```

### 3. 실제 API 호출

[TypeSafe 콘솔](https://console.typesafe.ai/)에서 발급받은 키를 현재 셸의 환경 변수에 설정한다. 아래 키 문자열은 자리표시자다. 실제 키를 코드나 Git 저장소에 저장하지 않는다.

Windows PowerShell:

```powershell
$env:TYPESAFE_API_KEY = "YOUR_API_KEY"
python jev_route.py
```

Linux·macOS의 Bash:

```bash
export TYPESAFE_API_KEY="YOUR_API_KEY"
python3 jev_route.py
```

실제 호출에는 계정 접근 권한이 필요하며 사용량에 따른 요금이 발생한다. 이 글을 작성하면서 실제 API 호출은 수행하지 않았다. 문의가 한국어이므로 실제 도입 전에는 한국어 문의로 별도 평가해야 한다. 공식 문서는 영어에서 정확도가 가장 높고 다른 언어의 성능은 동일하지 않다고 안내한다. ([언어 지원 안내](https://docs.typesafe.ai/models#language-support))

## 결과 확인

`--demo` 경로를 실행해 확인한 출력은 다음과 같다.

```text
clear: auto:billing
uncertain: review
human: review
other: review
```

이 로그는 **직접 만든 입력으로 정책 코드의 동작을 확인한 결과**다. Jev가 위 문의를 실제로 이렇게 분류했다는 기록이 아니다. 실제 API 응답의 수치와 선택값은 실행 결과로 확인해야 한다.

검증에서는 높은 confidence의 `other`도 검토로 가는지, 낮은 confidence와 상담원 요청이 자동 분류를 막는지 확인한다. 응답이 깨졌거나 HTTP 오류가 발생하면 실제 호출 경로는 `review`를 출력한다. 이 출력은 검토 대상으로 표시하는 것이며, 실제 검토 큐 등록은 서비스에서 구현해야 한다.

## 실무 팁

### 흔한 실수

| 실수 | 수정 방향 |
|---|---|
| confidence 0.9를 정답 확률 90%로 취급 | 확률과 분포 요약값을 구분하고 자체 평가 |
| Noul이 0에 가까우면 불확실하다고 해석 | 아니요 쪽 예측이며, 불확실성은 0.5 부근 |
| 어떤 입력도 세 팀 중 하나로 강제 분류 | `other`와 검토 경로를 설계 |
| 여러 질문이 앞 질문의 답을 공유한다고 가정 | 독립 평가를 전제로 코드에서 결합 |
| confidence가 높으면 권한 검사도 생략 | 실행 전의 업무 조건은 코드로 검사 |
| `jev-latest`로 평가하고 모델 버전을 기록하지 않음 | 고정 ID와 응답 모델, 질문 버전을 기록 |

### 주의사항

**타입이 제한되어도 잘못된 판단은 가능하다.** 공식 Jev 1.13 한계 문서는 숫자 계산·날짜 비교·간접 참조·무관한 정보가 많은 긴 입력·적대적 내용·후보 순서 등의 문제를 공개한다. 숫자와 날짜 처리는 코드로 옮기고, 상태는 질문에 필요한 근거 위주로 구성하자. 이 문서는 **1.13에 대한 안내**이므로 모든 문제가 현재 버전에 같은 정도로 남아 있다고 단정하지는 않는다. ([Jev 1.13 한계 문서](https://docs.typesafe.ai/model-jaggedness/jev-1.13))

독립 연구도 살펴볼 필요가 있다. 2026년 10월 14일 공개된 사전공개 논문 *Are AI Decision Models Biased? A Case Study of Jev*는 질문 표현과 선택지 순서에 따라 확률·판단이 달라지는 현상을 보고한다. 특정 실험 조건의 결과를 모든 업무에 일반화할 수는 없지만, **정답률뿐 아니라 표현 변화와 선택지 순서에 대한 안정성도 평가해야 한다**는 근거가 된다. ([연구 원문](https://arxiv.org/abs/2610.19619))

운영 전에는 실제 문의에서 대표 사례와 애매한 사례를 모아 다음을 함께 비교하자.

- 자동 분류한 사례 중 맞게 분류한 비율과 전체 자동 분류 비율
- 팀별 오분류율, 상담원 요청을 놓친 비율
- 질문 표현과 후보 순서를 바꿨을 때의 결과 변화
- 모델 버전·언어별 결과, 지연시간의 p50·p95와 요청 실패율

민감한 원문을 전부 로그에 남기기보다, 필요한 식별자와 모델·질문 버전·판단값·오류 종류를 기록하는 식으로 관측 항목을 정하자. HTTP `429`나 일시적 서버 오류의 재시도·대기·검토 전환도 필요하다. 위 예제는 오류 시 검토로 넘기는 흐름을 보여주기 위해 자동 재시도를 생략했다.

### 추천 명령어

문법 검사와 키 없는 동작 확인:

```bash
python -m py_compile jev_route.py
python jev_route.py --demo
```

실제 응답은 JSON 한 줄로 출력되므로 별도 파일에 저장해 확인할 수 있다. 계정 키를 설정한 뒤 실행한다.

```bash
python jev_route.py > result.json
```

`review: ...`가 출력된 경우에는 JSON 응답이 아니라 오류 경로다. 응답을 수집할 때 성공·실패를 구분하고, 출력된 확률을 실제 정답 데이터와 대조하자.

## 마무리

### 핵심 요약

Jev는 소프트웨어에서 사용할 좁은 판단을 담당한다. `state`에 근거를 주고, Choice·Score·Noul로 질문을 정의하며, 앱은 결과와 불확실성을 보고 다음 경로를 선택한다. 올바른 응답 형식과 올바른 판단은 별도로 검증해야 한다.

### 언제 사용하면 좋은가

후보가 정해진 문의 분류, 문서 관련성 평가, 조건에 따른 라우팅처럼 반복하는 판단에 적용을 검토할 수 있다. 긴 설명이나 답변 초안이 필요하면 생성형 모델을 연결하고, 정확한 계산과 권한 검사는 코드로 처리하는 구성이 자연스럽다.

### 추가 학습 주제

확률 보정과 reliability diagram, 검토를 허용하는 분류 방식, 임계값에 따른 자동 처리율과 오류율의 관계, 생성형 모델과 판단 모델을 함께 사용하는 라우팅을 살펴보면 도입 평가를 구체화할 수 있다.

## 참고 자료

- [TypeSafe: Jev 소개](https://docs.typesafe.ai/introduction)
- [TypeSafe: System One 개념](https://docs.typesafe.ai/concepts/system-one)
- [TypeSafe: Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [TypeSafe: Choice](https://docs.typesafe.ai/primitives/choice)
- [TypeSafe: Score](https://docs.typesafe.ai/primitives/score)
- [TypeSafe: Noul](https://docs.typesafe.ai/primitives/noul)
- [TypeSafe: Confidence](https://docs.typesafe.ai/confidence)
- [TypeSafe: HTTP API](https://docs.typesafe.ai/api/system-one)
- [TypeSafe: 모델·가격·언어 지원](https://docs.typesafe.ai/models)
- [TypeSafe: Jev 1.13의 한계](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- [Imperatrice 외: Are AI Decision Models Biased? A Case Study of Jev](https://arxiv.org/abs/2610.19619)
