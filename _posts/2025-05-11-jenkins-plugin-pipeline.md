---
title: "Jenkins Pipeline 사용법 가이드"
date: 2025-05-11
category: jenkins
tags: [jenkins, plugin, pipeline]
---

# Jenkins Pipeline 사용법 가이드

Jenkins Pipeline은 CI/CD 흐름을 코드로 정의하여 더욱 효율적이고 일관성 있는 자동화 작업을 가능하게 합니다. 이 문서에서는 Pipeline 플러그인의 역할, 기본 구조, 주요 기능, 예제까지 자세히 소개합니다.

---

## ✅ Jenkins Pipeline이란?

Pipeline은 Jenkins의 Job 단계를 코드 기반으로 구성할 수 있게 해주는 기능입니다. 이를 통해 복잡한 빌드/테스트/배포 흐름을 자동화하고 관리할 수 있습니다.

- 선언형 파이프라인(`Declarative Pipeline`)과 스크립트형(`Scripted Pipeline`) 두 가지 방식이 있음
- Jenkinsfile로 버전 관리가 가능
- 시각적인 파이프라인 확인을 위해 **Blue Ocean** 과 함께 활용 가능


---

## 🔧 Jenkinsfile 기본 구조 (선언형)

```groovy
pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        echo '빌드 실행 중...'
      }
    }

    stage('Test') {
      steps {
        echo '테스트 실행 중...'
      }
    }
  }

  post {
    always {
      echo '작업 완료'
    }
  }
}
```

---

## 🔧 환경변수, 인증 처리, 알림 연동 포함한 예제

```groovy
pipeline {
  agent any

  environment {
    GITHUB_TOKEN = credentials('github-token')
  }

  stages {
    stage('Clone') {
      steps {
        git url: 'https://github.com/your-repo/project.git', branch: 'main'
      }
    }

    stage('Build') {
      steps {
        ansiColor('xterm') {
          sh 'echo "\u001B[34mBuilding project...\u001B[0m"'
          sh './build.sh'
        }
      }
    }

    stage('Test') {
      steps {
        sh './run_tests.sh'
        junit 'reports/**/*.xml'
      }
    }

    stage('Notify') {
      steps {
        slackSend (
          channel: '#build-status',
          color: '#00FF00',
          message: "✅ Build passed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        )
      }
    }
  }

  post {
    failure {
      slackSend (
        channel: '#build-status',
        color: '#FF0000',
        message: "❌ Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
      )
    }
    always {
      echo '🎯 파이프라인 완료'
    }
  }
}
```

---

## 🔌 관련 플러그인 목록

| 플러그인                   | 설명                              |
| -------------------------- | --------------------------------- |
| Pipeline                   | Jenkinsfile 기반 파이프라인 실행  |
| Git Plugin                 | Git 저장소와의 연동 지원          |
| Blue Ocean                 | 시각적인 파이프라인 UI 제공       |
| AnsiColor Plugin           | 콘솔 출력 색상 적용               |
| Credentials Binding Plugin | 환경 변수로 보안 자격증명 설정    |
| JUnit Plugin               | 테스트 결과 시각화 및 리포트 제공 |
| Slack Notification Plugin  | Slack 채널로 빌드 결과 전송       |

---

## 🔎 추가 참고자료

- 공식 문서: [Jenkins Pipeline 문서](https://www.jenkins.io/doc/book/pipeline/)
- Blue Ocean UI: [Blue Ocean 소개](https://www.jenkins.io/doc/book/blueocean/)
