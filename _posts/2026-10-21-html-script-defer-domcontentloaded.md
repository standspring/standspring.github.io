---
title: "HTML script의 defer·async 차이와 DOMContentLoaded: jQuery ready 대체하기"
description: "HTML 파싱과 script 실행 순서를 바탕으로 defer·async·module의 차이를 설명하고, jQuery document ready를 DOMContentLoaded와 readyState로 바꾸는 방법을 실행 예제와 함께 정리합니다."
date: 2026-10-21 00:00:00 +0900
categories: [Development, Web]
tags: [HTML, JavaScript, script, defer, async, DOMContentLoaded, jQuery]
toc: true
toc_sticky: true
---

# HTML script의 defer·async 차이와 DOMContentLoaded: jQuery ready 대체하기

## 들어가며

HTML에 버튼을 만들고 JavaScript로 클릭 이벤트를 등록했는데 `null` 오류가 발생한다. 검색해 보면 스크립트를 맨 아래로 옮기거나, `defer`를 붙이거나, `$(document).ready()`로 감싸라는 해결책이 나온다. 모두 실행 시점과 관련 있지만, 보장하는 범위는 다르다.

**DOM을 사용하는 외부 스크립트는 `<script defer src="...">`로 불러오는 구성을 먼저 검토하자.** HTML 파싱이 끝난 뒤 실행하므로, 초기 HTML의 요소를 다루기 위해 파일 전체를 다시 ready 이벤트로 감쌀 필요가 없는 경우가 많다. 이벤트로 DOM 준비를 기다려야 한다면 브라우저 표준 API인 `DOMContentLoaded`를 사용하면 된다.

다만 jQuery `ready`와 `DOMContentLoaded`는 완전히 같은 API가 아니다. 특히 **이벤트가 발생한 뒤에 코드를 등록하는 경우**에는 동작이 달라진다. 이 차이까지 이해해야 기존 코드를 안전하게 바꿀 수 있다.

이 글의 실행 순서 설명은 HTML에 처음부터 작성되어 있고 파서가 처리하는 스크립트를 기준으로 한다. JavaScript로 나중에 추가하는 스크립트는 별도 규칙이 있으므로 뒤에서 구분한다.

![일반 script는 다운로드와 실행 동안 HTML 파싱을 멈추고, async는 준비되면 실행하며, defer는 파싱 완료 후 실행한 뒤 DOMContentLoaded가 발생하는 순서를 비교한 그림](/assets/img/2026-10-21-html-script-defer-domcontentloaded.svg)

*HTML 파싱·스크립트 다운로드·실행 시점을 구분한 개념도다. 막대 길이는 성능 측정값이 아니며, async 행은 DOMContentLoaded 전에 실행되는 경우를 보여 준다. 실제 async 실행은 이벤트 이후일 수도 있다.*

## 문제 상황

다음 HTML을 실행해 보자.

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>실행 시점 문제</title>
  <script>
    const button = document.querySelector("#save");
    console.log(button);
    button.addEventListener("click", () => console.log("저장"));
  </script>
</head>
<body>
  <button id="save" type="button">저장</button>
