# Frontend 가이드

Flutter Web 앱입니다. 이 문서의 명령은 별도 표기가 없으면 `frontend/` 디렉터리 기준입니다.

## 목차

- [사전 준비](#사전-준비)
- [실행](#실행)
- [Google 로그인 설정](#google-로그인-설정)
- [배포 빌드](#배포-빌드)
- [구성](#구성)
- [문제 해결](#문제-해결)

## 사전 준비

Flutter 버전은 FVM으로 고정되어 있습니다 (`.fvmrc`, Flutter 3.47.9). 시스템에 설치된 다른 버전의 Flutter와 충돌하지 않도록 모든 명령은 `fvm flutter`로 실행합니다.

```bat
dart pub global activate fvm
fvm install
fvm flutter pub get
```

VS Code에서는 `.vscode/settings.json`의 `dart.flutterSdkPath`를 FVM이 설치한 SDK 경로로 지정합니다.

```json
{
  "dart.flutterSdkPath": "C:\\Users\\<사용자>\\fvm\\versions\\3.47.9"
}
```

## 실행

백엔드가 `localhost:8000`에서 실행 중이어야 합니다. 저장소 루트에서 다음을 실행합니다.

```bat
scripts\web.bat
```

Chrome에서 http://localhost:3000 으로 앱이 열립니다. 직접 실행하는 경우는 다음과 같습니다.

```bat
fvm flutter run -d chrome --web-port 3000 --dart-define=API_BASE_URL=http://localhost:8000
```

| 설정 | 기본값 | 설명 |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | 백엔드 주소. `--dart-define`으로 지정하며, `web.bat`은 같은 이름의 환경변수를 읽습니다 |
| 웹 포트 | `3000` | Google OAuth의 승인된 JavaScript 원본과 일치해야 하므로 고정합니다 |

다른 백엔드에 연결하려면 다음과 같이 실행합니다.

```bat
set API_BASE_URL=https://api.example.com
scripts\web.bat
```

## Google 로그인 설정

클라이언트 ID는 백엔드 `.env`의 `GOOGLE_CLIENT_ID` 한 곳에서 관리합니다. 웹은 시작할 때 `GET /api/auth/google/`로 값을 받아오므로 프론트엔드 빌드 옵션은 필요하지 않습니다.

1. Google Cloud Console의 API 및 서비스 > 사용자 인증 정보에서 OAuth 클라이언트 ID를 만듭니다. 애플리케이션 유형은 웹 애플리케이션입니다.
2. 승인된 JavaScript 원본에 `http://localhost:3000`과 배포 주소를 추가합니다. 리디렉션 URI는 필요하지 않습니다.
3. OAuth 동의 화면이 테스트 모드이면 로그인할 계정을 테스트 사용자로 등록합니다.
4. 발급된 클라이언트 ID를 `backend/.env`의 `GOOGLE_CLIENT_ID`에 넣고 백엔드를 다시 시작합니다.

동작 방식은 다음과 같습니다.

- 로그인 화면에 Google Identity Services의 공식 버튼이 표시됩니다. `GOOGLE_CLIENT_ID`가 비어 있으면 비활성 버튼이 표시됩니다.
- 백엔드는 ID 토큰의 서명, 만료, 대상(`aud`), 이메일 인증 여부를 검증한 뒤 일반 로그인과 같은 JWT를 발급합니다.
- 같은 이메일의 계정이 있으면 해당 계정으로 로그인하고, 없으면 비밀번호 없는 계정을 새로 만듭니다.

## 배포 빌드

```bat
fvm flutter build web --release --dart-define=API_BASE_URL=https://api.example.com
fvm flutter build web --release --wasm --dart-define=API_BASE_URL=https://api.example.com
```

- 결과물 `build/web/`을 정적 호스팅(Nginx, Firebase Hosting, S3 등)에 배포합니다.
- 하위 경로에 배포하면 `--base-href /경로/`를 지정합니다.
- 배포 주소를 백엔드 `.env`의 `CORS_ALLOWED_ORIGINS`와 Google OAuth의 승인된 JavaScript 원본에 추가합니다.

## 구성

| 구분 | 내용 |
|---|---|
| 상태 관리 | `provider` (View - ViewModel - Service 구조) |
| 네트워크 | `http`. [api_client.dart](../frontend/lib/core/network/api_client.dart)가 JWT 헤더 추가와 만료 시 자동 갱신을 처리 |
| 저장소 | `shared_preferences` (브라우저 localStorage). 키: `flutter.jwt_token`, `flutter.refresh_token`, `flutter.theme_mode` |
| Google 로그인 | `google_sign_in`, `google_sign_in_web`. [google_sign_in_service.dart](../frontend/lib/service/google_sign_in_service.dart) |
| 외부 링크 | `url_launcher`. 뉴스 원문을 새 탭으로 엽니다 |
| 반응형 | 폭 840px 이상은 좌측 NavigationRail, 미만은 하단 탭바. 콘텐츠 최대 폭은 [responsive_center.dart](../frontend/lib/widgets/responsive_center.dart)에서 제한 |

파일별 역할은 [lib/readme.md](../frontend/lib/readme.md)를 참고하세요.

## 문제 해결

| 증상 | 원인과 조치 |
|---|---|
| `pub get`에서 SDK 버전 오류 | 시스템 Flutter가 실행되었습니다. `fvm flutter`로 실행합니다 |
| `fvm use` 실행 시 심볼릭 링크 오류 (1314) | Windows 개발자 모드가 꺼져 있습니다. `fvm flutter`는 링크 없이 동작하므로 무시해도 됩니다 |
| 화면이 로그인에서 넘어가지 않거나 네트워크 오류 | 백엔드 실행 여부와 `API_BASE_URL`을 확인합니다 |
| Google 버튼이 비활성 상태 | 백엔드 `.env`의 `GOOGLE_CLIENT_ID`가 비어 있거나 백엔드가 재시작되지 않았습니다 |
| Google 팝업에서 `origin_mismatch` 오류 | 승인된 JavaScript 원본에 현재 주소와 포트가 등록되어 있지 않습니다 |
| 패키지 추가 후 실행 오류 | 실행 중인 앱은 핫 리로드로 새 패키지를 반영하지 못합니다. 앱을 다시 실행합니다 |
