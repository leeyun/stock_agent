import 'package:flutter/widgets.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:google_sign_in_web/web_only.dart' as gsi_web;

import 'auth_service.dart';

/// Google 로그인 (Google Identity Services).
/// 클라이언트 ID는 빌드 옵션 없이 백엔드(.env의 GOOGLE_CLIENT_ID)에서 받아온다.
class GoogleSignInService {
  GoogleSignInService._();

  static Future<bool>? _ready;

  /// 백엔드에 클라이언트 ID가 설정돼 있으면 GIS를 한 번만 초기화하고 true.
  /// 실패하면(백엔드 미기동, ID 미설정) 다음 호출 때 다시 시도한다.
  static Future<bool> ensureInitialized(AuthService authService) => _ready ??= _init(authService);

  static Future<bool> _init(AuthService authService) async {
    try {
      final clientId = await authService.fetchGoogleClientId();
      if (clientId.isNotEmpty) {
        await GoogleSignIn.instance.initialize(clientId: clientId);
        return true;
      }
    } catch (_) {}
    _ready = null;
    return false;
  }

  /// 로그인에 성공하면 GoogleSignInAuthenticationEventSignIn이 들어온다 (broadcast 스트림).
  static Stream<GoogleSignInAuthenticationEvent> get authenticationEvents =>
      GoogleSignIn.instance.authenticationEvents;

  /// 웹에서는 Google 정책상 GIS가 그리는 공식 버튼을 써야 한다.
  static Widget renderButton({double? width}) => gsi_web.renderButton(
        configuration: gsi_web.GSIButtonConfiguration(
          theme: gsi_web.GSIButtonTheme.outline,
          size: gsi_web.GSIButtonSize.large,
          text: gsi_web.GSIButtonText.continueWith,
          shape: gsi_web.GSIButtonShape.rectangular,
          minimumWidth: width,
          locale: 'ko',
        ),
      );

  /// 앱 로그아웃 시 Google 자동 선택도 해제한다.
  static Future<void> signOut() async {
    final ready = _ready;
    if (ready != null && await ready) {
      await GoogleSignIn.instance.signOut();
    }
  }
}
