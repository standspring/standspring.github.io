---
title: "Python JSON 설정 파일 읽기: 문법 오류와 설정 값 오류를 나누어 확인하기"
description: "JSON의 기본 문법과 Python 자료형 변환을 설명합니다. UTF-8 설정 파일 읽기, JSONDecodeError의 행·열 확인, 필수 항목과 숫자·불리언 검증을 실행 예제로 익힙니다."
date: 2026-11-28 17:17:10 +0900
categories: [Development, Python]
tags: [Python, JSON, 설정파일, 디버깅, 초보자가이드]
toc: true
toc_sticky: true
image:
  path: /assets/img/2026-11-28-python-json-config-guide-handwritten-hero.png
  alt: "JSON 설정 파일을 읽고 문법과 설정 값의 조건을 차례로 확인하는 과정"
---

프로그램의 이름이나 재시도 횟수를 바꾸려고 매번 Python 코드를 고치고 싶지는 않다. 이런 값을 별도 JSON 파일에 두면 설정과 처리 코드를 나누기 쉽다. 다만 파일을 읽었다고 해서 프로그램이 원하는 설정이 모두 갖춰진 것은 아니다.

**파일을 읽을 수 있는지, JSON 문법이 맞는지, 프로그램이 요구하는 값인지**를 순서대로 확인해 보자. 이 글은 Python 표준 라이브러리만 사용하는 작은 로컬 예제다. 외부 서비스에 연결하거나 실제 재시도 작업을 실행하지 않고 설정을 읽어 보여 준다.

## JSON은 Python 코드와 다른 데이터 형식

JSON은 언어와 독립적인 텍스트 데이터 형식이다. 객체의 이름은 큰따옴표로 감싸고, 값에는 문자열·숫자·불리언·null·객체·배열을 넣을 수 있다. 문법 기준은 [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html)에 정리되어 있다.

```json
{
  "app_name": "연습 앱",
  "retry_count": 3,
  "enabled": true
}
```

| JSON에서 쓰는 값 | Python에서 읽은 값 |
|---|---|
| 객체 `{}` | `dict` |
| 배열 `[]` | `list` |
| 문자열 `"연습 앱"` | `str` |
| 정수 `3` | `int` |
| 소수 `3.5` | 기본 변환에서 `float` |
| `true`, `false` | `True`, `False` |
| `null` | `None` |

JSON 파일에는 Python의 `True`·`None`이나 작은따옴표 문자열을 그대로 쓰지 않는다. 일반 JSON에는 주석과 마지막 항목 뒤의 쉼표도 넣지 않는다. 같은 객체 안에서 이름을 중복해서 쓰지 않는 편이 좋다. Python의 기본 디코더는 중복 이름에서 마지막 값을 남길 수 있다.

## 1. 연습 파일 두 개 준비하기

새 연습 폴더에 다음 두 파일을 같은 위치로 저장한다.

- [config.json 다운로드](/assets/code/python-json-config-guide/config.json)
- [read_config.py 다운로드](/assets/code/python-json-config-guide/read_config.py)

PowerShell에서 그 폴더로 이동한 뒤 실행한다. Python이 이미 설치되어 있고 `python --version`이 동작하는 환경을 기준으로 한다.

```powershell
python --version
python read_config.py
$configExitCode = $LASTEXITCODE
Write-Output "exit: $configExitCode"
```

기본 예제는 앱 이름, 재시도 횟수 3, 사용 여부 `True`를 출력하고 종료 코드 0을 반환한다. `true`가 `True`로 표시되는 것은 JSON의 불리언을 Python 값으로 읽었기 때문이다.

전체 예제의 기본 파일 위치는 다음과 같이 정했다.

```python
Path(__file__).resolve().parent / "config.json"
```

현재 작업 폴더가 아니라 **스크립트 파일 옆**에서 기본 설정을 찾는다. 다른 파일을 확인하려면 다음처럼 지정할 수 있다. 이 상대 경로는 명령을 실행한 작업 폴더를 기준으로 해석한다.

```powershell
python read_config.py --config .\another-config.json
```

## 2. 파일 읽기와 JSON 변환 구분하기

핵심 코드는 다음과 같다. 전체 예제에서는 `args.config`가 위에서 지정한 파일 경로다.

```python
text = args.config.read_text(encoding="utf-8-sig")
data = json.loads(text)
config = validate_config(data)
```

첫 줄은 파일을 문자열로 읽고, 두 번째 줄은 그 문자열을 Python 값으로 변환한다. `read_text()`의 파일 읽기·인코딩 동작은 [pathlib 공식 문서](https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text)를 참고할 수 있다. 예제는 UTF-8 파일과 UTF-8 BOM이 붙은 파일을 모두 읽도록 `utf-8-sig`를 사용했다. 다른 인코딩을 자동 감지하는 설정은 아니다.