</body>
</html>
```

브라우저 콘솔에서는 다음과 같은 오류를 확인할 수 있다. 오류의 세부 표기는 브라우저에 따라 다를 수 있다.

```text
null
Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
```

버튼이 HTML 파일에 없어서가 아니다. **스크립트를 실행하는 순간에는 브라우저가 아직 버튼 부분을 파싱하지 않았기 때문**이다. 나중에 개발자 도구에서 버튼이 보인다는 사실과 오류 발생 당시 DOM에 버튼이 있었다는 것은 다르다.

## 원인 분석

### 1. HTML 소스와 DOM은 다르다

브라우저는 HTML을 읽어 요소 노드로 구성된 DOM(Document Object Model)을 만든다. JavaScript의 `querySelector()`는 이 DOM을 조회한다.

파일 전체가 준비되어 있어도 DOM 전체가 한 번에 만들어지는 것은 아니다. 파서가 위에서 아래로 처리하는 도중 일반적인 인라인 `<script>`를 만나면, 그 지점에서 코드를 실행한다. 아직 파싱하지 않은 아래쪽 버튼은 조회할 수 없다.

외부 파일을 불러오는 일반적인 클래식 스크립트도 주의해야 한다.

```html
<script src="app.js"></script>
```

파서는 해당 스크립트를 실행할 수 있을 때까지 기다리고, 실행을 마친 뒤 나머지 HTML을 처리한다. 파일 다운로드가 오래 걸리면 그만큼 DOM 생성도 늦어질 수 있다. 브라우저가 미리 리소스를 발견하고 가져오는 최적화와는 별개로, **파서의 진행을 막는다는 성질**이 핵심이다.

여기서 `src`는 외부 파일의 주소다. `src` 없이 태그 안에 작성한 코드는 인라인 스크립트라고 부른다. 이 글에서 **클래식 스크립트**는 `type`을 생략한 일반 JavaScript 스크립트를 가리키며, `type="module"`로 선언한 모듈 스크립트와 구분한다. 일반 JavaScript에 `type="text/javascript"`를 따로 붙일 필요는 없다.

### 2. 다운로드 시점과 실행 시점을 나누어 보자

스크립트 로딩에는 적어도 두 가지 질문이 있다.

- **가져오기:** HTML 파싱과 함께 파일을 다운로드할 수 있는가?
- **실행:** 파일이 준비되면 바로 실행하는가, 파싱이 끝날 때까지 기다리는가?

`async`와 `defer`는 둘 다 외부 스크립트를 HTML 파싱과 병행해서 가져올 수 있게 한다. 차이는 실행 시점과 순서에 있다. 이 규칙은 [WHATWG HTML 표준의 script 처리 방식](https://html.spec.whatwg.org/multipage/scripting.html#attr-script-async)에 정의되어 있다.

### 3. defer: DOM 생성 후, 작성한 순서대로 실행한다

```html
<head>
  <script defer src="library.js"></script>
  <script defer src="app.js"></script>
