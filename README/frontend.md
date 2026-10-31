# Frontend 실행 방법

Flutter 기반 모바일 앱. `frontend/trender/` 디렉토리 기준.

## 1. 사전 준비

- Flutter SDK 설치 (`pubspec.yaml` 기준 `sdk: ^3.13.2` 이상)
- Android Studio(에뮬레이터) 또는 실기기 / Xcode(iOS 시뮬레이터, macOS만)

설치 확인:

```bash
flutter doctor
```

## 2. 패키지 설치

```bash
cd frontend/trender
flutter pub get
```

## 3. 백엔드 API 주소 연결 (중요)

현재 [lib/service/auth_service.dart](../frontend/trender/lib/service/auth_service.dart)의 `baseUrl`이 특정 ngrok 주소로 하드코딩되어 있다.

```dart
final String baseUrl = 'https://edging-feminism-fox.ngrok-free.dev/api/auth';
```

로컬 백엔드([backend.md](backend.md)로 띄운 서버)에 붙이려면 이 값을 아래 중 하나로 바꿔야 한다.

- 에뮬레이터에서 로컬 PC의 Django 서버에 붙이는 경우: `http://10.0.2.2:8000/api/auth` (Android 에뮬레이터 기준)
- 실기기에서 붙이는 경우: 같은 네트워크의 PC IP, 또는 `ngrok http 8000`으로 새 터널을 만들어 그 주소로 교체

## 4. 실행

```bash
flutter run
```

기기를 여러 개 인식하면 `flutter devices`로 확인 후 `flutter run -d <device_id>`로 지정한다.

## 참고

- 상태관리: `provider`
- 토큰 저장: `flutter_secure_storage` (JWT access/refresh 토큰)
- 화면 구성: `lib/view/` (로그인/회원가입/스플래시/메인), `lib/view_model/` (Provider 기반 뷰모델)
