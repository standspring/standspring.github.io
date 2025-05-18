---
title: "GoogleTest 설치부터 첫 테스트까지"
date: 2025-05-15
category: C
tags: [C, googletest, gtest, unittest]
---

# GoogleTest 설치부터 첫 테스트까지

C++ 프로젝트에서 단위 테스트는 코드의 안정성과 유지보수를 위한 필수 도구입니다. 이 글에서는 GoogleTest(GTest)를 설치하고 간단한 테스트 코드를 작성하여 실행하는 방법까지 단계별로 소개합니다.

---

## 📦 1. GoogleTest 설치 방법

GoogleTest는 GitHub에 공개된 오픈소스 라이브러리입니다. 설치 방법은 크게 두 가지가 있습니다:

### 🔹 1-1. CMake로 FetchContent 사용하기 (권장)

```cmake
cmake_minimum_required(VERSION 3.14)
project(MyProject)

include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/heads/main.zip
)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(MyTest main.cpp)
target_link_libraries(MyTest gtest gtest_main)
include(GoogleTest)

gtest_discover_tests(MyTest)
```

### 🔹 1-2. Git Submodule로 추가하기

```bash
git submodule add https://github.com/google/googletest.git
cd googletest
mkdir build && cd build
cmake .. && make
```

이후 `add_subdirectory(googletest)`로 프로젝트에 포함시킵니다.

---

## 🧪 2. 첫 테스트 코드 작성하기

`main.cpp` 파일에 아래와 같은 간단한 테스트 코드를 작성해 봅시다.

```cpp
#include <gtest/gtest.h>

int Add(int a, int b) {
    return a + b;
}

TEST(MathTest, Addition) {
    EXPECT_EQ(Add(2, 3), 5);
    EXPECT_NE(Add(2, 2), 5);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

* `TEST` 매크로는 새로운 테스트 케이스를 정의합니다.
* `EXPECT_EQ`, `EXPECT_NE` 등은 검증 함수입니다.

---

## ▶️ 3. 테스트 실행하기

빌드 후 실행 파일을 실행하면 다음과 같은 출력이 나옵니다:

```bash
[==========] Running 1 test from 1 test suite.
[----------] Global test environment set-up.
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[----------] Global test environment tear-down
[==========] 1 test from 1 test suite ran. (0 ms total)
[  PASSED  ] 1 test.
```

---

## 📌 4. 자주 쓰는 GoogleTest 매크로 정리

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

## 🧱 5. Test Fixture (테스트 고정 장치) 사용법

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

## 💡 마무리

이제 GoogleTest를 설치하고, 테스트를 작성하고 실행하는 전 과정을 경험해 보았습니다. `EXPECT`, `ASSERT` 매크로를 활용해 다양한 조건을 검증하고, `Test Fixture`로 테스트의 품질을 높일 수 있습니다.