</head>
```

외부 클래식 스크립트에 `defer`를 붙이면 다음 특성이 생긴다.

1. 파일을 가져오는 동안 HTML 파싱을 계속한다.
2. HTML 파싱이 끝난 뒤 실행한다. 파일이 아직 준비되지 않았다면 기다린다.
3. 같은 방식으로 선언한 `defer` 스크립트끼리는 문서에 작성한 순서대로 실행한다.
4. 이 스크립트들의 실행을 처리한 뒤 `DOMContentLoaded`가 발생한다.

따라서 위 예제에서는 `app.js`가 먼저 다운로드되어도 `library.js` 다음에 실행된다. 초기 HTML의 버튼도 이미 DOM에 있다. [MDN의 defer 설명](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script#defer)에서도 문서 순서와 `DOMContentLoaded` 이전 실행을 확인할 수 있다.

여기서 순서 보장은 **동기적인 코드 실행 순서**다. `library.js`가 `fetch()`로 요청을 시작했다고 해서 응답 처리까지 끝난 다음 `app.js`를 실행하는 것은 아니다. 비동기 작업의 완료는 Promise나 `await` 등으로 별도 연결해야 한다.

### 4. async: 파일이 준비되면 가능한 시점에 실행한다

```html
<script async src="analytics.js"></script>
```

`async`는 HTML 파싱과 병행해서 파일을 가져오고, 파일이 준비되면 가능한 시점에 실행한다. HTML 파싱이 끝나기 전에 실행될 수 있으며, **여러 `async` 스크립트의 문서상 순서를 보장하지 않는다.**

```html
<!-- app.js가 library.js를 사용한다면 안전하지 않은 구성이다. -->
<script async src="library.js"></script>
<script async src="app.js"></script>
```

캐시가 있는 환경에서는 우연히 잘 동작하더라도, 네트워크 상황이 바뀌면 `app.js`가 먼저 실행될 수 있다. 독립적으로 실행할 수 있는 통계 수집 코드 등에서 검토할 수 있지만, DOM이나 다른 라이브러리가 필요하다면 준비 조건을 직접 관리해야 한다.

또한 `async`는 JavaScript를 별도 스레드에서 실행한다는 뜻이 아니다. 일반적인 페이지 스크립트의 실행은 메인 스레드를 사용하므로, 파싱 도중 실행되면 그동안 파서 진행을 방해할 수 있다.

### 5. 일반 script·defer·async·module 비교

아래 표는 처음부터 HTML에 선언한 스크립트를 기준으로 한다. `module`의 비동기 평가에 관한 예외는 이어지는 설명을 함께 읽자.

| 작성 방식 | HTML 파싱 중 가져오기 | 실행 시점 | 다른 파일과의 순서 | DOMContentLoaded와의 관계 |
|---|---|---|---|---|
| `<script src="a.js">` | 해당 지점에서 파서는 대기 | 준비되면 그 위치에서 실행 | 일반 클래식 스크립트끼리 문서 순서 | 파싱·실행이 끝나야 발생 가능 |
| `<script defer src="a.js">` | 파싱과 병행 | 파싱 완료 후 | `defer` 클래식 스크립트끼리 문서 순서 | 실행 처리를 기다림 |
| `<script async src="a.js">` | 파싱과 병행 | 준비되는 대로 | 문서 순서 보장 없음 | 해당 파일의 로딩을 기다리지 않음 |
| `<script type="module" src="a.js">` | 의존 모듈도 가져옴 | 기본적으로 파싱 완료 후 평가 시작 | 의존 관계는 `import`로 명시 | 기본 평가 처리를 기다림; 비동기 작업 전체의 완료 신호는 아님 |

일반 인라인 클래식 `<script>`에는 가져올 외부 파일이 없다. 그 위치에서 실행되며, 여기에 `defer`를 붙여도 실행이 지연되지 않는다.

### 6. module은 기본적으로 파싱 이후에 실행된다

```html
<script type="module" src="main.js"></script>
```

`async`를 붙이지 않은 모듈 스크립트는 기본적으로 HTML 파싱 후 실행되므로 `defer`를 추가할 필요가 없다. 인라인 `type="module"`에도 이 기본 동작이 적용된다.

모듈은 단순히 클래식 스크립트에 지연 옵션을 붙인 것과는 다르다. 자체 스코프와 strict mode를 사용하고, 파일 사이의 의존성을 `import` / `export`로 표현한다. 두 파일이 서로 의존한다면 HTML 태그 순서에만 기대기보다 `import`로 연결하자. 로컬 실험도 `file://` 대신 HTTP 서버로 진행하는 편이 좋다. ([MDN JavaScript 모듈](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules#other_differences_between_modules_and_classic_scripts))

주의할 예외도 있다.

- `<script type="module" async>`는 기본적인 파싱 후 실행 보장을 사용하지 않는다.
- 모듈 최상위의 `await`(top-level await) 뒤에 이어지는 코드는 `DOMContentLoaded` 이후에 실행될 수 있다.
- `import()`로 나중에 불러온 모듈의 초기화까지 `DOMContentLoaded`가 기다리지는 않는다.

따라서 모듈에서 데이터를 받아 초기화하는 작업이 있다면, 준비 완료 Promise나 명시적인 초기화 함수를 사용해야 한다. DOM 준비와 애플리케이션 준비는 서로 다른 조건이다.

### 7. DOMContentLoaded와 load는 기다리는 대상이 다르다

`DOMContentLoaded`는 HTML 파싱과 파싱 후 실행 대상으로 등록된 스크립트들의 처리가 끝난 뒤 문서에 발생한다. `defer` 스크립트의 다운로드가 늦으면 이 이벤트도 늦어진다. 반면 이미지·iframe·`async` 스크립트의 로딩 완료는 기다리는 대상이 아니다. `async`는 상황에 따라 이 이벤트보다 먼저 실행될 수도, 나중에 실행될 수도 있다. ([MDN DOMContentLoaded](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event))

