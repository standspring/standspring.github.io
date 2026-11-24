---
title: "Python venv 사용법: Windows에서 가상환경 만들고 pip 설치 오류 줄이기"
description: "패키지를 설치했는데 import가 실패할 때 확인할 Python 경로부터 설명합니다. Windows PowerShell에서 venv 생성, 활성화 없는 실행, requirements.txt 저장과 환경 재생성, VS Code 연결을 따라 해 봅니다."
date: 2026-11-24 17:21:36 +0900
categories: [Development, Python]
tags: [Python, venv, pip, Windows, VSCode, 가상환경]
toc: true
toc_sticky: true
image:
  path: /assets/img/2026-11-24-python-venv-windows-guide-handwritten-hero.png
  alt: "프로젝트용 가상환경을 만들고 같은 Python으로 패키지 설치와 실행을 이어가는 과정"
---

`pip install`은 끝났는데 프로그램을 실행하면 `ModuleNotFoundError`가 나타난다. 어제까지 실행되던 프로젝트가 다른 패키지를 설치한 뒤부터 이상해지기도 한다. 이런 문제를 만났다면 **설치에 사용한 Python과 실행에 사용한 Python이 같은지** 먼저 확인해 보자.

이 글에서는 Windows PowerShell에서 작은 연습 프로젝트를 만든다. Python이 이미 설치되어 있고 `python --version`이 실행되는 환경을 기준으로 한다. 명령은 프로젝트 폴더 안에서 순서대로 실행한다.

## venv는 프로젝트별 패키지 보관함

