---
title: "MariaDB SQL 기본 사용법 정리 (CREATE, INSERT, SELECT 완전 기초)"
date: 2026-03-26
categories: [Database, SQL]
tags: [MariaDB, SQL, DB, 입문]
---

MariaDB는 MySQL과 호환되는 대표적인 오픈소스 관계형 데이터베이스입니다.
이 글에서는 가장 기본이 되는 SQL 문법을 정리합니다.

- CREATE TABLE
- INSERT
- SELECT
- UPDATE
- DELETE

---

## 1. 데이터베이스 생성 및 선택

```sql
-- 데이터베이스 생성
CREATE DATABASE test_db;

-- 데이터베이스 선택
USE test_db;
````

---

## 2. 테이블 생성 (CREATE TABLE)

### 기본 문법

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 설명

| 컬럼       | 설명                |
| ---------- | ------------------- |
| id         | 자동 증가 기본 키   |
| name       | 문자열 (최대 50자)  |
| age        | 정수                |
| created_at | 생성 시간 자동 기록 |

---

## 3. 데이터 삽입 (INSERT)

### 단일 데이터 삽입

```sql
INSERT INTO users (name, age)
VALUES ('홍길동', 30);
```

### 여러 데이터 삽입

```sql
INSERT INTO users (name, age)
VALUES
('김철수', 25),
('이영희', 28);
```

---

## 4. 데이터 조회 (SELECT)

### 전체 조회

```sql
SELECT * FROM users;
```

### 특정 컬럼 조회

```sql
SELECT name, age FROM users;
```

### 조건 조회 (WHERE)

```sql
SELECT * FROM users
WHERE age >= 30;
```

### 정렬 (ORDER BY)

```sql
SELECT * FROM users
ORDER BY age DESC;
```

### 개수 제한 (LIMIT)

```sql
SELECT * FROM users
LIMIT 5;
```

---

## 5. 데이터 수정 (UPDATE)

```sql
UPDATE users
SET age = 31
WHERE name = '홍길동';
```

⚠️ `WHERE` 조건 없이 실행하면 모든 데이터가 변경됩니다.

---

## 6. 데이터 삭제 (DELETE)

```sql
DELETE FROM users
WHERE id = 1;
```

⚠️ `WHERE` 없이 실행하면 전체 데이터 삭제됩니다.

---

## 7. 테이블 삭제 (DROP TABLE)

```sql
DROP TABLE users;
```

---

## 8. 자주 쓰는 조건들

### 비교 연산

```sql
WHERE age > 20
WHERE age BETWEEN 20 AND 30
```

### IN 사용

```sql
WHERE age IN (20, 25, 30);
```

### LIKE (문자 검색)

```sql
WHERE name LIKE '김%';   -- 김으로 시작
WHERE name LIKE '%수';   -- 수로 끝남
```

---

## 9. 기본 흐름 (실무 패턴)

```text
1. SELECT (조회)
2. INSERT (데이터 추가)
3. UPDATE (데이터 수정)
4. DELETE (데이터 삭제)
```

---

## 10. 실전 예제

```sql
-- 테이블 생성
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price INT
);

-- 데이터 삽입
INSERT INTO products (name, price)
VALUES ('노트북', 1000000);

-- 조회
SELECT * FROM products;

-- 수정
UPDATE products SET price = 900000 WHERE id = 1;

-- 삭제
DELETE FROM products WHERE id = 1;
```

---

## 마무리

MariaDB에서 SQL의 핵심은 다음 4가지입니다:

* CREATE → 구조 만들기
* INSERT → 데이터 넣기
* SELECT → 데이터 조회
* UPDATE / DELETE → 데이터 변경

이 4가지만 제대로 이해해도 대부분의 DB 작업을 수행할 수 있습니다.

---
