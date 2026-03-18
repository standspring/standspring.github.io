---
title: "GoogleTest: 실수하기 쉬운 GTest 코드 패턴"
date: 2025-05-21
category: C
tags: [C, c++, googletest, gtest, unittest, pattern, test-smell, refactoring]
---


# 🔁 테스트 코드 리팩토링: 실수하기 쉬운 GTest 코드 패턴

## ⚠️ 문제 1: 테스트 중복 코드

여러 테스트 함수에 같은 초기화 코드가 반복된다면 `Test Fixture`를 활용해 중복 제거하세요.

🔴 나쁜 예:

```cpp
TEST(MyTest, Case1) {
    std::vector<int> v = {1, 2, 3};
    EXPECT_EQ(v.size(), 3);
}

TEST(MyTest, Case2) {
    std::vector<int> v = {1, 2, 3};
    EXPECT_EQ(v[1], 2);
}
```

✅ 좋은 예:

```cpp
class MyFixture : public ::testing::Test {
protected:
    void SetUp() override {
        v = {1, 2, 3};
    }
    std::vector<int> v;
};

TEST_F(MyFixture, Case1) {
    EXPECT_EQ(v.size(), 3);
}

TEST_F(MyFixture, Case2) {
    EXPECT_EQ(v[1], 2);
}
```

---

## ⚠️ 문제 2: 의미 없는 테스트 이름

의도를 알 수 없는 테스트 이름은 유지보수에 방해됩니다.

🔴 나쁜 예: `TEST(MyTest, Test1)`

✅ 좋은 예:

```cpp
TEST(StringUtil_ToUpper_WhenLowercase, ShouldReturnUppercase) {
    EXPECT_EQ(ToUpper("abc"), "ABC");
}
```

---

## ⚠️ 문제 3: 복잡한 테스트 로직

테스트는 단순하고 명확해야 합니다. 너무 많은 조건을 한 테스트에 넣지 마세요.

🔴 나쁜 예:

```cpp
TEST(CalculatorTest, ComplexCase) {
    Calculator c;
    c.Input("1+2");
    EXPECT_EQ(c.Result(), 3);
    c.Input("5-1");
    EXPECT_EQ(c.Result(), 4);
    c.Input("2*3");
    EXPECT_EQ(c.Result(), 6);
}
```

✅ 좋은 예:

```cpp
TEST(CalculatorTest, Add) {
    Calculator c;
    c.Input("1+2");
    EXPECT_EQ(c.Result(), 3);
}

TEST(CalculatorTest, Subtract) {
    Calculator c;
    c.Input("5-1");
    EXPECT_EQ(c.Result(), 4);
}
```

---