가상환경은 프로젝트가 사용할 Python 실행 환경과 패키지 설치 위치를 분리한다. 기본 설정에서는 다른 가상환경과 기본 Python에 설치한 패키지를 그대로 공유하지 않는다. 예를 들어 프로젝트 A와 B가 같은 라이브러리의 서로 다른 버전을 요구할 때, 각자 가상환경을 두고 관리할 수 있다. 기본 개념은 [Python venv 공식 문서](https://docs.python.org/3/library/venv.html)에 정리되어 있다.

![각각의 가상환경에 서로 다른 버전의 패키지를 보관하는 프로젝트 A와 B](/assets/img/2026-11-24-python-venv-windows-guide-isolation.png)
_같은 이름의 패키지도 프로젝트마다 별도의 설치 위치에서 관리한다. 그림의 버전 번호는 개념 설명용이다._

이 구분은 패키지 관리를 위한 것이다. 가상환경 안에서 실행한 코드가 파일이나 네트워크에 접근하지 못하도록 막는 보안 경계는 아니다.

| 이름 | 이 실습에서의 역할 |
|---|---|
| `python` | 명령을 해석하고 프로그램을 실행하는 Python |
| `venv` | 가상환경을 만드는 표준 라이브러리 모듈 |
| `.venv` | 프로젝트 안에 만들 가상환경 폴더 이름 |
| `pip` | 선택한 Python 환경에 패키지를 설치하는 도구 |
| `requirements.txt` | 다시 설치할 패키지 목록을 적어 두는 파일 |

## 1. 사용할 Python을 확인하고 환경 만들기

먼저 연습용으로 새 폴더를 만든다. 아래 폴더가 이미 있으면 다른 이름을 사용한다.

```powershell
New-Item -ItemType Directory -Path 'venv-practice'
Set-Location -LiteralPath 'venv-practice'

python --version
python -c "import sys; print(sys.executable)"
python -m venv .venv
```

두 번째 출력은 현재 `python` 명령이 가리키는 실행 파일이다. 여러 Python 버전이 설치되어 있다면, 프로젝트가 요구하는 버전인지 여기서 확인한다. `venv`는 명령을 실행한 기본 Python을 바탕으로 만들어진다. 원하는 버전을 자동으로 찾아 다운로드하는 명령은 아니다.

Windows에서는 `.venv\Scripts` 아래에 실행 파일이 생긴다. 생성 후 다음 두 명령으로 확인한다.

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

`pip --version` 출력의 설치 경로가 현재 프로젝트의 `.venv` 안에 있는지 살펴본다. 단순히 버전 숫자만 보는 것보다 **어디에 설치되어 있는지**가 이 실습에서는 더 중요하다.

## 2. 활성화 없이 같은 Python으로 설치하고 실행하기

가상환경을 쓰기 위해 반드시 활성화 스크립트를 실행할 필요는 없다. [venv의 동작 설명](https://docs.python.org/3/library/venv.html#how-venvs-work)처럼 해당 환경의 Python 실행 파일을 직접 지정해도 된다.

```powershell
.\.venv\Scripts\python.exe -m pip install requests
.\.venv\Scripts\python.exe -c "import requests; print(requests.__version__); print(requests.__file__)"
```

`requests`는 연습용 패키지다. 설치에는 패키지 저장소로 접근할 수 있는 인터넷 연결이 필요하지만, 위 확인 명령은 웹 요청을 보내지 않고 설치된 패키지를 불러오기만 한다. 설치 흐름은 [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)도 참고할 수 있다.

`python.exe -m pip`는 **그 Python으로 pip 모듈을 실행한다**는 뜻이다. 설치와 실행 양쪽에서 같은 실행 파일을 지정하므로, 서로 다른 환경을 사용하는 실수를 줄일 수 있다.

프로젝트의 `main.py`를 실행할 때도 같은 원칙을 적용한다.

```powershell
.\.venv\Scripts\python.exe main.py
```

`main.py`는 본인 프로그램 파일명으로 바꾼다. 상대 경로는 현재 작업 폴더를 기준으로 해석된다. 다른 위치에서 예약 실행한다면 작업 폴더를 지정하거나 실행 파일·스크립트의 전체 경로를 사용한다.

## 3. 활성화는 긴 경로를 줄이는 편의 기능

직접 경로를 적는 방식이 익숙해졌다면 활성화도 사용할 수 있다.

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
python -m pip --version
```

활성화는 현재 셸에서 가상환경의 실행 파일을 먼저 찾도록 경로를 조정한다. 프롬프트에 `(.venv)`가 표시되는 것과 함께, 실제 출력 경로도 확인한다. 작업을 마치면 다음 명령으로 빠져나온다.

```powershell
deactivate
```

새 터미널에는 이전 활성화 상태가 그대로 이어지지 않는다. `Activate.ps1`이 실행 정책 때문에 차단되면, 앞 절의 `.\.venv\Scripts\python.exe` 직접 실행 방식으로 계속할 수 있다. 이 실습을 위해 시스템 실행 정책을 바꿀 필요는 없다.

## 4. 설치 목록을 저장하고 다시 구성하기

프로젝트가 실행되는 상태에서 설치 목록을 기록한다. 다음은 PowerShell 명령이다.

```powershell
.\.venv\Scripts\python.exe -m pip freeze |
    Set-Content -LiteralPath requirements.txt -Encoding utf8
Get-Content -LiteralPath requirements.txt
```

`requests`와 함께 설치된 의존 패키지의 버전도 보일 수 있다. `pip freeze`는 현재 설치된 내용을 requirements 형식으로 출력하며, 의존성을 새로 계산한 lockfile을 만드는 기능은 아니다. 자세한 차이는 [pip freeze 공식 문서](https://pip.pypa.io/en/stable/cli/pip_freeze/)에 설명되어 있다.

같은 프로젝트 안에서 비교할 새 환경을 만들어 설치해 본다. 기존 `.venv`를 지우거나 덮어쓸 필요가 없다.

```powershell
python -m venv .venv-rebuild
.\.venv-rebuild\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-rebuild\Scripts\python.exe -m pip check
.\.venv-rebuild\Scripts\python.exe -c "import requests; print(requests.__version__)"
```

`pip check`는 설치된 패키지의 의존성 호환성을 검사한다. 성공하더라도 프로그램의 모든 기능이 정상이라는 뜻은 아니므로 실제 프로그램도 실행해 본다.

다른 PC로 옮길 때는 코드와 설치 목록을 전달하고 가상환경을 다시 만든다. Python 버전, 운영체제, 외부 라이브러리 차이 때문에 동일한 목록만으로 모든 환경이 완전히 같아지는 것은 아니다. 프로젝트 README에는 Python 버전과 별도 설정도 기록해 두는 편이 좋다.

Git을 쓴다면 프로젝트의 기존 `.gitignore`에 다음 줄을 추가한다. 기존 파일 전체를 덮어쓰지 말고 필요한 항목만 덧붙인다.

```gitignore
.venv/
.venv-rebuild/
```

## 설치했는데 import가 안 될 때의 점검 순서

현재 실행 환경을 한 번에 확인하고 싶다면 다음 파일을 프로젝트에 저장한다. [환경 확인 예제 다운로드](/assets/code/python-venv-windows-guide/env_info.py)도 사용할 수 있다.

```python
import sys
from importlib.metadata import PackageNotFoundError, version

print("Python:", sys.executable)
print("Version:", sys.version.split()[0])
print("Virtual environment:", sys.prefix != sys.base_prefix)
try:
    print("requests:", version("requests"))
except PackageNotFoundError:
    print("requests: not installed in this environment")
```

`env_info.py`로 저장했다면 아래와 같이 실행한다. 경로와 버전은 각자 설치한 환경에 따라 달라진다.

```powershell
.\.venv\Scripts\python.exe env_info.py
```

| 증상 | 먼저 확인할 것 |
|---|---|
| 설치는 됐지만 `ModuleNotFoundError` | 실행한 Python 경로와 `-m pip --version`의 경로 |
| VS Code에서만 import 실패 | 편집기에서 선택한 인터프리터와 터미널의 실행 파일 |
| 새 터미널에서 패키지가 안 보임 | 활성화 여부 또는 가상환경 Python 직접 지정 여부 |
| `requirements.txt` 설치 실패 | 첫 오류 메시지, Python 버전, 패키지의 해당 환경 지원 여부 |
| 폴더를 옮긴 후 가상환경 실행 실패 | 이동한 환경을 재사용하지 말고 새 위치에서 재생성 |

VS Code에서는 Python 파일을 열고 상태 표시줄의 환경 선택에서 프로젝트의 `.venv`를 선택한다. 환경이 보이지 않으면 환경 검색을 새로 고침한다. 인터페이스와 검색 방법은 [VS Code Python 환경 문서](https://code.visualstudio.com/docs/python/environments)를 참고한다.

이후 [PyInstaller로 exe 만들기](/posts/python_windows_exe_deployment_pyinstaller/)나 [작업 스케줄러로 Python 실행하기](/posts/task_scheduler/)로 이어갈 때도, 어느 Python으로 설치하고 실행하는지 같은 기준으로 확인하면 된다.
