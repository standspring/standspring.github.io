---
title: "GoogleTest: 실무에 바로 쓰는 GTest & GMock 가이드"
date: 2025-05-19
category: C
tags: [C, googletest, gtest, unittest, mock, expect_call]
---

# GoogleTest: 실무에 바로 쓰는 GTest & GMock 가이드

단위 테스트는 코드 품질과 유지보수성 확보에 필수입니다. 이 글에서는 실무에서 자주 쓰는 GoogleTest 매크로와 Test Fixture, Mock 사용법까지 중급 테스트 작성법을 다룹니다.

---

## 📌 1. 자주 쓰는 GoogleTest 매크로 정리

GoogleTest는 다양한 매크로를 통해 유연하고 표현력 있는 테스트를 지원합니다. 자주 쓰이는 매크로를 정리해보면 다음과 같습니다:

| 매크로                         | 설명                                 |
| ------------------------------ | ------------------------------------ |
| `EXPECT_EQ(val1, val2)`        | 두 값이 같은지 확인 (Equal)          |
| `EXPECT_NE(val1, val2)`        | 두 값이 다른지 확인 (Not Equal)      |
| `EXPECT_LT(val1, val2)`        | val1 < val2 확인 (Less Than)         |
| `EXPECT_LE(val1, val2)`        | val1 <= val2 확인 (Less or Equal)    |
| `EXPECT_GT(val1, val2)`        | val1 > val2 확인 (Greater Than)      |
| `EXPECT_GE(val1, val2)`        | val1 >= val2 확인 (Greater or Equal) |
| `EXPECT_TRUE(condition)`       | 조건이 true인지 확인                 |
| `EXPECT_FALSE(condition)`      | 조건이 false인지 확인                |
| `EXPECT_THROW(stmt, exc_type)` | 예외 발생 여부 확인                  |
| `EXPECT_NO_THROW(stmt)`        | 예외가 발생하지 않아야 함            |
| `EXPECT_ANY_THROW(stmt)`       | 어떤 예외든 발생해야 함              |

> ⚠️ `EXPECT_*`는 실패해도 다음 테스트로 진행되며, `ASSERT_*`는 실패 시 테스트를 종료합니다.

---

## 🧱 2. Test Fixture (테스트 고정 장치) 사용법

`Test Fixture`는 공통된 설정이 필요한 테스트 케이스를 위한 구조입니다. 테스트 실행 전후에 필요한 초기화/해제를 깔끔하게 관리할 수 있습니다.

### 🔸 기본 구조

```cpp
class MyFixture : public ::testing::Test {
protected:
    void SetUp() override {
        // 테스트 전에 실행되는 코드
    }

    void TearDown() override {
        // 테스트 후에 실행되는 코드
    }

    int value = 0;
};

TEST_F(MyFixture, SampleTest) {
    value = 42;
    EXPECT_EQ(value, 42);
}
```

* `TEST_F`는 Test Fixture에서 정의된 클래스와 연동됩니다.
* `SetUp()`과 `TearDown()`을 통해 테스트 전후의 상태를 설정할 수 있습니다.

### 🔸 예제: 벡터 테스트

```cpp
#include <gtest/gtest.h>
#include <vector>

class VectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        vec.push_back(10);
        vec.push_back(20);
    }

    std::vector<int> vec;
};

TEST_F(VectorTest, SizeCheck) {
    EXPECT_EQ(vec.size(), 2);
}

TEST_F(VectorTest, ValueCheck) {
    EXPECT_EQ(vec[0], 10);
    EXPECT_EQ(vec[1], 20);
}
```

---

## 🤖 3. Mocking을 위한 GoogleMock 사용법

GoogleMock은 가상 객체(Mock Object)를 만들어 함수 호출을 감시하고, 호출 횟수나 인자를 검증할 수 있도록 해줍니다.

### 🔹 Mock 클래스 정의

```cpp
class Printer {
public:
    virtual ~Printer() = default;
    virtual void Print(const std::string& msg) = 0;
};

class MockPrinter : public Printer {
public:
    MOCK_METHOD(void, Print, (const std::string& msg), (override));
};
```

### 🔹 호출 검증 예시

```cpp
void SendMessage(Printer* printer) {
    printer->Print("Hello, world!");
}

TEST(MockTest, ShouldCallPrintOnce) {
    MockPrinter mock;
    EXPECT_CALL(mock, Print("Hello, world!")).Times(1);

    SendMessage(&mock);
}
```

* `MOCK_METHOD`로 함수 mocking
* `EXPECT_CALL(...).Times(n)`으로 호출 횟수 검증
* `.With(...)`, `.WillOnce(...)` 등으로 인자 값이나 리턴값을 설정 가능

---

## 🛠️ 4. 실무에서 자주 쓰는 GTest 패턴

### ✔️ private 함수 테스트

* 테스트 대상 클래스를 `friend class`로 설정하거나, 헤더를 별도 노출하여 테스트 코드에서 접근 가능하게 처리

```cpp
class MyClass {
private:
    int Secret() { return 42; }
    friend class MyClassTest;
};
```

### ✔️ 공통 테스트 유틸 함수 사용

* 반복되는 검증 로직은 함수로 분리하여 가독성과 재사용성 확보

```cpp
void ExpectEven(int n) {
    EXPECT_EQ(n % 2, 0);
}
```

### ✔️ 테스트 이름 구조화

* 테스트 이름을 `ClassName_MethodName_Condition` 형식으로 작성하여 직관적으로 이해할 수 있게 함

```cpp
TEST(Math_Addition_PositiveNumbers, ShouldReturnSum) {
    EXPECT_EQ(Add(1, 2), 3);
}
```

### ✔️ 다양한 경계 조건과 예외 케이스 테스트

* NULL, 빈 벡터, 최대값/최소값 등 경계조건을 항상 커버하도록 작성

```cpp
TEST(VectorTest, HandlesEmptyInput) {
    std::vector<int> empty;
    EXPECT_TRUE(empty.empty());
}
```
