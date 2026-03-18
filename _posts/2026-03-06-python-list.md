---
title: "python list 선언시 길이 설정"
date: 2026-03-06 12:00:00 +0900
categories: python
tags: [python, list, dynamic-array, mutable-sequence]
toc: true
toc_sticky: true
---

결론부터 말하면 **Python의 `list()`는 C/C++처럼 “크기만 미리 선언”하는 방식은 없습니다.**

파이썬 리스트는 **동적 배열(dynamic array)** 이라서, 요소를 추가할 때 자동으로 크기가 늘어납니다.

---

## 1️⃣ 크기만 미리 확보하고 싶을 때 (초기값으로 채우기)

보통은 아래처럼 **초기값을 넣어서 길이를 맞춥니다.**

```python
n = 10
a = [None] * n
print(a)
```

출력:

```
[None, None, None, None, None, None, None, None, None, None]
```

✔ 길이 10짜리 리스트 생성
✔ 이후 인덱스로 바로 접근 가능

```python
a[0] = 100
```

---

## 2️⃣ 숫자 0으로 초기화

```python
n = 5
a = [0] * n
```

---

## 3️⃣ 2차원 리스트 만들 때 주의 (중요!)

잘못된 방법 ❌

```python
a = [[0] * 3] * 5
```

이건 **같은 리스트 객체를 5번 참조**하기 때문에 값이 같이 바뀝니다.

올바른 방법 ✅

```python
a = [[0] * 3 for _ in range(5)]
```

---

## 4️⃣ 진짜로 메모리만 먼저 확보 가능?

파이썬 기본 리스트에서는 **불가능합니다.**
하지만 성능이 중요한 경우:

* `array` 모듈
* `numpy`
* `deque`
* `bytearray`

같은 자료구조를 사용합니다.

예:

```python
import numpy as np
a = np.zeros(10)
```

---

## 참고 (성능 관점)

파이썬 리스트는 내부적으로 **자동으로 용량을 여유 있게 확보**합니다.
그래서 보통은 미리 크기 선언할 필요가 거의 없습니다.

---
