---
title: "Python line_profiler 사용법: 느린 코드 한 줄을 찾아 최적화하기"
description: "Python line_profiler 설치부터 @profile, LINE_PROFILE, kernprof 실행, Hits·Time·Per Hit 결과 해석과 정규식 최적화 예제까지 정리합니다."
date: 2026-10-16 00:00:00 +0900
categories: [Development, Python]
tags: [Python, line_profiler, Profiling, Performance, 최적화, 프로파일링]
toc: true
toc_sticky: true
---

# Python line_profiler 사용법: 느린 코드 한 줄을 찾아 최적화하기

![코드의 느린 줄과 실행 시간 막대를 돋보기로 살펴보는 Python line_profiler 개념 삽화](/assets/img/2026-10-16-python-line-profiler.png)

*줄별 실행 시간을 확인해 병목을 찾는 과정을 표현한 개념 삽화이며, 실제 프로파일링 화면은 아니다.*

Python 프로그램이 느릴 때 코드를 읽으며 원인을 추측하기 쉽다. 하지만 실제 시간을 많이 쓰는 곳은 예상과 다를 수 있다. 한 번 실행하는 복잡한 계산보다, 수십만 번 반복하는 간단한 작업이 더 큰 병목이 되기도 한다.

이럴 때 **함수 내부의 각 줄이 얼마나 자주 실행되고, 얼마나 많은 시간을 쓰는지** 보여 주는 도구가 `line_profiler`다. 이 글에서는 설치부터 측정 결과 해석, 코드 개선 후 검증까지 하나의 예제로 살펴본다.

## 1. line_profiler는 언제 쓰면 좋을까?

먼저 구분할 것은 전체 실행 시간, 함수별 시간, 줄별 시간이다.

| 확인하고 싶은 것 | 도구 예시 | 활용 시점 |
|---|---|---|
| 작업 전체가 얼마나 걸리는가 | `time.perf_counter()` | 처리 시간과 개선 전후 비교 |
| 어떤 함수에서 시간이 많이 드는가 | `cProfile` | 분석할 함수의 범위 좁히기 |
| 그 함수의 어느 줄이 느린가 | `line_profiler` | 반복 계산이나 호출 위치 확인 |
| 짧은 코드 조각 중 무엇이 빠른가 | `timeit` | 작은 대안의 반복 비교 |

