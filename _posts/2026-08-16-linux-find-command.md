---
title: "리눅스 find 명령어 사용법 완벽 정리: 파일 검색부터 삭제, exec 실행까지"
description: "Linux find 명령어의 기본 문법, 이름 검색, 파일 타입, 크기, 수정 시간, 권한, 소유자, exec, xargs, 삭제 옵션까지 실무 예제로 자세히 정리합니다."
date: 2026-08-16
categories: [Linux]
tags: [Linux, find, command, shell, bash, file-search, devops]
---

![Linux find command file search workflow](/assets/img/2026-08-16-linux-find-command.svg)

# 리눅스 find 명령어 사용법 완벽 정리

리눅스에서 파일을 찾을 때 가장 자주 사용하는 명령어 중 하나가 `find`이다.

단순히 파일 이름만 찾는다면 `ls`, `grep`, `locate`로도 어느 정도 해결할 수 있다.
하지만 실제 서버 운영이나 개발 환경에서는 조건이 훨씬 복잡해진다.

예를 들면 이런 상황이다.

- 특정 확장자의 파일만 찾고 싶다.
- 7일 이상 지난 로그 파일을 삭제하고 싶다.
- 100MB보다 큰 파일을 찾고 싶다.
- 특정 권한을 가진 파일을 찾아야 한다.
- 검색한 파일에 대해 `chmod`, `rm`, `grep` 같은 명령을 실행하고 싶다.

이런 작업을 할 때 `find`는 거의 필수 도구이다.

이번 글에서는 리눅스 `find` 명령어 사용법을 옵션별 예제 중심으로 아주 자세히 정리한다.

---

## 1. find 기본 문법

`find`의 기본 문법은 다음과 같다.

```bash
find [검색 시작 경로] [검색 조건] [실행 동작]
```

가장 단순한 예제는 현재 디렉터리 아래의 모든 파일과 디렉터리를 출력하는 것이다.

```bash
find .
```

예시 출력:

```text
.
./README.md
./src
./src/main.c
./src/util.c
./logs
./logs/app.log
```

여기서 `.`은 현재 디렉터리를 의미한다.

특정 디렉터리에서 검색하려면 경로를 지정한다.

```bash
find /var/log
```

홈 디렉터리에서 검색하려면 다음처럼 쓴다.

```bash
find ~
```

---

## 2. 파일 이름으로 검색하기: -name

가장 많이 사용하는 옵션은 `-name`이다.

```bash
find . -name "app.log"
```

현재 디렉터리 아래에서 이름이 정확히 `app.log`인 파일 또는 디렉터리를 찾는다.

와일드카드도 사용할 수 있다.

```bash
find . -name "*.log"
```

현재 디렉터리 아래에서 `.log`로 끝나는 모든 파일을 찾는다.

```bash
find . -name "test_*"
```

`test_`로 시작하는 파일을 찾는다.

```bash
find . -name "*config*"
```

이름에 `config`가 포함된 파일을 찾는다.

주의할 점은 와일드카드를 사용할 때 반드시 따옴표로 감싸는 것이 좋다는 것이다.

```bash
find . -name *.log
```

위 명령은 현재 쉘이 먼저 `*.log`를 확장해 버릴 수 있다.
그래서 의도하지 않은 결과가 나올 수 있다.

안전하게 다음처럼 작성한다.

```bash
find . -name "*.log"
```

---

## 3. 대소문자 구분 없이 검색하기: -iname

`-name`은 대소문자를 구분한다.

```bash
find . -name "readme.md"
```

이 명령은 `README.md`를 찾지 못할 수 있다.

대소문자를 무시하고 검색하려면 `-iname`을 사용한다.

```bash
find . -iname "readme.md"
```

다음 파일들을 모두 찾을 수 있다.

```text
./README.md
./readme.md
./ReadMe.md
```

확장자 검색에도 사용할 수 있다.

```bash
find . -iname "*.jpg"
```

이 명령은 `.jpg`, `.JPG`, `.Jpg` 같은 파일을 모두 찾는다.

---

## 4. 파일 타입으로 검색하기: -type

`find`는 파일, 디렉터리, 심볼릭 링크 등을 구분해서 검색할 수 있다.

