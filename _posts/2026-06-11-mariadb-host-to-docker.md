---
title: "호스트 MariaDB를 Docker MariaDB로 옮기는 방법"
description: "Ubuntu 같은 호스트에서 직접 운영하던 MariaDB를 Docker Compose 기반 MariaDB 컨테이너로 이전하는 절차를 초보자도 따라 할 수 있게 백업, 복원, 포트 전환, 롤백 순서로 정리합니다."
date: 2026-06-11
categories: [Database, Docker]
tags: [MariaDB, Docker, Docker Compose, Database, Backup, Restore, Linux, 서버운영]
---

![MariaDB 호스트에서 Docker로 이전하는 흐름](/assets/img/2026-06-11-mariadb-host-to-docker.svg)

호스트에 MariaDB를 직접 설치해서 운영하다 보면 처음에는 편하다.
하지만 시간이 지나면 서버 이전, 버전 관리, 백업 경로 관리, 개발 환경 복제 같은 일이 점점 번거로워진다.

이럴 때 MariaDB를 Docker 컨테이너로 옮기면 DB 실행 환경을 파일 하나로 관리할 수 있다.
단, 데이터베이스는 실수하면 서비스 장애나 데이터 손실로 이어질 수 있으므로 순서를 지키는 것이 중요하다.

이 글에서는 **현재 호스트에서 실행 중인 MariaDB를 Docker Compose 환경의 MariaDB로 이전하는 방법**을 초보자 기준으로 정리한다.

---

## 목표 구조

이전 전에는 MariaDB가 호스트에 직접 설치되어 있다고 가정한다.

```text
애플리케이션
  ↓
호스트 MariaDB
  ↓
/var/lib/mysql
```

이전 후에는 MariaDB가 Docker 컨테이너 안에서 실행된다.
데이터는 컨테이너 내부에만 두지 않고, 호스트 디렉터리에 저장한다.

```text
애플리케이션
  ↓
Docker MariaDB container
  ↓
/srv/mariadb-docker/data
```

중요한 점은 **컨테이너를 지워도 데이터가 사라지지 않게 하는 것**이다.
그래서 MariaDB 데이터 디렉터리인 `/var/lib/mysql`을 호스트의 `/srv/mariadb-docker/data`에 연결한다.

---

## 전체 작업 흐름

작업 순서는 다음과 같다.

1. 현재 MariaDB 버전을 확인한다.
2. 기존 DB를 덤프 파일로 백업한다.
3. Docker Compose 파일을 만든다.
4. Docker MariaDB를 임시 포트로 먼저 실행한다.
5. 백업 파일을 Docker MariaDB에 복원한다.
6. 데이터가 정상인지 확인한다.
7. 기존 MariaDB를 멈추고 Docker MariaDB를 3306 포트로 전환한다.
8. 문제가 있으면 기존 MariaDB로 롤백한다.

처음부터 기존 DB를 지우거나 덮어쓰지 않는다.
새 Docker DB를 먼저 만들고, 충분히 확인한 뒤에 마지막에 포트만 전환한다.

---

## 작업 전 주의사항

운영 중인 DB를 옮길 때는 반드시 서비스 점검 시간을 잡는 것이 좋다.
백업을 뜨는 동안에도 데이터가 계속 바뀌면 백업 시점과 실제 운영 데이터가 달라질 수 있다.

가장 안전한 방법은 아래 순서다.

1. 웹 서비스나 배치 프로그램의 DB 쓰기 작업을 잠시 멈춘다.
2. MariaDB 백업을 만든다.
3. Docker MariaDB에 복원한다.
4. 애플리케이션 연결을 새 DB로 바꾼다.

또한 이 글의 명령어에서 비밀번호, DB 이름, 계정명은 예시다.
실제 서버에서는 반드시 본인 환경에 맞게 바꿔야 한다.

---

## 1. 현재 MariaDB 버전 확인하기

먼저 현재 호스트에서 사용 중인 MariaDB 버전을 확인한다.

```bash
mariadb --version
```

또는 아래 명령어를 사용할 수도 있다.

```bash
mysql --version
```

예를 들어 결과가 다음과 비슷하다고 하자.

```text
mariadb  Ver 15.1 Distrib 10.11.8-MariaDB
```

그러면 Docker 이미지도 가능하면 같은 주 버전인 `mariadb:10.11`을 사용하는 것이 좋다.
처음 이전할 때부터 버전 업그레이드까지 같이 하면 문제가 생겼을 때 원인 파악이 어려워진다.

