---
title: "Python tracemalloc 사용법: 메모리가 늘어나는 코드 찾기"
description: "Python 표준 라이브러리 tracemalloc으로 현재·최대 메모리, 스냅샷 차이, 할당 위치를 분석하고 캐시 누적과 일시적인 메모리 피크를 구분하는 방법을 정리합니다."
date: 2026-10-17 00:00:00 +0900
categories: [Development, Python]
tags: [Python, tracemalloc, Memory, Profiling, 메모리, 최적화, 프로파일링]
toc: true
toc_sticky: true
---

# Python tracemalloc 사용법: 메모리가 늘어나는 코드 찾기

![코드의 할당 위치와 스냅샷 사이에 늘어난 메모리 블록을 돋보기로 살펴보는 Python tracemalloc 개념 삽화](/assets/img/2026-10-17-python-tracemalloc.png)

*메모리 할당 위치와 스냅샷 변화를 추적하는 과정을 표현한 개념 삽화이며, 실제 분석 화면은 아니다.*

배치 작업을 반복할수록 메모리가 늘거나, 큰 데이터를 처리하는 순간 메모리 부족으로 프로그램이 종료되는 일이 있다. 이때 먼저 확인할 것은 **작업이 끝나도 남는 데이터인지, 처리 중에만 크게 생기는 임시 데이터인지**다.

