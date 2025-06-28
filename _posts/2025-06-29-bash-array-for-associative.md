---
title: "Bash에서 배열(Array)과 연관 배열(Associative Array) 반복문 사용법"
date: 2025-06-29
category: bash
tags: [bash, array, for, associative, associativearray]
---

# Bash에서 배열(Array)과 연관 배열(Associative Array) 반복문 사용법

Bash에서는 일반 배열(`indexed array`)과 연관 배열(`associative array`)을 지원합니다. 이 글에서는 두 종류의 배열을 `for` 루프를 통해 순회하는 방법을 예제와 함께 자세히 소개합니다.

## 1. 일반 배열 (Indexed Array)

### 배열 선언 및 초기화

```bash
fruits=("apple" "banana" "cherry")
```

### 예제 1: 인덱스 없이 값 순회

```bash
for fruit in "${fruits[@]}"; do
  echo "I like $fruit"
done
```

**출력:**

```
I like apple  
I like banana  
I like cherry
```

### 예제 2: 인덱스와 값 모두 출력

```bash
for i in "${!fruits[@]}"; do
  echo "Index $i: ${fruits[$i]}"
done
```

**출력:**

```
Index 0: apple  
Index 1: banana  
Index 2: cherry
```

`"${!array[@]}"` 문법은 배열의 인덱스를 반환합니다.

---

## 2. 연관 배열 (Associative Array)

Bash 4.0 이상에서 사용 가능하므로, 버전을 확인하세요.

```bash
bash --version
```

### 배열 선언 및 초기화

```bash
declare -A capitals
capitals=(
  [Korea]="Seoul"
  [Japan]="Tokyo"
  [France]="Paris"
)
```

### 예제 1: 키-값 순회

```bash
for country in "${!capitals[@]}"; do
  echo "The capital of $country is ${capitals[$country]}"
done
```

**출력:**

```
The capital of Korea is Seoul  
The capital of Japan is Tokyo  
The capital of France is Paris
```

### 예제 2: 값만 순회

```bash
for city in "${capitals[@]}"; do
  echo "Capital city: $city"
done
```

---

## 3. 배열 순회 시 주의사항

- 항상 `"${array[@]}"` 또는 `"${!array[@]}"` 와 같이 **쌍따옴표로 감싸야** 공백이 포함된 값도 올바르게 처리됩니다.
- associative array는 `declare -A`로 반드시 선언해주어야 합니다.
- associative array는 숫자뿐 아니라 문자열 키도 허용됩니다.

---

## 4. 응용 예제: 사용자 목록과 직급 출력

```bash
declare -A users
users=(
  [alice]="Manager"
  [bob]="Developer"
  [carol]="Designer"
)

for name in "${!users[@]}"; do
  echo "$name is a ${users[$name]}"
done
```

**출력:**

```
alice is a Manager  
bob is a Developer  
carol is a Designer
```

---

## 마무리

Bash에서 배열을 사용하는 것은 스크립트의 유연성과 가독성을 높이는 데 매우 유용합니다. 특히, 연관 배열은 데이터를 키-값 쌍으로 다룰 수 있어 복잡한 데이터 구조를 단순하게 처리할 수 있습니다. `for` 루프와 함께 활용하면 반복 작업을 효율적으로 처리할 수 있습니다.

```bash
# bash version >= 4.0 인지 확인하는 것도 잊지 마세요!
```
