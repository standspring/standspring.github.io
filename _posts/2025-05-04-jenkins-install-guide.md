---
title: "Jenkins war 파일 이용해서 설치"
date: 2025-05-04
category: jenkins
tags: [jenkins, install, CI/CD, jenkins.war]
---

# Jenkins 설치 가이드

Jenkins는 오픈 소스 기반의 자동화 서버로, CI/CD(지속적 통합 및 배포) 파이프라인을 구현할 때 가장 널리 사용되는 도구 중 하나입니다. 이 포스트에서는 Ubuntu 기반 리눅스 환경에 Jenkins.war 파일을 이용하여 설치하는 방법을 소개합니다.

---

## 1. Java 설치
Jenkins는 Java 기반 애플리케이션이므로 먼저 Java를 설치해야 합니다.

```bash
# sudo apt update
# sudo apt install openjdk-17-jdk -y
# java -version
openjdk version "17.0.14" 2025-01-21
OpenJDK Runtime Environment (build 17.0.14+7-Ubuntu-124.04)
OpenJDK 64-Bit Server VM (build 17.0.14+7-Ubuntu-124.04, mixed mode, sharing)
```

`java -version` 수행 결과가 17이 아닐 경우, `update-alternatives` 명령을 통해 기본 java 버전을 변경할 수 있습니다.

```bash
# java -version
openjdk version "17.0.14" 2025-01-21
OpenJDK Runtime Environment (build 17.0.14+7-Ubuntu-124.04)
OpenJDK 64-Bit Server VM (build 17.0.14+7-Ubuntu-124.04, mixed mode, sharing)

# update-alternatives --config java
There are 2 choices for the alternative java (providing /usr/bin/java).

  Selection    Path                                         Priority   Status
------------------------------------------------------------
* 0            /usr/lib/jvm/java-17-openjdk-amd64/bin/java   1711      auto mode
  1            /usr/lib/jvm/java-11-openjdk-amd64/bin/java   1111      manual mode
  2            /usr/lib/jvm/java-17-openjdk-amd64/bin/java   1711      manual mode

Press <enter> to keep the current choice[*], or type selection number:
```

번호를 입력하고 엔터를 누르면 해당 Java 버전이 기본으로 설정됩니다.
`java -version` 수행하여 변경 결과를 확인합니다.


---

## 2. Jenkins 설치 (온라인)

### 🔹 1) Jenkins.war 다운로드
https://www.jenkins.io/download/ 에서 jenkins.war 다운로드합니다.

jenkin 의 home directory를 생성하고, 해당 위치에 jenkins.war 를 이동합니다.

```bash
# mkdir /home/path/jenkins/
# mv jenkins.war /home/path/jenkins/
```

### 🔹 2) 방화벽 포트 열기 (기본 포트: 8080)
기본 포트는 8080 이지만, 이 문서에서는 8090으로 진행하겠습니다.
```bash
# sudo ufw allow 8080
# sudo ufw status
```

### 🔹 3) jenkins 실행 테스트

```bash
# cd /home/path/jenkins/
# java -jar jenkins.war --httpPort=8090 -DJENKINS_HOME=/home/path/jenkins/jenkins_home --logfile=/home/path/jenkins/jenkins.log
```

jenkins.log 파일에 초기 비밀번호가 출력됩니다. 혹은 초기 비밀번호를 확인할 수 있는 파일(initialAdminPassword)의 위치가 표기됩니다.

initialAdminPassword 파일을 조회하면 비밀번호를 확인할 수 있습니다.
```bash
# sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

정상적으로 로딩이 완료되었다는 메시지를 확인하면, 브라우저에서 http://[IP]:8090 으로 접속하여 jenkins 초기 페이지를 확인할 수 있습니다.


---

## 3. Jenkins 실행 및 부팅 시 자동 실행 설정

부팅시마다 매번 java -jar 를 이용하여 실행하는 것이 번거로우므로, system service로 등록하여 자동 실행을 등록합니다.

```bash
# vi /etc/systemd/system/jenkins.service
[Unit]
Description=Jenkins Daemon
After=syslog.target network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/java -jar /home/path/jenkins/jenkins.war --httpPort=8090 -DJENKINS_HOME=/home/path/jenkins/jenkins_home --logfile=/home/path/jenkins/jenkins.log
Environment="JENKINS_HOME=/hoem/path/jenkins"
User=jenkins

[Install]
WantedBy=multi-user.target

# sudo systemctl start jenkins
# sudo systemctl enable jenkins
```

서비스 상태 확인:
```bash
sudo systemctl status jenkins
```

---

## 5. Jenkins 초기 설정
웹 브라우저에서 다음 주소에 접속:
```
http://<서버_IP>:8090
```

첫 실행 시 다음 명령어로 관리자 패스워드를 확인합니다:
```bash
# sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

이후 설치 마법사에서 권장 플러그인 설치 및 관리자 계정 생성을 진행합니다.

---

## 6. Jenkins 플러그인 설치 (수동)
- [Jenkins Plugin Index](https://plugins.jenkins.io/)에서 `.hpi` 파일을 다운로드합니다.
- `/home/path/jenkins/jenkins_home/plugins/` 경로에 `.hpi` 파일을 복사하고 Jenkins를 재시작합니다.

```bash
sudo cp my-plugin.hpi /home/path/jenkins/jenkins_home/plugins/
sudo systemctl restart jenkins
```

---
