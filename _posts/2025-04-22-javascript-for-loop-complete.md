---
title: "JavaScript for 반복문 완전 정리 (for / for...of / for...in / forEach)"
date: 2025-12-19
tags: [JavaScript, 반복문, for문, forof, forin, forEach, 기초문법]
---

# JavaScript for 반복문 완전 정리 (for / for...of / for...in / forEach)

JavaScript에서 반복은 거의 모든 코드에 등장합니다.  
배열을 순회하고, 객체를 다루고, 비동기 작업을 반복하거나, 조건에 따라 중간에 멈추기도 하죠.

그런데 JS에는 반복 방식이 여러 가지라서, 상황에 맞지 않는 반복문을 쓰면 **버그**나 **성능 저하**,  
혹은 **예상과 다른 동작(특히 객체/배열 혼용, 비동기)**이 생길 수 있습니다.

이 글에서는 다음을 한 번에 정리합니다.

- `for` (기본 for)
- `for...of` (값 순회)
- `for...in` (키 순회)
- `forEach` (콜백 기반 배열 순회)
- 언제 어떤 걸 쓰면 좋은지 + 흔한 실수(특히 `var`, 비동기)

---

## 1) 기본 `for` — 가장 범용적인 반복문

```javascript
for (let i = 0; i < 5; i++) {
  console.log(i);
}
```

### 장점
- 반복 범위/증가 조건을 **직접 제어** 가능
- `break`, `continue` 사용 가능
- 성능적으로도 안정적이고 예측 가능

### 언제 쓰면 좋은가?
- 인덱스가 꼭 필요할 때
- “중간 탈출(break)”이 필요할 때
- 두 배열을 같은 인덱스로 동시에 접근할 때

```javascript
const a = [10, 20, 30];
const b = [1, 2, 3];

for (let i = 0; i < a.length; i++) {
  console.log(a[i] + b[i]);
}
```

---

## 2) `for...of` — **값(value)**을 순회 (배열/문자열/iterable)

`for...of`는 배열/문자열 등 **반복 가능한(iterable)** 객체의 “요소 값”을 순회합니다.

```javascript
const arr = [10, 20, 30];

for (const value of arr) {
  console.log(value);
}
```

문자열도 가능합니다.

```javascript
for (const ch of "hello") {
  console.log(ch);
}
```

### 장점
- 인덱스가 필요 없을 때 코드가 깔끔함
- `break`, `continue` 사용 가능
- `forEach`와 달리 **비동기/예외 처리와 궁합이 좋음**

---

## 3) `for...in` — **키(key)**를 순회 (객체 전용으로 생각하기)

`for...in`은 **객체의 프로퍼티 이름(key)**을 순회합니다.

```javascript
const user = { name: "Alex", age: 30, job: "developer" };

for (const key in user) {
  console.log(key, user[key]);
}
```

### ⚠️ 배열에 쓰면 왜 위험할까?

배열은 객체이기도 해서 `for...in`이 “인덱스”를 문자열로 순회합니다.  
또한, 의도치 않게 **프로토타입 체인의 속성까지** 순회할 수도 있습니다.

```javascript
const arr = [1, 2, 3];
arr.custom = "x";

for (const k in arr) {
  console.log(k); // "0", "1", "2", "custom" (환경에 따라 더 나올 수도)
}
```

> 정리: **배열은 `for...of` 또는 `for`**가 안전합니다.  
> `for...in`은 **객체** 순회에만 쓰는 것을 추천합니다.

---

## 4) `forEach` — 배열 전용, “중간 탈출이 없는” 순회

```javascript
const arr = [10, 20, 30];

arr.forEach((value, index) => {
  console.log(index, value);
});
```

### 특징
- 배열에만 사용(유사 배열/iterable에는 직접 사용 불가)
- `break`, `continue` 사용 불가
- 콜백 기반이라 가독성이 좋은 편

### `forEach`에서 break가 안 되는 이유
`forEach`는 내부적으로 콜백을 호출하는 구조라서, 루프 제어를 콜백 밖으로 “탈출”시키지 않습니다.

```javascript
const arr = [1, 2, 3, 4, 5];

// "3을 만나면 멈추고 싶다" -> forEach로는 불편함
arr.forEach((v) => {
  if (v === 3) {
    // break; // ❌ 불가능
    return;  // 이건 콜백만 종료, 반복은 계속됨
  }
  console.log(v);
});
```

이럴 땐 `for...of`가 깔끔합니다.

```javascript
for (const v of [1, 2, 3, 4, 5]) {
  if (v === 3) break;
  console.log(v);
}
```

---

## 5) 언제 어떤 반복문을 쓰면 좋을까?

| 상황 | 추천 | 이유 |
|------|------|------|
| 배열을 값 중심으로 깔끔하게 순회 | `for...of` | 가독성 + break/continue 가능 |
| 인덱스가 필요하거나 범위를 세밀 제어 | `for` | 가장 유연함 |
| 객체의 key/value 순회 | `for...in` (또는 `Object.keys`) | 객체 프로퍼티용 |
| 단순 배열 처리(중간 탈출 필요 없음) | `forEach` | 짧고 읽기 쉬움 |

추가로, 객체 순회는 `Object.keys()`/`Object.entries()` 조합도 자주 씁니다.

```javascript
const user = { name: "Alex", age: 30 };

for (const [key, value] of Object.entries(user)) {
  console.log(key, value);
}
```

---

## 6) 흔한 실수 1: `var`와 클로저(setTimeout) 문제

```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
```

결과(대부분 환경):
```text
3
3
3
```

### 왜?
`var`는 블록 스코프가 아니라 함수 스코프라서, 루프가 끝난 뒤 `i`가 3으로 고정됩니다.

### 해결: `let` 사용

```javascript
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
```

---

## 7) 흔한 실수 2: 비동기 + forEach

아래 코드는 **await가 기대대로 동작하지 않습니다.**

```javascript
const items = [1, 2, 3];

items.forEach(async (v) => {
  await new Promise((r) => setTimeout(r, 100));
  console.log(v);
});

console.log("done");
```

`done`이 먼저 출력되거나, 순서가 섞여 보일 수 있어요.

### 해결: `for...of` + await

```javascript
const items = [1, 2, 3];

for (const v of items) {
  await new Promise((r) => setTimeout(r, 100));
  console.log(v);
}

console.log("done");
```

---

## 8) 결론

- **배열 값 순회**: `for...of` (가독성 좋고 제어 가능)
- **인덱스/범위 제어**: `for`
- **객체 키 순회**: `for...in` 또는 `Object.entries()`
- **단순 처리**: `forEach` (단, break/continue/await 제약)

반복문을 상황에 맞게 선택하면 코드가 훨씬 읽기 쉽고, 버그도 줄어듭니다.