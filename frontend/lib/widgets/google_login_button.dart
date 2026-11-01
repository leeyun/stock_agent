import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:provider/provider.dart';

import '../service/google_sign_in_service.dart';
import '../view_model/auth_view_model.dart';

/// Google 공식 로그인 버튼. 로그인되면 백엔드 JWT까지 받은 뒤 [onSuccess]를 호출한다.
/// 백엔드에 GOOGLE_CLIENT_ID가 없으면 비활성 버튼을 보여준다.
class GoogleLoginButton extends StatefulWidget {
  const GoogleLoginButton({super.key, required this.onSuccess});

  final VoidCallback onSuccess;

  @override
  State<GoogleLoginButton> createState() => _GoogleLoginButtonState();
}

class _GoogleLoginButtonState extends State<GoogleLoginButton> {
  late final Future<bool> _ready;
  StreamSubscription<GoogleSignInAuthenticationEvent>? _subscription;

  @override
  void initState() {
    super.initState();
    final authViewModel = context.read<AuthViewModel>();
    _ready = GoogleSignInService.ensureInitialized(authViewModel.authService).then((ready) {
      if (ready && mounted) {
        _subscription = GoogleSignInService.authenticationEvents.listen(_onEvent, onError: _onError);
      }
      return ready;
    });
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  Future<void> _onEvent(GoogleSignInAuthenticationEvent event) async {
    if (event is! GoogleSignInAuthenticationEventSignIn) return;
    final idToken = event.user.authentication.idToken;
    if (idToken == null) {
      _showError('Google에서 ID 토큰을 받지 못했습니다.');
      return;
    }

    final result = await context.read<AuthViewModel>().loginWithGoogle(idToken);
    if (!mounted) return;
    if (result.success) {
      widget.onSuccess();
    } else {
      _showError(result.errorMessage ?? 'Google 로그인에 실패했습니다.');
    }
  }

  void _onError(Object error) {
    // 사용자가 팝업을 닫은 경우 등은 조용히 무시한다.
    if (error is GoogleSignInException && error.code == GoogleSignInExceptionCode.canceled) return;
    _showError('Google 로그인에 실패했습니다.');
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: FutureBuilder<bool>(
        future: _ready,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: SizedBox.square(dimension: 24, child: CircularProgressIndicator(strokeWidth: 2)));
          }
          if (snapshot.data != true) {
            return Tooltip(
              message: '백엔드 .env에 GOOGLE_CLIENT_ID가 설정되지 않았습니다.',
              child: OutlinedButton(
                onPressed: null,
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: const Text('Google 로그인 사용 불가'),
              ),
            );
          }
          // GIS 버튼은 최대 400px
          return LayoutBuilder(
            builder: (context, constraints) => Center(
              child: GoogleSignInService.renderButton(width: constraints.maxWidth.clamp(200, 400).toDouble()),
            ),
          );
        },
      ),
    );
  }
}