CSS는 간접적으로 영향을 줄 수 있다. `DOMContentLoaded`가 스타일시트 전체를 직접 기다리는 것은 아니지만, 스크립트 실행을 막는 스타일시트가 있으면 `defer` 실행이 늦어지고 결과적으로 이벤트도 늦어진다. “CSS는 항상 무관하다”라고 단정하면 안 된다. ([HTML 파싱 종료 절차](https://html.spec.whatwg.org/multipage/parsing.html#the-end))

| 필요한 조건 | 사용할 방법 |
|---|---|
| 초기 HTML의 버튼·입력 요소에 접근 | `defer`, 기본 모듈, 또는 `DOMContentLoaded` |
| 페이지의 일반적인 이미지 등 종속 리소스 로딩 완료 | `window`의 `load` 이벤트 |
| 특정 이미지의 사용 가능 여부 | 해당 이미지의 `load`·`error`, 필요하면 `decode()` |
| API 응답이나 앱 초기화 완료 | 해당 작업의 Promise·완료 이벤트 |

`window.load`는 지연 로딩하는 리소스까지 모두 기다리는 신호는 아니다. 클릭 이벤트 하나를 등록하려고 전체 페이지의 리소스를 기다릴 필요도 없다. ([MDN window.load](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event))

## 해결 방법

### 1. 외부 파일을 직접 관리한다면 defer로 단순하게 구성한다

```html
<!-- index.html의 head 안 -->
<script defer src="app.js"></script>
```

```javascript
// app.js
const button = document.querySelector("#save");

if (button) {
  button.addEventListener("click", () => {
    console.log("저장");
  });
}
```

이 파일이 초기 HTML에 `defer`로 포함된다는 조건을 관리할 수 있다면 DOM 준비를 기다리는 래퍼 없이 작성할 수 있다. 위 `if`는 버튼이 없는 다른 페이지에서도 같은 파일을 공유할 수 있도록 넣은 검사다. 필수 요소가 반드시 있어야 하는 페이지라면, 요소가 없을 때 명확한 오류를 내는 방식도 가능하다.

`</body>` 직전에 일반 스크립트를 놓는 방식도 앞서 파싱한 요소에 접근할 수 있다. 다만 `<head>`의 `defer`는 파일을 일찍 발견할 기회를 주면서 실행은 뒤로 미룬다. 실제 다운로드 시점과 성능 차이는 브라우저의 사전 탐색, 캐시, 리소스 우선순위 등에 따라 달라진다.

### 2. jQuery document ready를 DOMContentLoaded로 바꾼다

기존 코드가 다음과 같다고 하자.

```javascript
$(document).ready(function () {
  $("#save").on("click", function () {
    console.log("저장");
  });
});
```

이 코드가 DOM 준비 전에 실행된다는 조건이라면, 표준 API로 다음처럼 바꿀 수 있다.

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector("#save");

  if (button) {
    button.addEventListener("click", () => {
      console.log("저장");
    });
  }
});
```

**DOM 준비를 기다리기 위해서만 jQuery를 추가하는 신규 코드라면 표준 API를 우선할 이유가 충분하다.** 브라우저가 이미 제공하는 기능으로 처리할 수 있고, 이 기능을 위해 별도의 라이브러리 로딩 순서를 관리하지 않아도 된다. jQuery 제거에 따른 전송량 등의 효과는 실제 페이지에서 확인하자.

기존 플러그인이 jQuery를 사용한다면 전환 범위를 따로 정해야 한다. 바깥쪽 `ready`만 바꿔도 내부의 `$()`, `.on()`, 플러그인 호출에는 여전히 jQuery가 필요하다. `DOMContentLoaded`가 jQuery의 다운로드 완료를 보장해 주는 것도 아니다.

참고로 jQuery 공식 문서는 jQuery를 사용하는 경우 `$(handler)` 표기를 권장한다. `$(document).ready(handler)` 등 일부 표기가 deprecated라고 해서 **ready 기능 전체가 없어진 것은 아니다.** ([jQuery .ready() 공식 문서](https://api.jquery.com/ready/))

### 3. 늦게 로딩될 수도 있다면 readyState를 함께 확인한다

단순한 일대일 치환에서 놓치기 쉬운 부분이다.

```javascript
// DOMContentLoaded가 이미 발생했다면 실행되지 않는다.
document.addEventListener("DOMContentLoaded", init);
```

jQuery `ready`는 DOM이 준비된 뒤 등록한 콜백도 실행한다. 반면 이미 끝난 `DOMContentLoaded` 이벤트는 새 리스너를 위해 다시 발생하지 않는다. `async`, 동적으로 추가한 스크립트, 나중에 실행한 `import()`에서 초기화를 놓치는 원인이 된다.

스크립트가 언제 실행될지 통제하기 어렵다면 다음 패턴을 사용할 수 있다.

```javascript
function onDomReady(callback) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", callback, { once: true });
  } else {
    callback();
  }
}