처음부터 모든 함수를 줄 단위로 측정하면 결과가 너무 많아진다. 전체 흐름에서 느린 함수를 찾고, 그 함수에만 `line_profiler`를 적용하는 순서가 실용적이다. 공식 프로젝트도 함수 수준 분석 이후 줄 수준 병목을 확인하는 용도로 소개한다. ([공식 저장소](https://github.com/pyutils/line_profiler))

## 2. 설치하기

프로젝트에서 사용하는 가상환경을 활성화한 뒤 설치한다.

```bash
python -m pip install line_profiler
```

`python -m pip`를 쓰면 현재 `python`에 연결된 환경에 패키지를 설치할 수 있다. 설치된 버전은 다음 명령으로 확인한다.

```bash
python -m pip show line_profiler
```

설치에 실패한다면 Python 버전과 운영체제에 맞는 wheel이 제공되는지 먼저 확인하자. wheel이 없는 환경에서는 소스 빌드에 필요한 컴파일러 등의 도구가 요구될 수 있다. ([설치 안내](https://github.com/pyutils/line_profiler#installation))

## 3. 분석할 예제 준비하기

문자열에서 숫자를 추출하는 `demo_profile.py`를 만든다. 아래 코드는 설명을 위해 **반복문 안에서 같은 정규식을 계속 컴파일하는 구조**로 작성했다.

```python
import re

from line_profiler import profile


@profile
def extract_numbers(rows):
    result = []
    for row in rows:
        pattern = re.compile(r"\d+")
        numbers = pattern.findall(row)
        result.append(sum(int(number) for number in numbers))
    return result


if __name__ == "__main__":
    rows = [f"order={i}, quantity={i % 7}, price=1200" for i in range(100_000)]
    totals = extract_numbers(rows)
    print(len(totals), totals[:3])
```

정상 실행 결과는 다음과 같다.

```text
100000 [1200, 1202, 1204]
```

`@profile`은 측정할 함수를 지정한다. 여기서는 입력 데이터 생성 시간을 제외하고 `extract_numbers()` 내부를 살펴보도록 범위를 정했다. 프로그램 전체 처리 성능을 판단할 때는 입력 생성 시간까지 포함할지 별도로 결정해야 한다.

## 4. 프로파일링 실행하기

### 권장 흐름: 환경변수로 측정 활성화

`from line_profiler import profile`로 가져온 데코레이터는 기본적으로 측정이 비활성화되어 있다. 환경변수 `LINE_PROFILE=1`로 활성화하고 평소처럼 스크립트를 실행할 수 있다. 종료 시 결과 파일과 확인 방법이 출력된다. ([공식 Quick Start](https://github.com/pyutils/line_profiler#quick-start))

Windows PowerShell에서는 다음과 같이 실행한다.

```powershell
$env:LINE_PROFILE = "1"
python demo_profile.py
Remove-Item Env:LINE_PROFILE
```

마지막 명령은 현재 PowerShell 세션의 설정을 지운다. 측정이 끝난 뒤 일반 실행으로 돌아가기 위한 단계다.

macOS·Linux의 Bash 계열 셸에서는 다음과 같다.

```bash
LINE_PROFILE=1 python demo_profile.py
```

일반 실행에서도 `line_profiler`를 import하므로 패키지 설치 자체는 필요하다. 측정 비활성화가 의존성 제거를 뜻하지는 않는다.

### 대안: kernprof로 실행

기존 튜토리얼에서 자주 보이는 `kernprof` 방식도 지원된다.

```bash
python -m kernprof -l -v demo_profile.py
```

- `-l`: 줄 단위 프로파일링을 사용한다.
- `-v`: 실행 후 측정 결과를 화면에 보여 준다.

기본 출력 파일은 다음 명령으로 다시 읽을 수 있다.

```bash
python -m line_profiler demo_profile.py.lprof
```

이 `.lprof` 파일 이름은 위의 `kernprof` 실행 기준이다. 환경변수 방식에서는 종료 메시지에 표시된 실제 파일 경로를 확인하자. 두 방식의 사용법은 [kernprof 문서](https://kernprof.readthedocs.io/en/stable/auto/kernprof.html)와 [line_profiler 문서](https://kernprof.readthedocs.io/en/stable/auto/line_profiler.html)에 정리되어 있다.

## 5. 결과표 읽는 법

다음 표는 **컬럼 해석을 위한 가상의 예시**다. 위 코드를 실행해 얻은 벤치마크가 아니며, 줄 번호도 생략했다.

```text
Timer unit: 1e-06 s

Hits       Time      Per Hit    % Time    Line Contents
100000     30000.0    0.3        10.0      pattern = re.compile(r"\d+")
100000     90000.0    0.9        30.0      numbers = pattern.findall(row)
100000    180000.0    1.8        60.0      result.append(sum(int(number) for number in numbers))
```

실제 결과에는 `Line #` 컬럼과 초기화·반복문·반환문 등 다른 실행 줄도 포함된다.

| 컬럼 | 의미 | 읽을 때 확인할 점 |
|---|---|---|
| `Line #` | 소스 줄 번호 | 측정한 소스와 현재 파일이 같은지 확인 |
| `Hits` | 해당 줄 실행 횟수 | 반복 횟수가 예상보다 많지 않은지 확인 |
| `Time` | 해당 줄에 누적된 시간 | 상단 `Timer unit`을 곱해 초로 환산 |
| `Per Hit` | `Time / Hits` | 한 번 실행할 때 드는 평균 비용 |
| `% Time` | 해당 함수 측정 시간 중 비율 | 프로그램 전체 비중과 구분 |
| `Line Contents` | 측정한 소스 코드 | 어떤 연산과 호출이 포함되는지 확인 |

예시의 타이머 단위가 `1e-06 s`이므로 `180000.0`은 `0.18초`에 해당한다. **숫자만 보고 밀리초라고 가정하면 안 된다.** 결과표의 컬럼과 단위는 [공식 사용 예제](https://kernprof.readthedocs.io/en/stable/auto/line_profiler.html)를 참고할 수 있다.

우선 `% Time`과 `Time`이 큰 줄을 보고, 이어 `Hits`와 `Per Hit`으로 이유를 나눠 본다. 한 번의 비용이 큰지, 작은 작업을 지나치게 반복하는지에 따라 개선 방향이 달라진다.

또한 위 마지막 줄에는 정수 변환, 합산, 리스트 추가가 함께 들어 있다. 원인을 더 구체적으로 알고 싶다면 중간 변수로 나눠 재측정할 수 있다. 다만 코드를 나누는 일 자체가 실행 비용에 영향을 줄 수 있다는 점도 고려해야 한다.

## 6. 측정 결과를 바탕으로 개선하기

같은 패턴을 처리하는 예제에서는 컴파일된 정규식을 반복문 밖으로 옮길 수 있다.

```python
@profile
def extract_numbers_fast(rows):
    pattern = re.compile(r"\d+")
    result = []
    for row in rows:
        numbers = pattern.findall(row)
        result.append(sum(int(number) for number in numbers))
    return result
```

이 코드를 앞의 파일에 `if __name__ == "__main__":` 블록보다 위에 추가하고 호출 대상을 바꾸면 된다. 기존 함수의 컴파일 호출은 행 수만큼 실행되지만, 개선 함수에서는 호출 한 번당 한 번 실행된다.

다만 Python의 `re`는 최근 패턴을 캐시한다. 따라서 기존 코드가 매번 정규식 전체를 새로 컴파일한다고 해석해서는 안 된다. 여기서 제거하는 것은 반복적인 `re.compile()` 호출과 캐시 조회 등의 비용이다. 캐시 동작은 [Python re 문서](https://docs.python.org/3/library/re.html#re.compile)에 설명되어 있다.

이 변경만으로 전체 시간이 크게 줄어든다고 보장할 수도 없다. 숫자 변환과 합산이 대부분의 시간을 차지한다면, 정규식 준비 비용을 줄여도 개선 폭은 작다. 줄 단위 결과는 **다음에 무엇을 바꿔 볼지 정하는 근거**로 사용하자.

## 7. 개선 전후 비교는 프로파일러를 끄고 확인하기

줄마다 시간을 기록하는 작업에는 부가 비용이 따른다. 프로파일러 실행 중 나온 전체 시간을 그대로 서비스의 처리 시간으로 간주하기보다, 개선 후에는 측정을 비활성화하고 같은 입력으로 비교하는 것이 좋다.

두 함수가 들어 있는 `demo_profile.py`와 같은 폴더에 `benchmark.py`를 만든다.

```python
from statistics import median
from timeit import repeat

from demo_profile import extract_numbers, extract_numbers_fast


rows = [f"order={i}, quantity={i % 7}, price=1200" for i in range(100_000)]

# 속도를 비교하기 전에 결과가 같은지 확인한다.
assert extract_numbers(rows) == extract_numbers_fast(rows)

for function in (extract_numbers, extract_numbers_fast):
    function(rows)  # 워밍업
    samples = repeat(lambda: function(rows), number=1, repeat=7)
    print(f"{function.__name__}: median={median(samples):.6f}s")
```

`LINE_PROFILE` 환경변수를 해제한 상태에서 다음과 같이 일반 실행한다. `kernprof`로 실행하지 않는다.

```bash
python benchmark.py
```

이 비교에서는 입력 생성 시간을 제외하고 함수 실행 시간만 측정한다. 중앙값을 쓰는 것은 일시적인 지연의 영향을 줄이려는 선택이다. 데이터 크기, 문자열 길이, Python 버전, 시스템 상태에 따라 결과는 달라질 수 있으므로 고정된 배속 수치를 기대하지 말자.

## 8. 결과 해석에서 주의할 점

### 호출한 함수 내부가 자동으로 펼쳐지지는 않는다

측정 함수가 다른 함수를 호출하면 호출 비용이 호출 줄에 나타날 수 있다. 그 함수 내부의 어느 줄이 느린지 보려면 해당 함수도 측정 대상으로 지정해야 한다.

### 라이브러리 호출 한 줄이 느릴 수도 있다

NumPy·Pandas 등에서 한 줄이 오래 걸린다고 해서 Python 줄 수준에서 내부 원인까지 확인할 수 있는 것은 아니다. 네이티브 연산이나 외부 시스템의 동작은 별도 분석이 필요할 수 있다.

### 기다리는 시간과 계산 시간을 구분하자

파일 읽기나 네트워크 호출이 오래 걸리면 해당 줄이 병목처럼 보일 수 있다. 이 경우 반복문 문법을 바꾸는 것보다 요청 횟수, 입출력 방식, 캐시 정책 등을 검토해야 한다. 비동기·멀티스레드·멀티프로세스 코드에서는 단순한 단일 스레드 예제와 같은 방식으로 시간을 해석하기 어렵다.

### 메모리 사용량을 보여 주는 도구는 아니다

`line_profiler`는 실행 시간을 분석한다. 큰 중간 객체 때문에 메모리가 부족하다면 `tracemalloc` 같은 메모리 분석 도구로 문제를 따로 확인해야 한다. 동시 실행과 측정상의 제약은 [공식 문서의 Limitations](https://kernprof.readthedocs.io/en/stable/auto/line_profiler.html#limitations)를 참고하자.

## 마무리

실무에서는 다음 순서로 적용하면 된다.

1. 대표 입력으로 느린 상황을 재현한다.
2. 함수 수준으로 분석 범위를 좁힌다.
3. 대상 함수에 `@profile`을 붙이고 줄별 시간을 측정한다.
4. `Time`, `Hits`, `Per Hit`을 함께 읽고 원인을 추정한다.
5. 한 가지 변경을 적용하고 출력이 같은지 확인한다.
6. 프로파일러를 끈 뒤 같은 입력으로 성능을 다시 비교한다.

핵심은 느려 보이는 코드를 무작정 고치는 대신, 실제로 시간을 쓰는 위치를 확인하는 것이다. 줄별 측정 결과와 프로그램 전체의 실행 시간을 함께 보면 작은 수정이 실제 성능 개선으로 이어졌는지 판단할 수 있다.

## 참고 자료

*본문 예제는 Python 3.14.5와 line_profiler 5.0.2에서 실행을 확인했다. 결과표의 숫자는 해석을 위한 가상의 예시다.*

- [line_profiler 공식 저장소](https://github.com/pyutils/line_profiler)
- [line_profiler 패키지 문서](https://kernprof.readthedocs.io/en/stable/auto/line_profiler.html)
- [kernprof 실행 옵션](https://kernprof.readthedocs.io/en/stable/auto/kernprof.html)
- [Python re.compile과 패턴 캐시](https://docs.python.org/3/library/re.html#re.compile)
- [Python timeit 문서](https://docs.python.org/3/library/timeit.html)