`tracemalloc`은 Python이 추적하는 메모리 블록의 할당 위치를 살펴보는 표준 라이브러리다. 별도 패키지 설치 없이 사용할 수 있다. [공식 문서](https://docs.python.org/3/library/tracemalloc.html)에 소개된 기능을 바탕으로, 직접 실행할 수 있는 예제로 메모리 증가의 원인을 좁혀 보자.

## 1. line_profiler와 무엇이 다를까?

이전에 다룬 [line_profiler 글]({% post_url 2026-10-16-python-line-profiler %})은 느린 줄을 찾는 데 초점을 맞췄다. 이번에는 메모리를 만드는 위치를 찾는다.

| 문제 상황 | 먼저 확인할 것 | 분석 방향 |
|---|---|---|
| 함수 실행이 오래 걸린다 | 줄별 실행 시간 | `line_profiler` |
| 작업을 반복할수록 메모리가 늘어난다 | 작업 전후에 남는 할당 | 스냅샷 차이 |
| 처리 중 잠깐 메모리가 급증한다 | 현재 사용량과 최대 사용량 | 피크 측정 |
| 운영체제의 프로세스 메모리가 크다 | 프로세스 전체 메모리 | RSS 등 운영체제 지표도 함께 확인 |

느린 코드와 메모리를 많이 쓰는 코드가 항상 같지는 않다. 대량의 결과를 리스트에 저장하면 재사용은 편하지만 메모리를 오래 점유한다. 반대로 결과를 하나씩 처리하면 저장 공간을 줄일 수 있어도, 다시 순회하려면 재계산이 필요할 수 있다. 요구사항에 맞는 절충이 필요하다.

## 2. 현재 사용량과 최대 사용량 측정하기

다음 코드를 `demo_tracemalloc.py`로 저장한다.

```python
import tracemalloc


def total_with_list(size):
    values = [number * number for number in range(size)]
    return sum(values)


def total_streaming(size):
    return sum(number * number for number in range(size))


def measure(function, size):
    # 각 실행을 독립된 추적 구간으로 비교한다.
    tracemalloc.start()
    try:
        result = function(size)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, current, peak


if __name__ == "__main__":
    size = 200_000
    first = measure(total_with_list, size)
    second = measure(total_streaming, size)
    assert first[0] == second[0]

    for name, (_, current, peak) in zip(("list", "generator"), (first, second)):
        print(f"{name}: current={current / 1024:.2f} KiB, "
              f"peak={peak / 1024:.2f} KiB")
```

```bash
python demo_tracemalloc.py
```

이 예제에서는 제곱값을 모두 리스트에 담는 방식과 제너레이터 표현식으로 순차 합산하는 방식을 비교한다. 출력의 단위는 `KiB`, 즉 `1024바이트`다.

- `current`: 조회 시점에 남아 있는 추적 대상 메모리.
- `peak`: 추적 시작 이후 기록된 최대 메모리.

함수 반환 후에는 `values` 리스트가 더 이상 필요하지 않다. 그래서 `current`가 작더라도 실행 중의 `peak`는 클 수 있다. 여기서 중요한 것은 반환 이후의 한 시점만 보면 **중간 리스트의 비용을 놓칠 수 있다는 점**이다.

제너레이터 방식은 전체 제곱값을 리스트로 보관하지 않는다. 합계만 필요한 작업이라면 이런 변경을 검토할 수 있다. 다만 제너레이터로 만든 결과를 나중에 다시 `list()`로 감싸면 전체 저장 비용이 돌아온다.

이 측정 함수는 별도의 스크립트에서 추적을 시작하지 않은 상태로 사용하는 예제다. 이미 진단 도구가 추적 중인 애플리케이션에서는 `start()`와 `stop()`으로 기존 진단 상태를 바꾸지 않도록 측정 구간을 설계해야 한다.

## 3. 스냅샷으로 남아 있는 할당 위치 찾기

피크가 높다는 사실만으로는 어느 코드에서 데이터가 남는지 알기 어렵다. 이번에는 응답 본문을 캐시에 계속 보관하는 상황을 만든다. `demo_snapshot.py`로 저장한다.

```python
from pathlib import Path
import tracemalloc


cache = []


def handle_batch(count):
    for index in range(count):
        payload = bytearray(4096)
        cache.append(payload)


def only_this_file(snapshot):
    return snapshot.filter_traces([
        tracemalloc.Filter(True, str(Path(__file__).resolve()))
    ])


if __name__ == "__main__":
    tracemalloc.start(10)
    try:
        before = tracemalloc.take_snapshot()
        handle_batch(2_000)
        after = tracemalloc.take_snapshot()

        changes = only_this_file(after).compare_to(
            only_this_file(before), "lineno"
        )
        print("[increases]")
        for stat in [item for item in changes if item.size_diff > 0][:5]:
            print(stat)

        cache.clear()
        released = tracemalloc.take_snapshot()
        print("[after clear]")
        for stat in only_this_file(released).compare_to(
            only_this_file(after), "lineno"
        )[:5]:
            print(stat)
    finally:
        tracemalloc.stop()
```

```bash
python demo_snapshot.py
```

`payload = bytearray(4096)` 줄과 `cache.append(payload)` 줄에 주목하자. 전자는 본문 버퍼를 만들고, 후자는 참조를 보관하면서 리스트 저장 공간을 늘린다. 지역 변수 `payload`가 다음 반복에서 덮어써져도 캐시가 이전 버퍼들을 참조하기 때문에 데이터가 남는다.

이것은 의도적으로 캐시를 유지하는 예제다. 실무에서 같은 패턴이 발견되면 보관이 필요한지, 개수나 총용량 제한이 있는지, 만료 조건이 작동하는지를 점검하면 된다.

### 결과의 size와 count 읽기

다음은 형식 설명을 위한 가상의 출력이다. 실제 수치와 줄 번호는 환경에 따라 달라진다.

```text
demo_snapshot.py:10: size=8100 KiB (+8100 KiB), count=4000 (+4000), average=2074 B
```

| 항목 | 의미 |
|---|---|
| `파일:줄` | 할당이 기록된 위치 |
| `size` | 새 스냅샷에 남은 블록들의 크기 합계 |
| 괄호 안 크기 | 이전 스냅샷에 비해 증가하거나 감소한 크기 |
| `count` | 새 스냅샷의 메모리 블록 수 |
| 괄호 안 개수 | 블록 수의 변화 |
| `average` | 새 스냅샷에서 블록당 평균 크기 |

**메모리 블록 수를 Python 객체 수와 같다고 해석하면 안 된다.** 예를 들어 하나의 버퍼 객체가 내부 저장 공간을 별도로 할당할 수 있다.

`after.compare_to(before, "lineno")`는 파일과 줄 단위의 순변화를 보여 준다. 중간에 생겼다가 사라진 모든 할당을 합산하는 기능은 아니다. 또한 기본 정렬은 크기 차이의 절댓값을 기준으로 하므로, 큰 감소가 위에 나올 수도 있다. 증가만 보고 싶어 예제에서는 `size_diff > 0`을 선택했다. ([Snapshot API](https://docs.python.org/3/library/tracemalloc.html#tracemalloc.Snapshot.compare_to))

## 4. 메모리 증가가 곧 누수일까?

첫 요청을 처리하면서 모듈을 불러오거나 캐시를 채우면 메모리가 늘 수 있다. 두 시점 사이에 증가했다는 사실만으로 누수를 확정하기는 어렵다.

서비스를 진단한다면 다음 순서가 도움이 된다.

1. 초기화와 워밍업을 끝낸다.
2. 비슷한 입력과 동시 요청 수로 작업을 반복한다.
3. 작업 완료 시점마다 스냅샷을 비교한다.
4. 증가가 일정 수준에서 멈추는지 계속 누적되는지 확인한다.
5. 늘어나는 할당 위치와 해당 데이터를 보관하는 코드를 조사한다.

앞의 캐시는 `cache.clear()` 이후 버퍼 참조가 사라지므로 할당 감소를 관찰할 수 있다. 하지만 실제 코드에서 다른 변수가 같은 데이터를 참조한다면 캐시만 비워도 메모리가 남는다.

또한 할당 위치와 참조를 유지하는 위치는 다를 수 있다. 스냅샷에서 버퍼를 만드는 줄을 찾았다고 조사가 끝나는 것은 아니다. 반환된 버퍼가 어떤 리스트, 딕셔너리, 작업 큐 등에 들어가는지도 확인해야 한다.

## 5. 호출 경로와 추적 시작 시점 정하기

기본적으로 저장하는 호출 프레임은 하나다. 앞의 예제는 `start(10)`으로 깊이를 늘렸다. 같은 생성 함수가 여러 곳에서 호출된다면, `after` 스냅샷이 있는 지점에 다음 코드를 추가해 호출 경로별로 살펴볼 수 있다.

```python
for stat in only_this_file(after).statistics("traceback")[:3]:
    print(f"{stat.size / 1024:.1f} KiB, {stat.count} blocks")
    for line in stat.traceback.format():
        print(line)
```

초기 import부터 보고 싶다면 프로그램 시작 시 추적을 켤 수도 있다.

```bash
python -X tracemalloc=10 your_app.py
```

PowerShell에서 환경변수로 설정하는 방법은 다음과 같다.

```powershell
$env:PYTHONTRACEMALLOC = "10"
python your_app.py
Remove-Item Env:PYTHONTRACEMALLOC
```

시작 시 추적을 켜는 옵션은 통계를 자동 출력하지 않는다. 프로그램 안에서 스냅샷 등을 조회하는 코드는 여전히 필요하다. 시작 전에 할당된 블록은 추적에 포함되지 않으며, 프레임을 많이 보관하면 진단 비용도 늘어난다. ([시작 설정](https://docs.python.org/3/library/tracemalloc.html#tracemalloc.start))

## 6. reset_peak와 stop의 차이

긴 프로그램 안에서 여러 작업의 피크를 나눠 보고 싶을 때는 `reset_peak()`를 사용할 수 있다. 이 기능은 Python 3.9 이상에서 제공한다.

```python
import tracemalloc

tracemalloc.start()
retained = bytearray(1024 * 1024)
tracemalloc.reset_peak()
baseline, _ = tracemalloc.get_traced_memory()

temporary = bytearray(2 * 1024 * 1024)
del temporary
current, peak = tracemalloc.get_traced_memory()

print(f"current={current}, peak={peak}, baseline={baseline}")
tracemalloc.stop()
```

`reset_peak()`는 최대치를 현재 추적 사용량으로 재설정한다. 기존 할당 기록을 지우거나 메모리를 해제하지 않는다. 따라서 위 피크에는 이미 보관 중인 `retained`의 메모리도 포함된다.

반면 `stop()`은 추적을 중단하고 기록을 지운다. 비교할 스냅샷이 필요하면 중단 전에 확보해야 한다. ([reset_peak](https://docs.python.org/3/library/tracemalloc.html#tracemalloc.reset_peak), [stop](https://docs.python.org/3/library/tracemalloc.html#tracemalloc.stop))

## 7. 결과를 해석할 때 주의할 점

### RSS와 같은 숫자를 기대하지 말자

작업 관리자에 나오는 프로세스 메모리는 Python의 추적 대상 블록만 계산한 값과 범위가 다르다. 네이티브 라이브러리의 직접 할당, 메모리 매핑 등은 추적 연동 방식에 따라 보이지 않을 수 있다. 확장 모듈이 추적에 참여할 수도 있으므로, 라이브러리의 메모리가 전부 보인다거나 전부 안 보인다고 단정하지 말자.

Python에서 객체가 해제돼도 런타임과 메모리 할당자가 공간을 재사용하려고 보관하면 운영체제 지표가 바로 줄지 않을 수 있다. Python의 메모리 계층에 대해서는 [메모리 관리 문서](https://docs.python.org/3/c-api/memory.html)를 참고하자.

### 스냅샷과 추적도 자원을 사용한다

진단 상태에서 나온 실행 시간을 평상시 성능으로 간주하기는 어렵다. 스냅샷을 계속 리스트에 쌓아 두는 진단 코드 자체도 부담이 될 수 있다. 필요한 구간과 횟수로 제한하고, 수정 후에는 진단을 끈 실행도 확인하자.

### 필터는 필요한 할당까지 가릴 수 있다

예제의 필터는 해당 파일에서 직접 기록된 할당만 골라 읽기 쉽게 만든다. 라이브러리 안에서 발생한 할당은 빠질 수 있으므로, 원인이 보이지 않으면 필터 없는 결과와 함께 확인하자. 호출 경로 전체를 대상으로 필터링하려면 프레임 깊이와 `all_frames` 옵션의 의미도 살펴봐야 한다.

## 마무리

메모리 문제를 재현했다면 먼저 현재 사용량과 피크를 구분하자. 종료 후 사용량은 작은데 피크만 크면 임시 데이터의 생성 방식을, 반복할수록 남는 양이 늘면 데이터 보관 구조를 살펴볼 수 있다.

`tracemalloc`로 할당 위치를 좁힌 뒤, 데이터가 필요한 기간과 보관량을 검토하고 같은 입력으로 다시 측정하면 개선 효과를 확인하기 쉽다. 최적화 전후에 처리 결과가 같은지도 함께 검증하자.

## 참고 자료

*본문 Python 예제는 Python 3.14.5에서 실행을 확인했다. 스냅샷 출력 예시의 숫자는 형식 설명을 위한 가상의 값이다.*

- [Python tracemalloc 공식 문서](https://docs.python.org/3/library/tracemalloc.html)
- [Python 메모리 관리](https://docs.python.org/3/c-api/memory.html)
- [함께 읽기: Python line_profiler 사용법]({% post_url 2026-10-16-python-line-profiler %})