자주 사용하는 `-type` 값은 다음과 같다.

| 옵션 | 의미 |
| --- | --- |
| `-type f` | 일반 파일 |
| `-type d` | 디렉터리 |
| `-type l` | 심볼릭 링크 |
| `-type b` | 블록 디바이스 |
| `-type c` | 문자 디바이스 |
| `-type p` | named pipe |
| `-type s` | socket |

일반 파일만 찾기:

```bash
find . -type f
```

디렉터리만 찾기:

```bash
find . -type d
```

심볼릭 링크만 찾기:

```bash
find . -type l
```

`.log` 확장자를 가진 일반 파일만 찾기:

```bash
find . -type f -name "*.log"
```

이렇게 `-type f`를 같이 쓰면 같은 이름의 디렉터리가 검색되는 일을 피할 수 있다.

---

## 5. 여러 조건을 함께 사용하기

`find`는 조건을 나열하면 기본적으로 AND 조건으로 처리한다.

```bash
find . -type f -name "*.log"
```

이 명령은 다음 두 조건을 모두 만족하는 항목을 찾는다.

1. 일반 파일이어야 한다.
2. 이름이 `.log`로 끝나야 한다.

크기가 100MB보다 큰 로그 파일을 찾는 예제:

```bash
find . -type f -name "*.log" -size +100M
```

`/var/log` 아래에서 30일 이상 지난 `.gz` 파일 찾기:

```bash
find /var/log -type f -name "*.gz" -mtime +30
```

---

## 6. OR 조건 사용하기: -o

둘 중 하나라도 만족하는 파일을 찾으려면 `-o`를 사용한다.

```bash
find . -type f \( -name "*.log" -o -name "*.txt" \)
```

이 명령은 `.log` 또는 `.txt` 파일을 찾는다.

괄호 앞의 `\(`, `\)`는 중요하다.
쉘에서 괄호가 특별한 의미를 가지기 때문에 백슬래시로 이스케이프한다.

대소문자 구분 없이 이미지 파일을 찾는 예제:

```bash
find . -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.gif" \)
```

---

## 7. NOT 조건 사용하기: !

특정 조건을 제외하려면 `!`를 사용한다.

`.log`가 아닌 일반 파일 찾기:

```bash
find . -type f ! -name "*.log"
```

`node_modules` 디렉터리 안의 파일을 제외하고 검색하기:

```bash
find . -type f ! -path "./node_modules/*"
```

`.git` 디렉터리를 제외하고 모든 파일 찾기:

```bash
find . -type f ! -path "./.git/*"
```

여러 디렉터리를 제외할 수도 있다.

```bash
find . -type f \
  ! -path "./.git/*" \
  ! -path "./node_modules/*" \
  ! -path "./dist/*"
```

---

## 8. 검색 깊이 제한하기: -maxdepth, -mindepth

`find`는 기본적으로 하위 디렉터리 전체를 재귀적으로 검색한다.
검색 범위를 제한하고 싶을 때 `-maxdepth`와 `-mindepth`를 사용한다.

현재 디렉터리 바로 아래만 검색:

```bash
find . -maxdepth 1
```

현재 디렉터리 바로 아래의 일반 파일만 검색:

```bash
find . -maxdepth 1 -type f
```

2단계 깊이까지만 검색:

```bash
find . -maxdepth 2 -type f
```

현재 디렉터리 자신은 제외하고 하위 항목만 검색:

```bash
find . -mindepth 1
```

현재 디렉터리 바로 아래 디렉터리만 찾기:

```bash
find . -mindepth 1 -maxdepth 1 -type d
```

실무에서는 백업 대상 디렉터리나 프로젝트 최상위 디렉터리 목록을 뽑을 때 자주 사용한다.

```bash
find /srv -mindepth 1 -maxdepth 1 -type d
```

---

## 9. 파일 크기로 검색하기: -size

파일 크기 조건은 `-size` 옵션을 사용한다.

기본 형식은 다음과 같다.

```bash
find . -type f -size [크기]
```

자주 사용하는 단위는 다음과 같다.

| 단위 | 의미 |
| --- | --- |
| `c` | byte |
| `k` | KB |
| `M` | MB |
| `G` | GB |