function init() {
  const button = document.querySelector("#save");
  if (!button) return;

  button.addEventListener("click", () => {
    console.log("저장");
  });
}

onDomReady(init);
```

`document.readyState`는 다음 상태를 갖는다.

| 상태 | 의미 |
|---|---|
| `loading` | HTML을 파싱하는 중 |
| `interactive` | 파싱 완료; `defer`·기본 모듈의 실행이 남아 있을 수 있음 |
| `complete` | 문서와 load를 지연시키는 리소스 처리가 끝난 상태 |

여기서 `interactive`를 “`DOMContentLoaded`가 이미 발생했다”라고 해석하면 안 된다. 위 함수는 **DOM 파싱이 끝났다면 바로 초기화해도 된다**는 조건에 맞춘 도우미다. 다른 `defer` 파일이 나중에 만드는 전역 값까지 기다리지는 않는다. 이 검사와 리스너 등록 사이에 이벤트를 놓치는 경쟁 조건은 동기 실행 구간에서 발생하지 않는다. ([MDN readyState](https://developer.mozilla.org/en-US/docs/Web/API/Document/readyState), [DOMContentLoaded의 상태 검사 예제](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event#checking_whether_loading_is_already_complete))

또한 이 도우미는 jQuery ready의 콜백 예약 방식·예외 처리까지 복제하지 않는다. `{ once: true }`도 해당 리스너를 한 번만 실행할 뿐, `onDomReady(init)`를 여러 번 호출했을 때의 중복 초기화까지 막지는 않는다.

### 4. defer로 불러온 jQuery를 바로 다음 인라인 코드에서 사용하지 않는다

다음 구성은 문제가 된다.

```html
<script defer src="/assets/js/jquery.min.js"></script>
<script>
  $(function () {
    console.log("초기화");
  });
</script>
```

아래 인라인 클래식 스크립트는 파싱 도중 즉시 실행된다. `defer`로 지정한 jQuery는 아직 실행 전이므로 `$ is not defined` 오류가 날 수 있다. **ready 콜백을 등록하는 `$()` 호출 자체가 jQuery를 필요로 한다.**

jQuery를 유지해야 한다면 초기화 코드도 외부 파일로 옮기고 같은 방식으로 순서를 맞출 수 있다. 다음은 로컬 jQuery 파일이 있다는 전제의 배치 예다.

```html
<script defer src="/assets/js/jquery.min.js"></script>
<script defer src="/assets/js/app.js"></script>
```

`app.js`가 이 방식으로만 로딩된다면 jQuery와 초기 DOM이 준비된 뒤 실행된다. 이때도 플러그인의 추가 비동기 초기화가 있다면 그 완료 조건은 별도로 확인해야 한다.

## 예제

### 1. defer 실행 순서를 확인하는 세 파일

빈 디렉터리에 다음 세 파일을 저장한다. 외부 라이브러리 설치는 필요 없다.

`index.html`:

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>defer 실행 순서 확인</title>
  <script>
    window.report = (message) => {
      console.log(message);
      document.querySelector("#log").textContent += message + "\n";
    };

    document.addEventListener("DOMContentLoaded", () => {
      window.report(`DOMContentLoaded: ${document.readyState}`);
    });

    window.addEventListener("load", () => {
      window.report(`load: ${document.readyState}`);
    });
  </script>
  <script defer src="library.js"></script>
  <script defer src="app.js"></script>
</head>
<body>
  <button id="save" type="button">준비 중</button>
  <pre id="log"></pre>
</body>
</html>
```

