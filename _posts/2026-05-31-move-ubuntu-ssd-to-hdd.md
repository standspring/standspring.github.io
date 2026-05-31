---
title: "Ubuntu 22.04 웹서버를 SSD에서 HDD로 옮기는 방법"
description: "SSD에 설치된 Ubuntu 22.04 웹서버를 HDD로 이전하는 전체 절차를 정리합니다. Apache, Tomcat 서버 운영 환경에서 rsync 복사, fstab 수정, GRUB 설치, 부팅 확인, 서비스 점검 방법까지 다룹니다."
date: 2026-05-31
categories: [Linux, Server]
tags: [Ubuntu, Ubuntu 22.04, SSD, HDD, Apache, Tomcat, rsync, GRUB, fstab, 웹서버]
---

![Ubuntu 22.04 웹서버 SSD에서 HDD로 이전 인포그래픽](/assets/img/2026-05-31-move-ubuntu-ssd-to-hdd.png)

SSD에 Ubuntu 22.04를 설치해서 Apache와 Tomcat 웹서버로 운영하고 있다.
그런데 웹서버는 로그, 캐시, 임시 파일, 업로드 파일 때문에 디스크 read/write가 계속 발생한다.

요즘 SSD는 내구성이 좋아서 일반적인 서버 운영 정도로는 쉽게 수명이 다하지 않는다.
하지만 로그가 많거나 장기간 운영하는 서버라면 SSD 쓰기 수명이 신경 쓰일 수 있다.
이럴 때는 Ubuntu 전체를 HDD로 옮기거나, 쓰기 작업이 많은 디렉터리만 HDD로 분리하는 방법을 고려할 수 있다.

이 글에서는 SSD에 설치된 Ubuntu 22.04 웹서버를 HDD로 옮기는 방법을 정리한다.

---

## 작업 전 주의사항

디스크 이전 작업은 실수하면 부팅이 안 되거나 데이터가 손실될 수 있다.
반드시 중요한 데이터는 먼저 백업해야 한다.

특히 아래 경로는 따로 백업해두는 것을 추천한다.

```bash
/etc/apache2/
/etc/tomcat*/
/var/www/
/opt/tomcat/
/var/lib/tomcat*/
/etc/systemd/system/
/home/
```

MySQL이나 MariaDB를 사용 중이라면 데이터베이스도 백업한다.

```bash
mysqldump -u root -p --all-databases > all-databases.sql
```

이 글에서는 기존 SSD가 `/dev/sda`, 새 HDD가 `/dev/sdb`라고 가정한다.
실제 장치명은 서버마다 다르므로 반드시 직접 확인해야 한다.

---

## 전체 작업 흐름

작업 순서는 다음과 같다.

1. HDD를 서버에 장착한다.
2. HDD에 파티션을 만든다.
3. HDD를 포맷한다.
4. SSD의 Ubuntu 시스템 전체를 HDD로 복사한다.
5. HDD의 `/etc/fstab`을 수정한다.
6. GRUB 부트로더를 HDD에 설치한다.
7. BIOS 또는 UEFI에서 HDD로 부팅하도록 설정한다.
8. Apache와 Tomcat 동작을 확인한다.

---

## 현재 디스크 확인하기

먼저 현재 디스크 구성을 확인한다.

```bash
lsblk
```

예를 들어 다음과 같이 나올 수 있다.

```text
NAME   SIZE TYPE MOUNTPOINT
sda    240G disk
├─sda1 512M part /boot/efi
└─sda2 239G part /
sdb      1T disk
```

위 예시에서는 `sda`가 기존 SSD이고, `sdb`가 새로 옮길 HDD다.

디스크 이름을 착각하면 기존 데이터를 지울 수 있다.
`lsblk`, `blkid`, `fdisk -l` 등을 이용해서 대상 디스크를 정확히 확인한 뒤 진행해야 한다.

```bash
sudo fdisk -l
```

---

## HDD 파티션 만들기

UEFI 부팅 환경을 기준으로 HDD에 EFI 파티션과 루트 파티션을 만든다.

```bash
sudo parted /dev/sdb
```

`parted` 안에서 다음 명령을 입력한다.

```text
mklabel gpt
mkpart ESP fat32 1MiB 513MiB
set 1 esp on
mkpart primary ext4 513MiB 100%
quit
```

그러면 대략 다음 구조가 된다.

```text
/dev/sdb1  EFI 파티션
/dev/sdb2  Ubuntu 루트 파티션
```

기존 서버가 BIOS 부팅 방식이라면 구성이 달라질 수 있다.
요즘 Ubuntu 서버는 대부분 UEFI 환경이 많으므로 이 글에서는 UEFI 기준으로 진행한다.