**이전은 이전대로 하고, 업그레이드는 나중에 따로 하는 것**을 추천한다.

---

## 2. 기존 DB 백업하기

백업 파일을 저장할 디렉터리를 만든다.

```bash
sudo mkdir -p /backup/mariadb
sudo chmod 700 /backup/mariadb
```

전체 데이터베이스를 백업한다.

```bash
sudo mariadb-dump \
  -u root -p \
  --all-databases \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  > /backup/mariadb/all-databases.sql
```

옵션 의미는 다음과 같다.

| 옵션 | 의미 |
| --- | --- |
| `--all-databases` | 모든 DB를 백업 |
| `--single-transaction` | InnoDB 테이블을 백업할 때 일관성을 유지 |
| `--routines` | 저장 프로시저와 함수를 포함 |
| `--triggers` | 트리거를 포함 |
| `--events` | 이벤트 스케줄러 내용을 포함 |

만약 `mariadb-dump` 명령어가 없다면 기존 환경에 따라 `mysqldump`를 사용할 수 있다.

```bash
sudo mysqldump \
  -u root -p \
  --all-databases \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  > /backup/mariadb/all-databases.sql
```

백업 파일이 만들어졌는지 확인한다.

```bash
ls -lh /backup/mariadb/all-databases.sql
```

파일 크기가 `0`이면 백업이 제대로 된 것이 아니다.
오류 메시지를 확인하고 다시 백업해야 한다.

---

## 3. Docker MariaDB 작업 디렉터리 만들기

Docker Compose 파일과 데이터 디렉터리를 둘 위치를 만든다.

```bash
sudo mkdir -p /srv/mariadb-docker/data
sudo mkdir -p /srv/mariadb-docker/conf
cd /srv/mariadb-docker
```

디렉터리 구조는 이렇게 사용할 것이다.

```text
/srv/mariadb-docker/
  docker-compose.yml
  .env
  data/
  conf/
```

`data` 디렉터리는 실제 MariaDB 데이터가 저장되는 곳이다.
이 디렉터리는 실수로 삭제하면 안 된다.

---

## 4. .env 파일 만들기

DB 비밀번호를 Compose 파일에 직접 쓰지 않기 위해 `.env` 파일을 만든다.

```bash
sudo nano .env
```

아래 내용을 넣는다.

```env
MARIADB_ROOT_PASSWORD=change_this_root_password
MARIADB_DATABASE=app_db
MARIADB_USER=app_user
MARIADB_PASSWORD=change_this_app_password
```

권한을 제한한다.

```bash
sudo chmod 600 .env
```

각 항목의 의미는 다음과 같다.

| 변수 | 의미 |
| --- | --- |
| `MARIADB_ROOT_PASSWORD` | MariaDB root 계정 비밀번호 |
| `MARIADB_DATABASE` | 처음 생성할 DB 이름 |
| `MARIADB_USER` | 애플리케이션에서 사용할 DB 계정 |
| `MARIADB_PASSWORD` | 애플리케이션 DB 계정 비밀번호 |

단, 나중에 전체 백업 파일을 복원할 것이므로 `MARIADB_DATABASE`, `MARIADB_USER`는 초기 생성용에 가깝다.
기존 DB 백업 안에 사용자와 권한 정보가 들어 있다면 복원 후 그 정보가 기준이 된다.

---

## 5. docker-compose.yml 작성하기

`docker-compose.yml` 파일을 만든다.

```bash
sudo nano docker-compose.yml
```

아래 내용을 넣는다.

```yaml
services:
  mariadb:
    image: mariadb:10.11
    container_name: mariadb
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "3307:3306"
    volumes:
      - ./data:/var/lib/mysql
      - ./conf:/etc/mysql/conf.d:ro
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
```

여기서 일부러 호스트 포트를 `3307`로 열었다.

```yaml
ports:
  - "3307:3306"
```

기존 호스트 MariaDB가 이미 `3306`을 사용 중일 가능성이 높기 때문이다.
처음에는 Docker MariaDB를 `3307`로 띄워서 테스트하고, 마지막 전환 시점에만 `3306`으로 바꾼다.

이미지 버전은 본인 환경에 맞게 바꾼다.

```yaml
image: mariadb:10.11
```

기존 MariaDB가 11.4라면 `mariadb:11.4`처럼 맞춘다.

---

## 6. Docker MariaDB 실행하기

