---
title: "SQL WHERE IN vs 범위 조건(a < x AND x < b) 성능 차이 완전 정리"
date: 2026-03-19 00:00:00 +0900
categories: sql
tags: [sql, where, where in, database, performance, index, range scan, where in 성능, 인덱스 seek,]
toc: true
toc_sticky: true
---

SQL 성능 튜닝을 하다 보면 자주 마주치는 질문이 있습니다.

```sql
WHERE x IN (101, 105, 109)
```

와

```sql
WHERE 100 < x AND x < 110
```

중 어떤 방식이 더 빠를까?

겉으로 보기에는 **둘 다 같은 행 수를 반환할 수 있지만**, 내부 실행 방식은 꽤 다릅니다.

핵심은 다음입니다.

* `IN` → 여러 개의 **점(point) 조회**
* `range 조건` → **연속 구간(interval) 조회**

즉, **같은 결과 행 수라도 인덱스 접근 방식 자체가 다르기 때문에 성능 차이가 발생할 수 있습니다.**

---

## 1. WHERE IN의 동작 방식

예를 들어:

```sql
WHERE x IN (101, 105, 109)
```

인덱스가 있다면 DB는 보통 각 값을 개별적으로 찾습니다.

실제로는 다음과 비슷하게 동작합니다.

```text
101 찾기
105 찾기
109 찾기
```

B-Tree 인덱스에서는 매번:

```text
root → branch → leaf
```

를 반복합니다.

즉:

* 인덱스 seek 여러 번 발생
* 값 개수만큼 탐색 반복
* 랜덤 접근 성격이 강함

---

## 2. 범위 조건의 동작 방식

예:

```sql
WHERE 100 < x AND x < 110
```

이 경우는 보통:

1. 시작 위치(101)를 한 번 찾고
2. leaf node를 연속적으로 스캔합니다.

즉:

```text
101 찾기
102 검사
103 검사
104 검사
105 검사
...
109 검사
```

즉:

* seek 1회
* 이후 연속 scan

---

## 3. 같은 결과 행 수여도 비용이 달라지는 이유

예를 들어 결과가 모두 3건이라고 가정해도 차이가 생깁니다.

### IN 조건

```sql
WHERE x IN (101, 105, 109)
```

읽는 위치:

```text
101 page
105 page
109 page
```

필요한 값만 직접 찾습니다.

---

### range 조건

```sql
WHERE 100 < x AND x < 110
```

중간 값도 검사합니다.

```text
101
102 확인
103 확인
104 확인
105
106 확인
107 확인
108 확인
109
```

즉:

**결과는 3건이어도 내부적으로 더 많은 key를 읽을 수 있습니다.**

---

## 4. CPU cycle 관점 비교

### WHERE IN

값 N개면 대략:

```text
N × tree depth
```

예를 들어 인덱스 depth가 3이면:

값 3개 → 약 9단계 탐색

---

### range 조건

```text
1 × tree depth + leaf scan
```

즉:

* 시작점 탐색 1번
* 이후 연속 검사

---

## 5. 언제 WHERE IN이 유리한가

값이 띄엄띄엄 떨어져 있을 때입니다.

예:

```sql
WHERE x IN (1000, 5000, 9000)
```

필요한 값 3개만 정확히 찾습니다.

반면 range로 쓰면:

```sql
WHERE 1000 <= x AND x <= 9000
```

중간 구간 전체를 검사할 수 있습니다.

즉:

**불필요한 scan이 매우 많아질 수 있습니다.**

---

## 6. 언제 range 조건이 유리한가

값이 연속적일 때입니다.

예:

```sql
WHERE x IN (1001,1002,1003,1004,1005)
```

이 경우는 사실상 연속 구간입니다.

range로 바꾸면:

```sql
WHERE 1000 < x AND x < 1006
```

더 효율적입니다.

이유:

* seek 5번 대신 seek 1번

---

## 7. 인덱스 page locality 차이

실무에서 매우 중요한 부분입니다.

### IN

```text
page1 → page8 → page15
```

page jump 발생 가능

즉:

* cache miss 가능성 증가

---

### range

```text
page1 → page2 → page3
```

연속 읽기

즉:

* cache locality 우수
* 디스크/메모리 효율 좋음

---

## 8. 옵티마이저가 내부적으로 바꾸는 경우도 있음

DBMS는 경우에 따라:

```sql
IN (1,2,3,4,5)
```

를 내부적으로 작은 range처럼 처리하기도 합니다.

특히:

* MySQL
* PostgreSQL
* MSSQL

모두 값 개수와 분포를 보고 최적화합니다.

하지만 기본 개념은 그대로입니다.

---

## 9. 실무 판단 기준

### 값이 떨어져 있으면

```sql
WHERE IN
```

유리

---

### 값이 붙어 있으면

```sql
WHERE a < x AND x < b
```

유리

---

## 10. 핵심 공식

### IN 비용

```text
seek 횟수 × index depth
```

### range 비용

```text
seek 1회 + scan span
```

즉:

**행 수보다 span 길이가 더 중요합니다.**

---

## 11. 한 줄 결론

> 같은 row 수라도
> `IN` 은 필요한 값만 점 탐색하고
> `range` 는 구간 전체를 훑기 때문에
> 값 분포가 sparse 하면 IN이 유리하고, 연속적이면 range가 유리합니다.

---

## 12. 실무 팁

EXPLAIN으로 확인하면 바로 보입니다.

예:

```sql
EXPLAIN SELECT * FROM table WHERE x IN (101,105,109);
```

vs

```sql
EXPLAIN SELECT * FROM table WHERE 100 < x AND x < 110;
```

여기서 확인할 포인트:

* index seek 횟수
* range scan 여부
* rows estimate

---

## 마무리

SQL 튜닝에서 중요한 건 단순히 문법이 아니라 **데이터 분포와 인덱스 구조를 함께 보는 것**입니다.

겉으로 같은 결과라도 내부 비용은 크게 달라질 수 있습니다.

---