정확히 10MB인 파일 찾기:

```bash
find . -type f -size 10M
```

10MB보다 큰 파일 찾기:

```bash
find . -type f -size +10M
```

10MB보다 작은 파일 찾기:

```bash
find . -type f -size -10M
```

1GB보다 큰 파일 찾기:

```bash
find / -type f -size +1G 2>/dev/null
```

여기서 `2>/dev/null`은 권한 오류 메시지를 숨기기 위해 사용한다.
루트 디렉터리(`/`)부터 검색하면 접근 권한이 없는 경로가 많기 때문이다.

큰 파일을 크기순으로 보고 싶다면 `find`와 `du`, `sort`를 조합할 수 있다.

```bash
find . -type f -size +100M -exec du -h {} \; | sort -h
```

---

## 10. 수정 시간으로 검색하기: -mtime, -mmin

파일이 마지막으로 수정된 시간을 기준으로 검색하려면 `-mtime` 또는 `-mmin`을 사용한다.

| 옵션 | 기준 |
| --- | --- |
| `-mtime` | 일 단위 |
| `-mmin` | 분 단위 |

오늘 수정된 파일 찾기:

```bash
find . -type f -mtime 0
```

7일 이상 지난 파일 찾기:

```bash
find . -type f -mtime +7
```

7일 이내에 수정된 파일 찾기:

```bash
find . -type f -mtime -7
```

30분 이내에 수정된 파일 찾기:

```bash
find . -type f -mmin -30
```

60분 이상 지난 파일 찾기:

```bash
find . -type f -mmin +60
```

예를 들어 `/var/log`에서 30일 이상 지난 로그 파일을 찾으려면 다음처럼 쓴다.

```bash
find /var/log -type f -name "*.log" -mtime +30
```

---

## 11. 접근 시간과 상태 변경 시간: -atime, -ctime

파일 시간 조건에는 수정 시간 외에도 접근 시간과 상태 변경 시간이 있다.

| 옵션 | 의미 |
| --- | --- |
| `-mtime` | 파일 내용이 마지막으로 수정된 시간 |
| `-atime` | 파일을 마지막으로 읽은 시간 |
| `-ctime` | 파일의 메타데이터가 마지막으로 변경된 시간 |

최근 3일 이내에 읽은 파일 찾기:

```bash
find . -type f -atime -3
```

10일 이상 접근하지 않은 파일 찾기:

```bash
find . -type f -atime +10
```

최근 1일 이내에 권한, 소유자, 링크 수 같은 메타데이터가 바뀐 파일 찾기:

```bash
find . -type f -ctime -1
```

`ctime`은 생성 시간이 아니다.
리눅스에서 `ctime`은 change time, 즉 inode 정보가 바뀐 시간을 의미한다.
파일 권한을 `chmod`로 바꾸거나 소유자를 `chown`으로 바꾸면 `ctime`이 변경된다.

---

## 12. 특정 날짜 기준으로 검색하기: -newer

특정 파일보다 나중에 수정된 파일을 찾으려면 `-newer`를 사용한다.

먼저 기준 파일을 만든다.

```bash
touch 기준파일.txt
```

그 이후에 수정된 파일을 찾는다.

```bash
find . -type f -newer 기준파일.txt
```

특정 날짜를 기준으로 하고 싶다면 `touch -t`로 기준 파일을 만들 수 있다.

```bash
touch -t 202608010000 기준파일.txt
find . -type f -newer 기준파일.txt
```

위 예제는 2026년 8월 1일 00시 이후에 수정된 파일을 찾는다.

임시 기준 파일을 만들기 싫다면 GNU find에서는 `-newermt`를 사용할 수 있다.

```bash
find . -type f -newermt "2026-08-01"
```

특정 기간 사이의 파일을 찾는 예제:

```bash
find . -type f \
  -newermt "2026-08-01" \
  ! -newermt "2026-09-01"
```

이 명령은 2026년 8월 1일 이상, 2026년 9월 1일 미만에 수정된 파일을 찾는다.

---

## 13. 권한으로 검색하기: -perm

특정 권한을 가진 파일을 찾으려면 `-perm`을 사용한다.

정확히 `644` 권한인 파일 찾기:

```bash
find . -type f -perm 644
```

정확히 `755` 권한인 파일 찾기:

```bash
find . -type f -perm 755
```

실행 권한이 하나라도 있는 파일 찾기:

```bash
find . -type f -perm /111
```

소유자 실행 권한이 있는 파일 찾기:

```bash
find . -type f -perm /100
```

소유자, 그룹, 기타 사용자 모두에게 실행 권한이 있는 파일 찾기:

```bash
find . -type f -perm -111
```

`-perm`에서 `/`와 `-`의 의미는 다르다.

| 표현 | 의미 |
| --- | --- |
| `-perm 644` | 권한이 정확히 644 |
| `-perm /111` | 실행 권한 비트 중 하나라도 있으면 검색 |
| `-perm -111` | 실행 권한 비트가 모두 있어야 검색 |

월드 쓰기 권한이 있는 파일 찾기:

```bash
find . -type f -perm /002
```

운영 서버에서 보안 점검할 때 유용하다.

```bash
find /var/www -type f -perm /002
```

---

## 14. 소유자와 그룹으로 검색하기: -user, -group

특정 사용자가 소유한 파일 찾기:

```bash
find . -user deploy
```

특정 그룹이 소유한 파일 찾기:

```bash
find . -group www-data
```

사용자와 그룹을 함께 조건으로 걸 수도 있다.

```bash
find /var/www -type f -user deploy -group www-data
```

존재하지 않는 사용자 ID를 가진 파일을 찾으려면 `-nouser`를 사용한다.

```bash
find / -nouser 2>/dev/null
```

존재하지 않는 그룹 ID를 가진 파일을 찾으려면 `-nogroup`을 사용한다.

```bash
find / -nogroup 2>/dev/null
```

서버에서 계정을 삭제한 뒤 남은 파일을 정리할 때 유용하다.

---

## 15. 빈 파일과 빈 디렉터리 찾기: -empty

크기가 0인 파일 또는 비어 있는 디렉터리를 찾으려면 `-empty`를 사용한다.

빈 파일 찾기:

```bash
find . -type f -empty
```

빈 디렉터리 찾기:

```bash
find . -type d -empty
```

빈 로그 파일 찾기:

```bash
find /var/log -type f -name "*.log" -empty
```

빈 디렉터리 삭제:

```bash
find . -type d -empty -delete
```

단, 삭제 명령은 항상 먼저 출력으로 확인한 뒤 실행하는 것이 좋다.

```bash
find . -type d -empty
```

확인 후:

```bash
find . -type d -empty -delete
```

---

## 16. 검색 결과 출력 형식 바꾸기: -print, -printf

`find`는 기본적으로 검색 결과를 출력한다.
명시적으로 쓰면 다음과 같다.

```bash
find . -type f -print
```

GNU find에서는 `-printf`로 출력 형식을 바꿀 수 있다.

파일 경로만 출력:

```bash
find . -type f -printf "%p\n"
```

파일 크기와 경로 출력:

```bash
find . -type f -printf "%s %p\n"
```

수정 시간과 경로 출력:

```bash
find . -type f -printf "%TY-%Tm-%Td %TH:%TM %p\n"
```

권한, 소유자, 그룹, 크기, 경로 출력:

```bash
find . -type f -printf "%m %u %g %s %p\n"
```

출력 예시:

```text
644 deploy www-data 2048 ./index.html
600 deploy deploy 128 ./config/.env
755 deploy deploy 4096 ./scripts/deploy.sh
```

---

## 17. 검색한 파일에 명령 실행하기: -exec

`find`의 강력한 기능 중 하나가 `-exec`이다.
검색 결과에 대해 다른 명령을 실행할 수 있다.

기본 문법:

```bash
find . [조건] -exec 명령 {} \;
```

여기서 `{}`는 검색된 파일 경로로 치환된다.
마지막의 `\;`는 `-exec` 명령의 끝을 의미한다.

`.log` 파일의 상세 정보 보기:

```bash
find . -type f -name "*.log" -exec ls -lh {} \;
```

`.sh` 파일에 실행 권한 추가:

```bash
find . -type f -name "*.sh" -exec chmod +x {} \;
```

`.bak` 파일 삭제:

```bash
find . -type f -name "*.bak" -exec rm {} \;
```

하지만 삭제 전에는 반드시 먼저 확인한다.

```bash
find . -type f -name "*.bak" -print
```

확인 후 삭제:

```bash
find . -type f -name "*.bak" -exec rm {} \;
```

---

## 18. -exec ... {} + 사용하기

`-exec 명령 {} \;`는 검색된 파일마다 명령을 한 번씩 실행한다.

예를 들어 파일이 1000개라면 `rm`이 1000번 실행될 수 있다.

```bash
find . -type f -name "*.tmp" -exec rm {} \;
```

반면 `{} +`를 사용하면 가능한 많은 파일을 모아서 명령을 실행한다.

```bash
find . -type f -name "*.tmp" -exec rm {} +
```

대량 파일 처리에서는 `{} +`가 더 효율적이다.

예를 들어 검색된 파일들의 상세 정보를 한 번에 확인하려면 다음처럼 쓸 수 있다.

```bash
find . -type f -name "*.log" -exec ls -lh {} +
```

---

## 19. 검색 결과를 grep으로 검사하기

파일 이름이 아니라 파일 내용에서 문자열을 찾고 싶을 때 `find`와 `grep`을 조합할 수 있다.

`.conf` 파일 안에서 `listen` 문자열 찾기:

```bash
find /etc -type f -name "*.conf" -exec grep -n "listen" {} + 2>/dev/null
```

현재 프로젝트의 `.c`, `.h` 파일에서 `malloc` 찾기:

```bash
find . -type f \( -name "*.c" -o -name "*.h" \) -exec grep -n "malloc" {} +
```

대소문자 구분 없이 `error` 찾기:

```bash
find . -type f -name "*.log" -exec grep -ni "error" {} +
```

참고로 코드 검색만 목적이라면 `rg` 또는 `grep -R`이 더 편할 때도 많다.
하지만 파일 조건을 세밀하게 걸어야 할 때는 `find`와 `grep` 조합이 여전히 유용하다.

---

## 20. xargs와 함께 사용하기

`find` 결과를 다른 명령으로 넘길 때 `xargs`를 사용할 수도 있다.

```bash
find . -type f -name "*.log" | xargs ls -lh
```

하지만 파일 이름에 공백, 줄바꿈, 특수문자가 들어가면 문제가 생길 수 있다.

더 안전한 방식은 `-print0`와 `xargs -0`를 함께 쓰는 것이다.

```bash
find . -type f -name "*.log" -print0 | xargs -0 ls -lh
```

공백이 포함된 파일도 안전하게 처리된다.

```text
./logs/error log.txt
./logs/access log.txt
```

삭제 작업에도 사용할 수 있다.

```bash
find . -type f -name "*.tmp" -print0 | xargs -0 rm
```

단순 삭제라면 `-delete`나 `-exec rm {} +`도 좋은 선택이다.

---

## 21. 파일 삭제하기: -delete

`find` 자체에 삭제 옵션인 `-delete`가 있다.

`.tmp` 파일 삭제:

```bash
find . -type f -name "*.tmp" -delete
```

30일 이상 지난 로그 파일 삭제:

```bash
find /var/log -type f -name "*.log" -mtime +30 -delete
```

빈 디렉터리 삭제:

```bash
find . -type d -empty -delete
```

삭제 명령은 실수하면 되돌리기 어렵다.
따라서 항상 먼저 `-print`로 대상 목록을 확인한다.

```bash
find /var/log -type f -name "*.log" -mtime +30 -print
```

문제가 없으면 삭제한다.

```bash
find /var/log -type f -name "*.log" -mtime +30 -delete
```

특히 `/` 또는 `/home` 같은 넓은 범위에서 `-delete`를 사용할 때는 매우 조심해야 한다.

---

## 22. 디렉터리 제외하기: -prune

`node_modules`, `.git`, `vendor` 같은 디렉터리는 검색에서 제외하고 싶을 때가 많다.
이때 `-prune`을 사용한다.

`.git` 디렉터리를 제외하고 파일 검색:

```bash
find . -path "./.git" -prune -o -type f -print
```

`node_modules`를 제외하고 `.js` 파일 찾기:

```bash
find . -path "./node_modules" -prune -o -type f -name "*.js" -print
```

여러 디렉터리 제외:

```bash
find . \
  \( -path "./.git" -o -path "./node_modules" -o -path "./dist" \) -prune \
  -o -type f -print
```

`-prune`은 처음 보면 문법이 조금 어색하다.
다음처럼 이해하면 된다.

1. 제외할 경로를 먼저 찾는다.
2. 그 경로는 더 내려가지 않는다.
3. 나머지 경로에서 원하는 조건을 검색한다.

---

## 23. 파일 경로로 검색하기: -path

파일 이름만이 아니라 전체 경로 패턴으로 검색하려면 `-path`를 사용한다.

```bash
find . -path "*/logs/*.log"
```

`logs` 디렉터리 아래의 `.log` 파일을 찾는다.

`test` 디렉터리 아래의 `.py` 파일 찾기:

```bash
find . -path "*/test/*.py"
```

`backup`이 포함된 경로 제외:

```bash
find . -type f ! -path "*backup*"
```

대소문자를 구분하지 않으려면 `-ipath`를 사용한다.

```bash
find . -ipath "*readme*"
```

---

## 24. 정규식으로 검색하기: -regex

`-regex`를 사용하면 경로 전체에 대해 정규식 검색을 할 수 있다.

```bash
find . -regex ".*\.\(c\|h\)"
```

`.c` 또는 `.h`로 끝나는 파일을 찾는다.

GNU find에서는 정규식 타입을 바꿀 수 있다.

```bash
find . -regextype posix-extended -regex ".*\.(c|h)"
```

대소문자 구분 없이 정규식 검색:

```bash
find . -regextype posix-extended -iregex ".*\.(jpg|png|gif)"
```

단순 확장자 검색은 `-name`이 더 읽기 쉽다.
복잡한 패턴이 필요할 때만 `-regex`를 사용하는 편이 좋다.

---

## 25. 링크 처리 옵션: -L, -P, -H

심볼릭 링크가 있는 디렉터리를 검색할 때는 링크 처리 방식이 중요하다.

기본적으로 `find`는 심볼릭 링크를 따라가지 않는다.
이 기본 동작은 `-P`와 같다.

```bash
find -P . -type f
```

심볼릭 링크가 가리키는 대상까지 따라가려면 `-L`을 사용한다.

```bash
find -L . -type f
```

명령행에 지정한 심볼릭 링크만 따라가고, 그 아래에서 만나는 링크는 따라가지 않으려면 `-H`를 사용한다.

```bash
find -H ./linked-dir -type f
```

심볼릭 링크를 따라가면 순환 링크나 예상보다 넓은 검색 범위가 생길 수 있다.
운영 서버에서는 검색 범위를 먼저 좁혀서 확인하는 것이 좋다.

---

## 26. 권한 오류 숨기기

루트 디렉터리부터 검색하면 권한 오류가 많이 나온다.

```bash
find / -name "*.conf"
```

예시 오류:

```text
find: '/proc/1234/task/1234/fd': Permission denied
find: '/root': Permission denied
```

오류 메시지를 숨기려면 표준 오류를 `/dev/null`로 보낸다.

```bash
find / -name "*.conf" 2>/dev/null
```

일반 사용자로 서버 전체를 검색할 때 자주 사용하는 형태이다.

---

## 27. 실무 예제 1: 오래된 로그 파일 찾고 삭제하기

먼저 삭제 대상 확인:

```bash
find /var/log/myapp -type f -name "*.log" -mtime +30 -print
```

문제가 없으면 삭제:

```bash
find /var/log/myapp -type f -name "*.log" -mtime +30 -delete
```

압축 로그까지 포함하려면:

```bash
find /var/log/myapp -type f \( -name "*.log" -o -name "*.log.gz" \) -mtime +30 -print
```

확인 후 삭제:

```bash
find /var/log/myapp -type f \( -name "*.log" -o -name "*.log.gz" \) -mtime +30 -delete
```

---

## 28. 실무 예제 2: 큰 파일 찾아서 디스크 정리하기

디스크가 꽉 찼을 때 먼저 큰 파일부터 찾는다.

```bash
find / -type f -size +1G 2>/dev/null
```

