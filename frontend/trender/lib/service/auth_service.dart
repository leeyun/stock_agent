import 'dart:convert';
import '../core/network/api_client.dart';
import '../model/user_model.dart';

class AuthService {
  final ApiClient client;
  AuthService({ApiClient? client}) : client = client ?? ApiClient();

  Future<bool> login(String username, String password) async {
    try {
      final res = await client.post('/api/auth/login/', body: {
        'username': username,
        'password': password,
      }, auth: false);

      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        await client.saveTokens(
          access: data['access'],
          refresh: data['refresh'],
        );
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  // 💡 상세 실패 사유를 반환하도록 개선
  Future<({bool success, String? errorMessage})> signUp(
    String username,
    String email,
    String password,
    String password2,
  ) async {
    try {
      final res = await client.post('/api/auth/signup/', body: {
        'username': username,
        'email': email,
        'password': password,
        'password2': password2,
      }, auth: false);

      if (res.statusCode == 201) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        await client.saveTokens(
          access: data['access'],
          refresh: data['refresh'],
        );
        return (success: true, errorMessage: null);
      } else {
        // 백엔드 유효성 검사 에러 파싱
        final body = jsonDecode(utf8.decode(res.bodyBytes));
        final List<String> errors = [];

        if (body is Map<String, dynamic>) {
          body.forEach((key, value) {
            String fieldName = key;
            if (key == 'username') fieldName = '아이디';
            if (key == 'email') fieldName = '이메일';
            if (key == 'password') fieldName = '비밀번호';
            if (key == 'password2') fieldName = '비밀번호 확인';

            if (value is List) {
              for (var err in value) {
                errors.add('• [$fieldName] $err');
              }
            } else if (value is String) {
              errors.add('• [$fieldName] $value');
            }
          });
        }

        final message = errors.isNotEmpty 
            ? errors.join('\n') 
            : '입력값을 다시 확인해주세요.';
        return (success: false, errorMessage: message);
      }
    } catch (e) {
      return (success: false, errorMessage: '서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
    }
  }

  Future<UserModel?> getMe() async {
    try {
      final res = await client.get('/api/auth/me/');
      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        return UserModel.fromJson(data);
      }
    } catch (_) {}
    return null;
  }

  Future<bool> updateUsername(String newUsername) async {
    try {
      final res = await client.patch('/api/auth/me/', body: {
        'username': newUsername,
      });
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    final refresh = await client.getRefreshToken();
    if (refresh != null) {
      try {
        await client.post('/api/auth/logout/', body: {'refresh': refresh});
      } catch (_) {}
    }
    await client.clearTokens();
  }
}