---
title: "Mocking을 위한 GoogleMock 사용법"
date: 2025-05-28
category: C
tags: [C, c++, googletest, gtest, unittest, mocking, mock, googlemock, mock-object]
---

# Mocking을 위한 GoogleMock 사용법

GoogleMock은 GoogleTest에 포함된 강력한 Mocking 도구로, 객체의 메서드 호출 여부, 호출 횟수, 인자 값 등을 쉽게 검증할 수 있도록 도와줍니다. 이 글에서는 GoogleMock을 사용하여 함수 호출을 검증하는 기본 사용법을 단계별로 소개하고 예시 코드도 함께 제공합니다.

---

## 🤖 1. Mock 클래스 정의

테스트 대상 인터페이스 또는 추상 클래스를 상속받아 `MOCK_METHOD`를 이용해 Mock 클래스를 만듭니다.

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

* `MOCK_METHOD(리턴형, 함수명, (인자 목록), (옵션))`
* override 키워드를 사용하여 기존 가상 함수 구현을 덮어씀

---

## 📞 2. 호출 여부 테스트하기

Mock 객체를 테스트 함수에 전달하고, `EXPECT_CALL`로 호출 여부와 인자 값을 검증합니다.

```cpp
void SendMessage(Printer* printer) {
    printer->Print("Hello, world!");
}

TEST(MockTest, ShouldCallPrintOnce) {
    MockPrinter mock;
    EXPECT_CALL(mock, Print("Hello, world!"))
        .Times(1);

    SendMessage(&mock);
}
```

* `EXPECT_CALL`은 지정된 조건의 함수가 **정확히 호출**되었는지 검사합니다.
* `.Times(n)`으로 호출 횟수 제한 가능

---

## 🔧 3. 다양한 호출 제어 옵션

GoogleMock은 다양한 조건과 행동을 지정할 수 있습니다.

| 설정                     | 설명                          |
| ------------------------ | ----------------------------- |
| `.Times(n)`              | 호출 횟수 기대값 지정         |
| `.WillOnce(Return(val))` | 호출 시 특정 값 리턴          |
| `.With(Args<...>(...))`  | 특정 인자 조합으로만 반응     |
| `.WillRepeatedly(...)`   | 여러 번 호출될 때의 기본 동작 |

```cpp
class Calculator {
public:
    virtual ~Calculator() = default;
    virtual int Add(int a, int b) = 0;
};

class MockCalculator : public Calculator {
public:
    MOCK_METHOD(int, Add, (int a, int b), (override));
};

TEST(MockCalculatorTest, ReturnCustomValue) {
    MockCalculator mock;

    EXPECT_CALL(mock, Add(1, 2))
        .WillOnce(::testing::Return(100));

    EXPECT_EQ(mock.Add(1, 2), 100);
}
```

---

## 🧪 4. 테스트 대상이 의존하는 객체를 격리하고 검증하기

Mock을 활용하면 테스트 대상 함수의 외부 의존성을 격리하고, 순수한 유닛 테스트 환경을 구축할 수 있습니다. 예를 들어 네트워크나 파일 입출력처럼 테스트하기 어려운 요소들을 Mock으로 대체할 수 있습니다.

```cpp
class Network {
public:
    virtual ~Network() = default;
    virtual bool Connect(const std::string& host) = 0;
};

class MockNetwork : public Network {
public:
    MOCK_METHOD(bool, Connect, (const std::string& host), (override));
};

bool InitConnection(Network* network) {
    return network->Connect("server.com");
}

TEST(NetworkTest, ShouldTryToConnect) {
    MockNetwork mock;
    EXPECT_CALL(mock, Connect("server.com"))
        .Times(1)
        .WillOnce(::testing::Return(true));

    EXPECT_TRUE(InitConnection(&mock));
}
```