`json.loads()`의 마지막 `s`는 문자열을 처리하는 함수라는 구분으로 기억하면 편하다. 파일 객체를 직접 넘길 때는 `json.load()`를 사용한다. 변환 규칙은 [Python json 모듈 문서](https://docs.python.org/3/library/json.html)에 있다.

## 3. JSON 문법이 맞아도 설정 값은 확인하기

다음 두 값은 모두 JSON 문법상 유효하지만 Python에서 읽은 자료형이 다르다.

```json
{"retry_count": "3"}
```

```json
{"retry_count": 3}
```

![문자열 3과 숫자 3은 모두 JSON 문법을 통과하지만 정수 조건에서는 다른 결과가 되는 비교](/assets/img/2026-11-28-python-json-config-guide-validation.png)
_그림은 retry_count의 자료형만 비교한다. 전체 예제는 app_name과 enabled도 필수로 확인한다._

예제의 규칙은 다음 세 가지다. JSON 자체가 강제하는 규칙이 아니라 **이 프로그램에서 정한 조건**이다.

| 항목 | 예제 프로그램의 조건 |
|---|---|
| `app_name` | 비어 있지 않은 문자열 |
| `retry_count` | 0부터 5까지의 정수 |
| `enabled` | 불리언 |

최상위 값이 객체인지 확인하고 필수 항목을 검사한 뒤 다음처럼 자료형과 범위를 확인한다.

```python
if type(data["retry_count"]) is not int or not 0 <= data["retry_count"] <= 5:
    raise ValueError("retry_count는 0~5의 정수여야 합니다.")
if type(data["enabled"]) is not bool:
    raise ValueError("enabled는 true 또는 false여야 합니다.")
```

여기서는 정수 조건에서 불리언까지 허용하지 않도록 `type(...) is int`를 사용했다. `"3"`을 자동으로 정수로 바꾸지 않고 오류로 알려 주므로, 설정을 잘못 적은 부분이 드러난다.

## 4. 문법 오류의 행과 열 읽기

원본 예제 파일은 보관하고 `broken.json`이라는 새 파일을 만들어 다음 내용을 넣어 보자. 마지막 항목 뒤 쉼표가 있는 잘못된 JSON이다.

```text
{
  "app_name": "연습 앱",
  "retry_count": 3,
  "enabled": true,
}
```

```powershell
python read_config.py --config .\broken.json
$configExitCode = $LASTEXITCODE
Write-Output "exit: $configExitCode"
```

예제는 `JSONDecodeError`에서 행·열과 오류 설명을 꺼내 표시하고 종료 코드 1을 반환한다. 표시된 위치는 파서가 더 진행하지 못한 지점이다. 바로 앞줄의 쉼표나 닫히지 않은 따옴표도 함께 살펴본다. 세부 오류 문구는 Python 버전에 따라 달라질 수 있다.

다음에는 정상 예제의 복사본에서 `retry_count`만 `"3"`으로 바꿔 보자. 이번에는 JSON 문법 오류가 아니라 **설정 값 오류**가 나온다. 파일이 없거나 인코딩을 읽지 못한 경우에는 **파일 읽기 실패**로 구분된다.

## 5. Python 값을 JSON 문자열로 만들기

설정을 출력하거나 별도 미리보기 파일로 저장할 때는 문자열을 손으로 조립하지 않고 `json.dumps()`를 쓴다.

```python
import json

config = {"app_name": "연습 앱", "retry_count": 3, "enabled": True}
preview = json.dumps(config, ensure_ascii=False, indent=2)
print(preview)
```

`ensure_ascii=False`는 한글을 읽기 쉬운 글자로 표시하도록 하고, `indent=2`는 들여쓰기를 넣는다. 기본 설정에서 한글이 `\u` 형태로 보이더라도 그것만으로 데이터가 깨진 것은 아니다. 전체 다운로드 예제는 설정 파일을 읽기만 하며, 위 예제도 파일을 덮어쓰지 않는다.

## 문제가 생겼을 때 점검할 순서

| 증상 | 먼저 볼 항목 |
|---|---|
| 파일을 찾지 못함 | 실제 파일명·확장자, 기본 경로와 지정 경로의 차이 |
| `JSON 문법 오류` | 큰따옴표, 쉼표, 괄호, JSON의 소문자 불리언 |
| `설정 값 오류` | 필수 항목, 문자열과 숫자 차이, 허용 범위 |
| 한글 읽기 실패 | 파일이 실제 UTF-8인지 |
| 수정한 설정이 반영되지 않음 | 실행한 프로그램과 읽은 파일의 위치, 프로그램 재실행 여부 |

이 예제는 시작할 때 한 번 읽는다. 파일을 수정한다고 실행 중인 프로그램이 자동으로 다시 읽지는 않는다. 검증 함수도 위 세 항목에 맞춘 작은 예제이며, 모든 JSON 확장·중복 이름·추가 항목을 엄격하게 검사하는 범용 스키마 검증기는 아니다.

설정 읽기가 안정되면 [Python logging 사용법](/posts/python-logging-guide/)과 연결해 어떤 설정 파일을 읽었는지와 실패 원인을 기록할 수 있다. 비밀번호나 토큰이 담긴 설정 전체를 그대로 로그나 공개 저장소에 남기지는 않는다.