크기와 함께 보기:

```bash
find / -type f -size +1G -exec du -h {} + 2>/dev/null
```

크기순 정렬:

```bash
find / -type f -size +500M -exec du -h {} + 2>/dev/null | sort -h
```

특정 디렉터리에서만 찾기:

```bash
find /home -type f -size +500M
```

로그 디렉터리에서 큰 파일 찾기:

```bash
find /var/log -type f -size +100M -exec ls -lh {} +
```

---

## 29. 실무 예제 3: 특정 문자열이 들어간 설정 파일 찾기

`/etc` 아래의 설정 파일에서 `server_name`이 들어간 파일 찾기:

```bash
find /etc -type f -name "*.conf" -exec grep -n "server_name" {} + 2>/dev/null
```

Nginx 설정에서 특정 도메인 찾기:

```bash
find /etc/nginx -type f -exec grep -n "example.com" {} + 2>/dev/null
```

프로젝트에서 DB 접속 문자열 찾기:

```bash
find . -type f \
  \( -name "*.env" -o -name "*.yml" -o -name "*.yaml" -o -name "*.properties" \) \
  -exec grep -n "DB_HOST" {} +
```

---

## 30. 실무 예제 4: 권한 문제 찾기

웹 루트에서 월드 쓰기 권한이 있는 파일 찾기:

```bash
find /var/www -type f -perm /002
```

월드 쓰기 권한이 있는 디렉터리 찾기:

```bash
find /var/www -type d -perm /002
```

실행 권한이 필요한 스크립트 찾기:

```bash
find ./scripts -type f -name "*.sh" ! -perm /111
```

찾은 스크립트에 실행 권한 추가:

```bash
find ./scripts -type f -name "*.sh" ! -perm /111 -exec chmod +x {} +
```

---

## 31. 실무 예제 5: 백업 파일 정리하기

백업 파일 확인:

```bash
find ./backup -type f \( -name "*.bak" -o -name "*.old" -o -name "*.tmp" \) -print
```

7일 이상 지난 백업 파일 확인:

```bash
find ./backup -type f \( -name "*.bak" -o -name "*.old" -o -name "*.tmp" \) -mtime +7 -print
```

삭제:

```bash
find ./backup -type f \( -name "*.bak" -o -name "*.old" -o -name "*.tmp" \) -mtime +7 -delete
```

---

## 32. 실무 예제 6: 최근 배포 이후 바뀐 파일 찾기

배포 직전에 기준 파일을 만들어 둔다.

```bash
touch /tmp/before-deploy
```

배포 후 변경된 파일을 확인한다.

```bash
find /var/www/myapp -type f -newer /tmp/before-deploy
```

또는 날짜 기준으로 확인한다.

```bash
find /var/www/myapp -type f -newermt "2026-08-16 10:00"
```

배포 이후 변경된 설정 파일만 찾기:

```bash
find /var/www/myapp -type f \
  \( -name "*.yml" -o -name "*.yaml" -o -name "*.conf" -o -name ".env" \) \
  -newermt "2026-08-16 10:00"
```

---

## 33. 실무 예제 7: 확장자별 파일 개수 세기

`.c` 파일 개수 세기:

```bash
find . -type f -name "*.c" | wc -l
```

`.c`와 `.h` 파일 개수 세기:

```bash
find . -type f \( -name "*.c" -o -name "*.h" \) | wc -l
```

공백이나 특수문자가 있는 파일명을 더 안전하게 처리하려면 다음처럼 쓴다.

```bash
find . -type f -name "*.c" -print0 | tr -cd '\0' | wc -c
```

---

## 34. 실무 예제 8: 찾은 파일을 tar로 묶기

`.log` 파일을 찾아 압축 파일로 묶기:

```bash
find ./logs -type f -name "*.log" -print0 | tar --null -czf logs.tar.gz --files-from -
```

7일 이내 수정된 파일만 백업:

```bash
find ./data -type f -mtime -7 -print0 | tar --null -czf recent-data.tar.gz --files-from -
```

파일 이름에 공백이 들어갈 수 있으므로 `-print0`와 `--null`을 함께 사용한다.

---

## 35. 자주 하는 실수