`library.js`:

```javascript
window.demo = { label: "저장" };
window.report(`library: ${document.readyState}`);
```

`app.js`:

```javascript
const button = document.querySelector("#save");
window.report(`app: ${document.readyState}, button=${button !== null}`);

button.textContent = window.demo.label;
button.addEventListener("click", () => {
  window.report("click: 저장");
});
```

예제 디렉터리에서 로컬 HTTP 서버를 실행한다.

```bash
python -m http.server 8000 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:8000`을 열고 페이지와 개발자 도구의 Console을 확인한다. `report()`는 실제로 호출되는 시점에 `#log`가 존재한다는 조건으로 작성했다. 이 예제에서는 두 `defer` 파일과 이후 이벤트에서만 호출한다.

### 2. 이미 끝난 DOMContentLoaded를 놓치는 경우

첫 번째 예제의 페이지 로딩이 끝난 뒤, 개발자 도구의 Console에서 다음 코드를 실행한다.

```javascript
console.log(document.readyState);

document.addEventListener("DOMContentLoaded", () => {
  console.log("late listener");
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    console.log("init: DOM 준비 완료");
  }, { once: true });
} else {
  console.log("init: DOM 준비 완료");
}
```

`late listener`는 출력되지 않고, 상태를 검사한 초기화 코드는 실행된다. 콘솔이 평가 결과로 추가 표시하는 `undefined` 등은 예제의 `console.log()` 출력과 구분하자.

## 결과 확인

첫 번째 예제에서 페이지를 연 직후에는 다음 순서가 나타난다.

```text
library: interactive
app: interactive, button=true
DOMContentLoaded: interactive
load: complete
```

버튼을 클릭하면 한 줄이 추가된다.

```text
click: 저장
```

이 결과에서 확인할 것은 세 가지다. `library.js`가 `app.js`보다 먼저 실행되고, `app.js`는 버튼을 찾을 수 있으며, 두 파일의 동기 실행 뒤에 `DOMContentLoaded`가 발생한다. 초기화 코드를 ready 래퍼 없이 작성해도 이 배치에서는 필요한 조건이 충족된다.

두 번째 예제의 명시적인 콘솔 출력은 다음과 같다.

```text
complete
init: DOM 준비 완료
```

`async` 차이도 실험하고 싶다면 첫 예제의 두 속성을 모두 `async`로 바꾸고 개발자 도구의 Network에서 캐시 사용을 끄거나 네트워크 속도를 제한해 보자. 실행 순서와 `readyState`는 달라질 수 있다. `#log`나 버튼이 아직 없거나, `app.js`가 `library.js`보다 먼저 실행되어 `null`·`undefined` 관련 오류가 발생할 수도 있다. 이것도 `async`가 DOM 준비와 파일 순서를 보장하지 않는다는 결과다. 한 번 정상 출력되더라도 **보장된 순서가 생기는 것은 아니다.**

## 실무 팁

### 흔한 실수

| 실수 | 이유 또는 수정 방향 |
|---|---|
| 인라인 클래식 `<script defer>`로 실행을 미루려 함 | `defer`는 이 경우 효과가 없음; 외부 파일 또는 DOM 준비 이벤트 사용 |
| `defer="false"`로 옵션을 끄려 함 | 불리언 속성은 존재 자체가 참; 끄려면 속성을 제거 |
| `async defer`를 같이 쓰면 두 장점을 얻는다고 생각 | 현재 브라우저에서는 `async` 동작 적용 |
| `DOMContentLoaded`가 이미 끝난 뒤 리스너만 추가 | `readyState` 검사 또는 로딩 구조 개선 |
| `defer`가 이미지·API 응답도 기다린다고 생각 | DOM 준비와 리소스·업무 준비를 구분 |
| `defer`를 붙이면 큰 동기 연산도 가벼워진다고 생각 | 실행 비용은 그대로; 긴 작업과 불필요한 코드를 따로 개선 |