Docker MariaDB를 실행한다.

```bash
sudo docker compose up -d
```

컨테이너 상태를 확인한다.

```bash
sudo docker compose ps
```

로그도 확인한다.

```bash
sudo docker logs -f mariadb
```

처음 실행할 때는 데이터 디렉터리를 초기화하느라 시간이 조금 걸릴 수 있다.
로그에 `ready for connections`와 비슷한 메시지가 보이면 접속 가능한 상태다.

---

## 7. Docker MariaDB 접속 테스트하기

호스트에서 Docker MariaDB에 접속해 본다.

```bash
mariadb -h 127.0.0.1 -P 3307 -u root -p
```

접속 후 간단히 DB 목록을 확인한다.

```sql
SHOW DATABASES;
```

종료한다.

```sql
exit;
```

여기까지 성공했다면 Docker MariaDB 자체는 정상적으로 실행 중이다.

---

## 8. 백업 파일 복원하기

이제 기존 MariaDB에서 만든 백업 파일을 Docker MariaDB로 복원한다.

먼저 `.env` 값을 현재 쉘에 불러온다.

```bash
cd /srv/mariadb-docker
set -a
. ./.env
set +a
```

복원한다.

```bash
sudo docker exec -i mariadb \
  mariadb -u root -p"$MARIADB_ROOT_PASSWORD" \
  < /backup/mariadb/all-databases.sql
```

데이터가 많으면 시간이 걸린다.
명령어가 끝날 때까지 기다린다.

복원 후 DB 목록을 확인한다.

```bash
sudo docker exec -it mariadb \
  mariadb -u root -p"$MARIADB_ROOT_PASSWORD" \
  -e "SHOW DATABASES;"
```

특정 테이블 개수도 확인해 본다.

```bash
sudo docker exec -it mariadb \
  mariadb -u root -p"$MARIADB_ROOT_PASSWORD" \
  -e "SELECT COUNT(*) FROM app_db.users;"
```

`app_db.users`는 예시다.
실제 DB 이름과 테이블 이름으로 바꿔야 한다.

---

## 9. 애플리케이션을 임시 포트로 테스트하기

가능하다면 애플리케이션 설정을 잠깐 바꿔서 Docker MariaDB를 테스트한다.

기존 설정이 아래와 같았다면

```text
DB_HOST=127.0.0.1
DB_PORT=3306
```

테스트용으로 이렇게 바꾼다.

```text
DB_HOST=127.0.0.1
DB_PORT=3307
```

확인할 내용은 다음과 같다.

1. 애플리케이션이 정상적으로 시작되는가?
2. 로그인, 조회, 등록, 수정, 삭제가 되는가?
3. 한글이 깨지지 않는가?
4. 시간 값이 이상하게 바뀌지 않았는가?
5. 배치 프로그램이나 스케줄러가 DB에 접속하는가?

특히 한글 데이터가 많은 서비스라면 문자셋을 꼭 확인해야 한다.

```sql
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
```

---

## 10. 최종 전환하기

테스트가 끝났다면 이제 실제 전환을 한다.

먼저 애플리케이션을 잠시 멈춘다.

```bash
sudo systemctl stop myapp
```

`myapp`은 예시다.
Apache, Tomcat, Spring Boot, Node.js 등 본인 서비스 이름에 맞게 바꾼다.

기존 호스트 MariaDB를 멈춘다.

```bash
sudo systemctl stop mariadb
```

부팅 시 자동 실행도 막는다.

```bash
sudo systemctl disable mariadb
```

Docker Compose 파일에서 포트를 `3306`으로 바꾼다.

```yaml
ports:
  - "3306:3306"
```

Docker MariaDB를 재시작한다.

```bash
cd /srv/mariadb-docker
sudo docker compose down
sudo docker compose up -d
```

3306 포트로 접속되는지 확인한다.

```bash
mariadb -h 127.0.0.1 -P 3306 -u root -p
```

문제가 없으면 애플리케이션 설정을 다시 `3306`으로 맞추고 실행한다.

```bash
sudo systemctl start myapp
```

애플리케이션 로그를 확인한다.

```bash
sudo journalctl -u myapp -f
```

---

## 11. 롤백 방법

전환 후 문제가 생기면 당황하지 말고 기존 MariaDB로 되돌릴 수 있어야 한다.

Docker MariaDB를 멈춘다.

```bash
cd /srv/mariadb-docker
sudo docker compose down
```