### 와일드카드에 따옴표를 쓰지 않는 경우

좋지 않은 예:

```bash
find . -name *.log
```

권장:

```bash
find . -name "*.log"
```

### 삭제 전 확인하지 않는 경우

위험한 예:

```bash
find . -name "*.tmp" -delete
```

권장:

```bash
find . -name "*.tmp" -print
```

확인 후:

```bash
find . -name "*.tmp" -delete
```

### 디렉터리와 파일을 구분하지 않는 경우

좋지 않은 예:

```bash
find . -name "cache"
```

파일인지 디렉터리인지 명확히 하는 것이 좋다.

```bash
find . -type d -name "cache"
```

또는:

```bash
find . -type f -name "cache"
```

### -mtime의 +, - 의미를 헷갈리는 경우

`find`에서 시간 조건의 기호는 다음처럼 이해하면 된다.

| 표현 | 의미 |
| --- | --- |
| `-mtime 7` | 대략 7일 전 |
| `-mtime +7` | 7일보다 오래됨 |
| `-mtime -7` | 7일보다 최근 |

오래된 파일 삭제에는 보통 `+`를 사용한다.

```bash
find ./logs -type f -mtime +30 -delete
```

최근 파일 조회에는 보통 `-`를 사용한다.

```bash
find ./logs -type f -mtime -1
```

---

## 36. 자주 쓰는 find 명령어 모음

현재 디렉터리 아래 모든 파일 찾기:

```bash
find . -type f
```

현재 디렉터리 아래 모든 디렉터리 찾기:

```bash
find . -type d
```

이름으로 파일 찾기:

```bash
find . -type f -name "filename.txt"
```

확장자로 파일 찾기:

```bash
find . -type f -name "*.log"
```

대소문자 무시하고 찾기:

```bash
find . -type f -iname "*.jpg"
```

100MB보다 큰 파일 찾기:

```bash
find . -type f -size +100M
```

7일 이내 수정된 파일 찾기:

```bash
find . -type f -mtime -7
```

30일 이상 지난 파일 찾기:

```bash
find . -type f -mtime +30
```

빈 파일 찾기:

```bash
find . -type f -empty
```

빈 디렉터리 찾기:

```bash
find . -type d -empty
```

실행 권한이 있는 파일 찾기:

```bash
find . -type f -perm /111
```

월드 쓰기 권한이 있는 파일 찾기:

```bash
find . -type f -perm /002
```

검색 결과에 명령 실행:

```bash
find . -type f -name "*.sh" -exec chmod +x {} +
```

오래된 로그 삭제:

```bash
find /var/log/myapp -type f -name "*.log" -mtime +30 -delete
```

---

## 마무리

`find` 명령어는 단순한 파일 검색 도구처럼 보이지만, 실제로는 리눅스 파일 시스템을 조건 기반으로 탐색하고 처리하는 강력한 자동화 도구이다.

핵심은 다음과 같다.

1. 이름 검색은 `-name`, 대소문자 무시는 `-iname`을 사용한다.
2. 파일과 디렉터리는 `-type f`, `-type d`로 명확히 구분한다.
3. 크기 조건은 `-size`, 시간 조건은 `-mtime`, `-mmin`, `-newermt`를 사용한다.
4. 권한 점검은 `-perm`, 소유자 점검은 `-user`, `-group`을 사용한다.
5. 검색 결과에 명령을 실행할 때는 `-exec` 또는 `xargs`를 사용한다.
6. 삭제 작업은 반드시 먼저 `-print`로 확인한 뒤 `-delete`를 실행한다.

처음에는 옵션이 많아 복잡해 보일 수 있다.
하지만 `find . -type f -name "*.log"` 같은 기본 패턴부터 익숙해지면, 서버 로그 정리, 대용량 파일 탐색, 권한 점검, 배포 후 변경 파일 확인 같은 작업을 훨씬 빠르고 안전하게 처리할 수 있다.

---

## 참고 자료

- [GNU findutils Manual](https://www.gnu.org/software/findutils/manual/html_mono/find.html)
- [Linux man page: find(1)](https://man7.org/linux/man-pages/man1/find.1.html)
- [GNU findutils Documentation](https://www.gnu.org/software/findutils/)