---

## HDD 포맷하기

EFI 파티션은 FAT32로 포맷한다.

```bash
sudo mkfs.vfat -F32 /dev/sdb1
```

루트 파티션은 ext4로 포맷한다.

```bash
sudo mkfs.ext4 /dev/sdb2
```

이 명령은 해당 파티션의 데이터를 모두 삭제한다.
반드시 새 HDD의 파티션이 맞는지 다시 확인하고 실행해야 한다.

---

## HDD 마운트하기

복사 작업을 위해 HDD 파티션을 임시로 마운트한다.

```bash
sudo mkdir -p /mnt/newroot
sudo mount /dev/sdb2 /mnt/newroot
```

EFI 파티션도 마운트한다.

```bash
sudo mkdir -p /mnt/newroot/boot/efi
sudo mount /dev/sdb1 /mnt/newroot/boot/efi
```

---

## SSD의 Ubuntu 시스템을 HDD로 복사하기

`rsync`를 사용해서 현재 시스템을 HDD로 복사한다.

```bash
sudo rsync -aAXHv \
  --exclude=/dev/* \
  --exclude=/proc/* \
  --exclude=/sys/* \
  --exclude=/tmp/* \
  --exclude=/run/* \
  --exclude=/mnt/* \
  --exclude=/media/* \
  --exclude=/lost+found \
  / /mnt/newroot/
```

주요 옵션의 의미는 다음과 같다.

| 옵션 | 의미 |
| --- | --- |
| `-a` | 파일 권한, 소유자, 심볼릭 링크 등을 보존 |
| `-A` | ACL 보존 |
| `-X` | 확장 속성 보존 |
| `-H` | 하드 링크 보존 |
| `-v` | 진행 내용 출력 |

이 방식으로 복사하면 Apache 설정, Tomcat 설정, 사용자 파일, systemd 서비스 파일까지 대부분 그대로 옮겨진다.

---

## 새 HDD의 UUID 확인하기

새 파티션의 UUID를 확인한다.

```bash
sudo blkid
```

예시는 다음과 같다.

```text
/dev/sdb1: UUID="AAAA-BBBB" TYPE="vfat"
/dev/sdb2: UUID="1111-2222-3333-4444" TYPE="ext4"
```

여기서 `/dev/sdb1`은 EFI 파티션이고, `/dev/sdb2`는 루트 파티션이다.
이 UUID를 새 시스템의 `/etc/fstab`에 반영해야 한다.

---

## HDD의 fstab 수정하기

새로 복사된 HDD 안의 `fstab` 파일을 연다.

```bash
sudo nano /mnt/newroot/etc/fstab
```

기존 SSD의 UUID로 되어 있는 부분을 HDD의 UUID로 바꾼다.

예를 들어 다음과 같이 수정한다.

```text
UUID=1111-2222-3333-4444 / ext4 errors=remount-ro 0 1
UUID=AAAA-BBBB /boot/efi vfat umask=0077 0 1
```

기존 SSD의 UUID가 남아 있으면 HDD로 부팅했을 때 루트 파일시스템을 찾지 못할 수 있다.

---

## chroot 환경으로 들어가기

GRUB를 설치하기 위해 새 HDD 시스템 안으로 들어간다.

먼저 필요한 시스템 디렉터리를 바인드 마운트한다.

```bash
sudo mount --bind /dev /mnt/newroot/dev
sudo mount --bind /proc /mnt/newroot/proc
sudo mount --bind /sys /mnt/newroot/sys
sudo mount --bind /run /mnt/newroot/run
```

그리고 `chroot`로 들어간다.

```bash
sudo chroot /mnt/newroot
```

이제 명령 프롬프트는 새 HDD 시스템 내부를 기준으로 동작한다.

---

## GRUB 부트로더 설치하기

UEFI 환경이라면 다음 명령을 실행한다.

```bash
grub-install /dev/sdb
update-grub
```

설치가 끝나면 `chroot`에서 빠져나온다.

```bash
exit
```

마운트한 디렉터리도 정리한다.

```bash
sudo umount /mnt/newroot/run
sudo umount /mnt/newroot/sys
sudo umount /mnt/newroot/proc
sudo umount /mnt/newroot/dev
sudo umount /mnt/newroot/boot/efi
sudo umount /mnt/newroot
```

만약 `target is busy` 메시지가 나오면 해당 경로를 사용하는 프로세스가 없는지 확인한 뒤 다시 언마운트한다.

---

## BIOS 또는 UEFI에서 HDD 부팅 설정하기

