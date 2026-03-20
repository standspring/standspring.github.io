---
title: "SQL 최적화 완벽 가이드 (실무에서 바로 쓰는 13가지 방법)"
date: 2026-03-20
categories: [Database, SQL]
tags: [sql, sql최적화, database, 인덱스, 성능튜닝, mysql, query, backend]
description: "SQL 성능을 빠르게 개선하는 실전 최적화 방법 13가지. 인덱스, 실행계획, JOIN, WHERE 튜닝까지 한 번에 정리."
---

SQL 최적화의 핵심은 단 하나입니다.

> **"적은 데이터를, 덜 읽고, 덜 정렬하고, 덜 계산하게 만드는 것"**

이 글에서는 실무에서 바로 적용 가능한 SQL 최적화 방법을 정리합니다.

---

## 1. 실행 계획(Execution Plan)부터 확인하자

SQL 튜닝은 감이 아니라 **근거 기반**으로 해야 합니다.

확인할 것:
- Full Table Scan 여부
- 인덱스 사용 여부
- JOIN 순서
- 불필요한 정렬(SORT)
- 임시 테이블 사용 여부

👉 **실행 계획을 보면 병목이 보입니다**

---

## 2. WHERE 절에서 데이터 양을 줄여라

가장 효과가 큰 최적화 포인트입니다.

### ❌ 비효율
```sql
WHERE YEAR(order_date) = 2025
````

### ✅ 개선

```sql
WHERE order_date >= '2025-01-01'
  AND order_date < '2026-01-01'
```

이유:

* 컬럼에 함수 적용 → 인덱스 못 탐
* 범위 조건 → 인덱스 활용 가능

---

## 3. 인덱스를 제대로 설계하라

SQL 성능 = 인덱스 설계

### 좋은 인덱스 대상

* WHERE 조건 컬럼
* JOIN 컬럼
* ORDER BY / GROUP BY 컬럼

### 예시

```sql
SELECT *
FROM orders
WHERE user_id = 1001
  AND status = 'PAID'
ORDER BY created_at DESC;
```

👉 추천 인덱스:

```sql
(user_id, status, created_at)
```

### ⚠️ 주의

* 인덱스 많으면 쓰기 성능 저하
* 단일 인덱스 여러 개보다 **복합 인덱스**가 유리

---

## 4. SELECT * 사용 금지

### ❌

```sql
SELECT *
```

### ✅

```sql
SELECT order_id, user_id, total_price
```

이유:

* I/O 감소
* 네트워크 비용 감소
* 커버링 인덱스 가능

---

## 5. JOIN은 작게, 필요한 만큼만

JOIN 자체는 문제가 아니지만 **대량 데이터 JOIN**은 위험합니다.

### 핵심 전략

* 먼저 WHERE로 줄이고 JOIN
* JOIN 컬럼 인덱스 필수
* 불필요한 JOIN 제거

---

## 6. 서브쿼리 vs JOIN vs EXISTS

상황별 선택이 중요합니다.

| 상황             | 추천   |
| ---------------- | ------ |
| 존재 여부 확인   | EXISTS |
| 작은 목록 비교   | IN     |
| 데이터 함께 조회 | JOIN   |

### 예시

```sql
WHERE EXISTS (
  SELECT 1
  FROM order_items oi
  WHERE oi.order_id = o.order_id
)
```

---

## 7. ORDER BY / GROUP BY 최소화

정렬은 비용이 큽니다.

### 최적화 방법

* 꼭 필요한 경우만 사용
* 인덱스로 정렬 대체
* 먼저 WHERE로 줄이기

---

## 8. LIMIT OFFSET 대신 키셋 페이징

### ❌

```sql
LIMIT 1000, 20
```

### ✅

```sql
WHERE order_id > :last_id
ORDER BY order_id
LIMIT 20
```

👉 뒤 페이지 갈수록 성능 차이 큼

---

## 9. OR 대신 IN 사용 고려

### ❌

```sql
WHERE status = 'READY' OR status = 'PAID'
```

### ✅

```sql
WHERE status IN ('READY', 'PAID')
```

---

## 10. 컬럼에 함수 사용 금지

### ❌

```sql
WHERE TRIM(code) = 'A100'
```

### ❌

```sql
WHERE amount * 1.1 > 100
```

👉 인덱스 사용 불가

---

## 11. 통계 정보와 테이블 구조 점검

옵티마이저는 통계를 기반으로 동작합니다.

체크:

* 통계 최신 여부
* 데이터 타입 적절성
* 문자열 길이
* NULL 남용 여부

---

## 12. 반복 처리 대신 배치 처리

### ❌

* 반복문으로 1건씩 처리

### ✅

```sql
UPDATE orders
SET status = 'EXPIRED'
WHERE status = 'READY'
  AND expire_at < NOW();
```

👉 SQL은 집합 처리 언어입니다

---

## 13. 느린 쿼리 로그 분석

중요한 것은 체감이 아니라 데이터입니다.

확인:

* 실행 시간
* 호출 횟수
* 평균/최대 시간

👉 **0.1초 쿼리 1만 번 = 더 큰 문제**

---

## 실무 체크리스트

빠르게 점검하려면:

1. 실행 계획 확인
2. WHERE 조건 최적화
3. 인덱스 점검
4. SELECT * 제거
5. 불필요한 JOIN 제거
6. 함수 사용 여부 확인
7. 페이징 방식 개선

---

## 개선 예시

### ❌ 기존

```sql
SELECT *
FROM orders
WHERE YEAR(created_at) = 2026
  AND status = 'PAID'
ORDER BY created_at DESC;
```

### ✅ 개선

```sql
SELECT order_id, user_id, created_at, total_price
FROM orders
WHERE created_at >= '2026-01-01'
  AND created_at < '2027-01-01'
  AND status = 'PAID'
ORDER BY created_at DESC;
```

👉 추천 인덱스:

```sql
(status, created_at)
```

---

## 마무리

SQL 최적화는 복잡해 보이지만 핵심은 단순합니다.

> **"인덱스를 잘 만들고, 읽는 데이터를 줄이고, 실행 계획으로 검증하라"**

이 3가지만 잘 지켜도 대부분의 성능 문제는 해결됩니다.

---