속성의 적용 범위와 불리언 속성 규칙은 [MDN script 속성 문서](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script#attributes)를 참고하자.

### 주의사항

JavaScript로 만든 `<script>`는 초기 HTML의 `defer` 선언과 동일하게 생각하면 안 된다. 동적으로 추가하는 외부 클래식 스크립트는 기본적으로 비동기 실행 특성을 갖는다. 순서가 필요하면 삽입 전 `async = false`를 지정하는 방법이 있지만, 이것이 파싱 완료를 기다리는 `defer`로 바뀐다는 뜻은 아니다. 모듈의 `import`나 로딩 완료 Promise로 의존 관계를 표현하는 방법도 있다. ([HTML script 처리 모델](https://html.spec.whatwg.org/multipage/scripting.html#prepare-the-script-element))

또한 `DOMContentLoaded`는 현재 문서의 초기 파싱에 관한 이벤트다. SPA의 화면 전환이나 나중에 추가한 컴포넌트마다 다시 발생하지 않는다. 이런 경우에는 라우터·프레임워크의 생명주기나 컴포넌트 초기화 시점을 사용해야 한다.

### 추천 명령어

프로젝트에서 실행 시점과 관련된 선언을 찾으려면 다음처럼 검색할 수 있다.

```bash
rg -n '<script|DOMContentLoaded|\.ready\(' .
```

브라우저 콘솔에서는 다음 두 줄로 현재 상태와 대상 요소를 확인할 수 있다.

```javascript
document.readyState
document.querySelector("#save")
```

성능을 비교할 때는 개발자 도구의 Network에서 다운로드를, Performance에서 스크립트 실행과 긴 작업을 함께 보자. `defer` 적용 여부만으로 고정된 개선 비율을 기대하기보다 같은 조건에서 DOM 준비 시점과 실제 상호작용을 비교하는 편이 유용하다.

## 마무리

### 핵심 요약

`defer`는 외부 클래식 스크립트의 실행을 HTML 파싱 뒤로 미루고, 같은 방식으로 선언한 파일들의 실행 순서를 지킨다. `async`는 준비되는 대로 실행하므로 DOM 준비나 파일 순서가 필요한 코드는 별도 설계가 필요하다.

DOM 준비를 이벤트로 기다릴 때는 `DOMContentLoaded`를 사용할 수 있다. 다만 jQuery `ready`가 제공하는 늦은 등록 처리까지 필요하다면 `readyState` 검사도 함께 고려해야 한다.

### 언제 사용하면 좋은가

새로 만드는 단순한 페이지라면 외부 스크립트에 `defer`를 적용하거나 기본 모듈로 구성하고, 필요한 DOM 초기화를 직접 실행하는 방식이 간결하다. 여러 경로에서 나중에 불러오는 공용 스크립트라면 상태 검사 도우미가 유용하다. jQuery 플러그인이 있는 기존 페이지는 라이브러리 의존성과 ready 사용을 함께 점검하며 전환하자.

### 추가 학습 주제

DOM 준비 문제를 해결한 뒤에는 ES 모듈의 의존성, 이벤트 루프와 마이크로태스크, 코드 분할과 동적 `import()`, 이미지 로딩·디코딩 시점을 살펴보면 실행 순서 문제를 더 정확하게 분석할 수 있다.

## 참고 자료

*본문의 기본 `defer` 예제, 버튼 클릭, `DOMContentLoaded` 이후의 리스너 등록 비교는 Chrome 155.0.8059.85에서 실행을 확인했다.*

- [WHATWG HTML: script 요소](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)
- [WHATWG HTML: 파싱 종료와 DOMContentLoaded](https://html.spec.whatwg.org/multipage/parsing.html#the-end)
- [MDN: script 요소와 defer·async](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script)
- [MDN: DOMContentLoaded 이벤트](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event)
- [MDN: document.readyState](https://developer.mozilla.org/en-US/docs/Web/API/Document/readyState)
- [MDN: window.load 이벤트](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event)
- [MDN: JavaScript 모듈](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [jQuery: .ready()](https://api.jquery.com/ready/)
