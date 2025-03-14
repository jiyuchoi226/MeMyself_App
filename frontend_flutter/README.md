# MeMyself 앱

## 개요

MeMyself는 사용자 활동과 감정을 기반으로 맞춤형 인사이트와 회고를 제공하는 고급 Flutter 애플리케이션입니다. 이 문서는 개발 환경 설정, 앱의 기능, 의존성 관리에 대한 포괄적인 가이드를 제공합니다.

## 목차

1. [환경 설정](#환경-설정)
2. [기능](#기능)
3. [의존성](#의존성)
4. [Gitignore 세부사항](#gitignore-세부사항)
5. [버전 관리](#버전-관리)

## 환경 설정

원활한 개발 환경을 위해 다음 단계를 따라 설정하세요:

### 사전 준비

- **Flutter SDK**: 버전 3.0.0 이상
- **Dart SDK**: Flutter와 함께 제공
- **Android Studio** 또는 **Visual Studio Code**: Flutter 플러그인 설치
- **Xcode**: iOS 개발을 위한 필수 도구 (macOS 사용자)

### 설치 및 설정

1. **Flutter 설치**: [Flutter 공식 사이트](https://flutter.dev/docs/get-started/install)에서 설치 가이드를 따르세요.
2. **의존성 설치**: 프로젝트 루트에서 `flutter pub get` 명령어를 실행하여 모든 패키지를 설치하세요.
3. **Firebase 설정**: `google-services.json` 및 `GoogleService-Info.plist` 파일을 `android/app` 및 `ios/Runner` 디렉토리에 각각 추가하세요.
4. **환경 변수 설정**: `.env` 파일을 생성하고 필요한 API 키와 시크릿을 추가하세요.

## 기능

- **사용자 맞춤형 인사이트**: 사용자 활동과 감정을 분석하여 맞춤형 피드백 제공
- **주간 리포트**: 주간 활동과 감정에 대한 요약 리포트 생성
- **실시간 감정 분석**: 입력된 감정을 실시간으로 분석하여 피드백 제공
- **안전한 데이터 관리**: Firebase를 통한 안전한 사용자 데이터 저장 및 관리

## 의존성

- **Flutter**: UI 빌드를 위한 프레임워크
- **Firebase**: 인증 및 데이터베이스 관리
- **Hive**: 로컬 데이터 저장소
- **Flutter Bloc**: 상태 관리
- **Google Sign-In**: Google 계정 인증

## Gitignore 세부사항

- **Firebase 설정 파일**: `google-services.json`, `GoogleService-Info.plist`
- **API 키 및 시크릿**: `lib/core/constants/api_keys.dart`, `.env`
- **키스토어 파일**: `*.jks`, `*.keystore`, `key.properties`
- **빌드 출력물**: `/build/`, `.gradle/`
- **플랫폼별 민감한 파일**: iOS 및 Android 관련 설정 파일

## 버전 관리

- **Flutter SDK**: 3.0.0 이상
- **Dart SDK**: Flutter와 함께 제공
- **Firebase**: 최신 버전 사용 권장
- **Hive**: 2.0.0 이상

이 문서를 통해 MeMyself 앱의 개발 환경을 설정하고, 기능을 이해하며, 의존성을 관리하는 데 필요한 모든 정보를 얻을 수 있습니다.
