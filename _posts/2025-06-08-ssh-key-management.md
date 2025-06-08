---
title: "ssh key 관리 팁"
date: 2025-06-08
category: ssh
tags: [ssh, ssh-keygen, sshkey, ssh-key, ssh-key-commnet]
---

## 🔧 1. SSH Key 관리 팁

SSH Key는 생성 후에도 꾸준한 관리가 필요합니다. 관리가 제대로 되지 않으면 오히려 보안 허점이 될 수 있습니다.

### 🗂️ 1) 여러 키를 사용할 경우 `~/.ssh/config` 활용

여러 원격 서버 혹은 Git 계정을 사용할 경우, 아래와 같이 키마다 별도 설정 가능:

```ini
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github

Host company-server
    HostName 192.168.0.10
    User ubuntu
    IdentityFile ~/.ssh/id_rsa_company
```

* `Host`: 사용할 별칭 (ssh 접속 시 `ssh github.com`처럼 사용 가능)
* `IdentityFile`: 연결 시 사용할 개인키 경로 지정

### 🔄 2) 주기적인 키 교체

* 6개월\~1년 단위로 키를 재발급하고 교체하는 것이 바람직
* 만약 키가 유출되었거나 사용처가 명확하지 않다면 즉시 폐기

### 🔒 3) 개인키 보호 수칙

* 절대 공유하거나 이메일로 전송하지 말 것
* 파일 권한은 `600` (읽기/쓰기)로 제한

```bash
chmod 600 ~/.ssh/id_ed25519
```

* 가능하면 패스프레이즈를 설정하여 추가 보안 적용

### 🧼 4) 사용하지 않는 공개키 정리

* 서버의 `~/.ssh/authorized_keys` 파일에서 더 이상 사용하지 않는 키는 주기적으로 삭제
* 키 주석(comment)을 잘 정리해두면 어떤 키인지 식별이 쉬움

#### 📝 키 주석(comment) 관리 방법

SSH Key를 생성할 때 `-C` 옵션으로 주석을 추가할 수 있습니다. 이 주석은 공개키 파일에 포함되며, 누가 어떤 용도로 생성한 키인지 구분하는 데 매우 유용합니다.

예시:

```bash
ssh-keygen -t ed25519 -C "yuri@dev-machine-2025"
```

생성된 공개키 파일 (`id_ed25519.pub`) 예:

```
ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKcJNk... yuri@dev-machine-2025
```

또는 만료일을 포함하여 다음과 같이 구성할 수도 있습니다:

```bash
ssh-keygen -t ed25519 -C "yuri@laptop (expire:2025-12-31)"
```

이렇게 하면 `authorized_keys` 파일을 관리할 때 누구의 키인지 쉽게 확인하고 만료 시점도 함께 추적할 수 있습니다.

* 서버의 `~/.ssh/authorized_keys` 파일에서 더 이상 사용하지 않는 키는 주기적으로 삭제
* 키 주석(comment)을 잘 정리해두면 어떤 키인지 식별이 쉬움

> ✅ 요약: SSH Key도 자산처럼 관리해야 합니다. 보안과 유지보수를 위해 체계적인 관리 습관이 필요합니다.

---

## 🏢 2. 실무 환경에서의 SSH Key 관리 사례

기업이나 조직에서는 수십\~수백 명의 개발자가 서버에 접근할 수 있기 때문에, SSH Key 관리 체계가 매우 중요합니다.

### 🏛️ 1) 중앙 집중형 Key 관리 도구 사용

* **HashiCorp Vault**: Key 저장, 접근 제어, 만료 관리 가능
* **AWS Secrets Manager / Parameter Store**: IAM 기반 권한 관리와 통합
* **Ansible + GitOps**: 서버 접속 키를 Git으로 관리하고 Ansible로 배포

### 🔁 2) Key Rotation 정책 수립

* 정기적으로 키를 폐기하고 재등록하는 규칙을 마련
* 퇴사자나 외부 협력자의 접근을 즉시 차단할 수 있도록 자동화

### 📋 3) 접속 로그 및 감사 기록 확보

* SSH 접속 시 로그를 남겨 누가 언제 어떤 서버에 접속했는지 추적 가능하게 함
* 보안 사고 발생 시 추적이 가능해야 함

### 🧩 4) LDAP 또는 SSO와의 연동

* 직원 계정이 LDAP 또는 SSO에 의해 관리된다면, SSH Key 접근권한도 해당 시스템과 연동
* 계정 비활성화 시 자동으로 키 접근도 차단

> 🔐 실제 사례: 모 기업은 키 주석에 사용자 이메일과 만료일을 명시해 두고, 배치 스크립트를 통해 만료된 키를 자동으로 제거하는 시스템을 도입함

---