서버를 재부팅한 뒤 BIOS 또는 UEFI 설정 화면으로 들어간다.

부팅 순서에서 새 HDD를 SSD보다 우선순위가 높게 설정한다.
설정을 저장한 뒤 재부팅한다.

```bash
sudo reboot
```

---

## HDD로 정상 부팅되었는지 확인하기

부팅 후 루트 파일시스템이 어떤 디스크에서 올라왔는지 확인한다.

```bash
lsblk
```

또는 다음 명령으로 `/`가 어떤 장치인지 확인한다.

```bash
df -h /
```

HDD에 해당하는 파티션이 `/`로 마운트되어 있다면 정상적으로 이전된 것이다.

---

## Apache 동작 확인하기

Apache 상태를 확인한다.

```bash
sudo systemctl status apache2
```

서비스가 실행 중이 아니라면 시작한다.

```bash
sudo systemctl start apache2
```

부팅 시 자동 실행도 확인한다.

```bash
sudo systemctl enable apache2
```

로컬에서 웹 페이지가 열리는지도 확인한다.

```bash
curl http://localhost
```

---

## Tomcat 동작 확인하기

Tomcat은 설치 방식에 따라 서비스 이름이 다를 수 있다.

먼저 Tomcat 관련 서비스를 확인한다.

```bash
systemctl list-units --type=service | grep tomcat
```

예를 들어 서비스 이름이 `tomcat9`라면 다음과 같이 확인한다.

```bash
sudo systemctl status tomcat9
```

실행되지 않았다면 시작한다.

```bash
sudo systemctl start tomcat9
sudo systemctl enable tomcat9
```

Tomcat 기본 포트도 확인한다.

```bash
curl http://localhost:8080
```

---

## 로그와 권한 확인하기

웹서버 이전 후에는 로그 디렉터리 권한 문제로 서비스가 실패하는 경우가 있다.

Apache 로그는 보통 다음 위치에 있다.

```text
/var/log/apache2/
```

Tomcat 로그는 설치 방식에 따라 다르지만 보통 다음 중 하나다.

```text
/var/log/tomcat9/
/opt/tomcat/logs/
```

서비스가 실패하면 다음 명령으로 원인을 확인한다.

```bash
journalctl -xe
```

Apache 로그도 확인한다.

```bash
sudo tail -n 100 /var/log/apache2/error.log
```

Tomcat 로그도 확인한다.

```bash
sudo tail -n 100 /var/log/tomcat9/catalina.out
```

---

## 대안: 전체 이전 대신 쓰기 많은 디렉터리만 HDD로 옮기기

SSD 수명이 걱정된다고 해서 꼭 Ubuntu 전체를 HDD로 옮겨야 하는 것은 아니다.

운영체제와 프로그램은 SSD에 그대로 두고, 쓰기 작업이 많은 디렉터리만 HDD로 분리하는 방식도 좋다.
이 방법은 SSD의 빠른 부팅 속도와 프로그램 실행 속도를 유지하면서, 로그나 업로드 파일처럼 자주 쓰는 데이터만 HDD에 저장할 수 있다.

분리 대상으로는 다음 경로를 고려할 수 있다.

```text
/var/log
/var/cache
/var/tmp
/var/www
/opt/tomcat/logs
```

예를 들어 `/var/log`를 HDD로 옮기려면 HDD 파티션을 별도 위치에 마운트한 뒤 기존 로그를 복사하고, `/etc/fstab`에 등록해서 부팅 시 자동 마운트되도록 구성할 수 있다.

서버 성능까지 고려하면 개인적으로는 Ubuntu 전체를 HDD로 옮기기 전에 이 방식을 먼저 검토하는 것을 추천한다.

---

## 마무리

SSD에서 HDD로 Ubuntu 22.04 서버를 옮기는 핵심은 다음 네 가지다.

```text
1. rsync로 시스템 전체 복사
2. 새 디스크 UUID에 맞게 /etc/fstab 수정
3. 새 디스크에 GRUB 설치
4. BIOS 또는 UEFI 부팅 순서 변경
```

Apache와 Tomcat은 시스템 파일과 설정 파일이 정상적으로 복사되었다면 대부분 그대로 동작한다.
다만 디스크 UUID, 파일 권한, 서비스 자동 실행 여부, 로그 경로는 반드시 확인해야 한다.

SSD 수명이 걱정된다면 전체 시스템을 HDD로 옮길 수 있다.
하지만 성능까지 함께 고려한다면 `/var/log`, `/var/www`, Tomcat 로그, 업로드 디렉터리처럼 쓰기 작업이 많은 경로만 HDD로 분리하는 방식도 충분히 좋은 선택이다.