기존 호스트 MariaDB를 다시 켠다.

```bash
sudo systemctl enable mariadb
sudo systemctl start mariadb
```

애플리케이션 설정을 기존 DB 기준으로 되돌린 뒤 서비스를 재시작한다.

```bash
sudo systemctl restart myapp
```

그래서 이전 작업 전에는 기존 MariaDB 패키지와 데이터 디렉터리를 바로 삭제하지 않는 것이 좋다.
며칠 정도 안정화 기간을 두고, 문제가 없다는 확신이 생긴 뒤 정리한다.

---

## 자주 만나는 문제

### 3306 포트가 이미 사용 중이라고 나오는 경우

기존 호스트 MariaDB가 실행 중이면 Docker MariaDB가 같은 포트를 사용할 수 없다.

확인한다.

```bash
sudo ss -lntp | grep 3306
```

테스트 단계에서는 `3307:3306`을 사용하고, 최종 전환 때 기존 MariaDB를 멈춘 뒤 `3306:3306`으로 바꾸면 된다.

### 컨테이너를 지웠더니 DB도 사라질까 걱정되는 경우

이 글의 Compose 파일은 아래 볼륨을 사용한다.

```yaml
volumes:
  - ./data:/var/lib/mysql
```

따라서 컨테이너를 지워도 `/srv/mariadb-docker/data`가 남아 있으면 DB 파일은 남아 있다.
하지만 `data` 디렉터리를 삭제하면 실제 데이터가 삭제되므로 주의해야 한다.

### .env 값을 바꿨는데 DB 비밀번호가 바뀌지 않는 경우

MariaDB Docker 이미지는 처음 데이터 디렉터리를 초기화할 때 환경 변수를 사용한다.
이미 `./data` 안에 DB가 만들어진 뒤에는 `.env`를 바꿔도 기존 root 비밀번호가 자동으로 바뀌지 않는다.

비밀번호 변경은 MariaDB에 접속해서 SQL로 처리해야 한다.

```sql
ALTER USER 'root'@'%' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### 복원 후 계정 접속이 안 되는 경우

기존 MariaDB의 사용자는 `'user'@'localhost'`로 만들어져 있을 수 있다.
Docker 환경에서는 접속 위치가 달라져서 권한이 맞지 않을 수 있다.

사용자 정보를 확인한다.

```sql
SELECT User, Host FROM mysql.user;
```

필요하면 애플리케이션용 계정을 새로 만든다.

```sql
CREATE USER 'app_user'@'%' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON app_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
```

운영 서버에서는 `%` 대신 실제 애플리케이션 컨테이너 네트워크나 접속 범위에 맞게 제한하는 것이 더 안전하다.

---

## 운영 시 추천 관리 명령어

컨테이너 상태 확인:

```bash
cd /srv/mariadb-docker
sudo docker compose ps
```

로그 확인:

```bash
sudo docker logs -f mariadb
```

재시작:

```bash
sudo docker compose restart
```

중지:

```bash
sudo docker compose down
```

수동 백업:

```bash
cd /srv/mariadb-docker
set -a
. ./.env
set +a

sudo docker exec mariadb \
  mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" \
  --all-databases \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  > /backup/mariadb/docker-all-databases.sql
```

---

## 정리

호스트 MariaDB를 Docker MariaDB로 옮길 때 핵심은 단순하다.

1. 기존 DB를 먼저 안전하게 백업한다.
2. Docker MariaDB는 처음에 `3307` 같은 임시 포트로 띄운다.
3. 백업 파일을 복원하고 데이터와 애플리케이션 동작을 확인한다.
4. 마지막에 기존 MariaDB를 멈추고 `3306` 포트를 Docker MariaDB로 넘긴다.
5. 안정화 전까지 기존 MariaDB 데이터는 지우지 않는다.

Docker로 옮겼다고 백업이 자동으로 해결되는 것은 아니다.
컨테이너 환경에서도 정기 백업, 복원 테스트, 로그 확인은 계속 필요하다.

하지만 Compose 파일과 데이터 디렉터리를 명확히 분리해두면, 서버 이전이나 재구성이 훨씬 쉬워진다.

---

## 참고 문서

- [MariaDB Docker Official Image - Docker Hub](https://hub.docker.com/_/mariadb)
- [MariaDB Docker Official Image Environment Variables](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables)
- [Docker Volumes Documentation](https://docs.docker.com/engine/storage/volumes/)
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
