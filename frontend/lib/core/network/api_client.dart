import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  // flutter run -d chrome --dart-define=API_BASE_URL=https://api.example.com 으로 주입
  // 빈 값(--dart-define=API_BASE_URL=)이면 웹 페이지와 같은 주소의 API를 쓴다 (Django가 웹을 서빙하는 ngrok 공개용)
  static const String _configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  static final String baseUrl = _configuredBaseUrl.isEmpty ? Uri.base.origin : _configuredBaseUrl;

  Map<String, String> _headers({String? token}) {
    final headers = <String, String>{
      'Content-Type': 'application/json; charset=utf-8',
      'ngrok-skip-browser-warning': '69420',
    };
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // 웹에서는 토큰을 브라우저 localStorage에 저장한다 (shared_preferences 웹 구현)
  static const _accessKey = 'jwt_token';
  static const _refreshKey = 'refresh_token';

  Future<void> saveTokens({required String access, required String refresh}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessKey, access);
    await prefs.setString(_refreshKey, refresh);
  }

  Future<String?> getAccessToken() async => (await SharedPreferences.getInstance()).getString(_accessKey);
  Future<String?> getRefreshToken() async => (await SharedPreferences.getInstance()).getString(_refreshKey);

  Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessKey);
    await prefs.remove(_refreshKey);
  }

  Future<bool> refreshToken() async {
    final refresh = await getRefreshToken();
    if (refresh == null) return false;

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/refresh/'),
        headers: _headers(),
        body: jsonEncode({'refresh': refresh}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_accessKey, data['access']);
        if (data['refresh'] != null) {
          await prefs.setString(_refreshKey, data['refresh']);
        }
        return true;
      }
    } catch (_) {}
    await clearTokens();
    return false;
  }

  Future<http.Response> get(String path, {bool auth = true}) async {
    String? token = auth ? await getAccessToken() : null;
    var res = await http.get(Uri.parse('$baseUrl$path'), headers: _headers(token: token));

    if (res.statusCode == 401 && auth) {
      if (await refreshToken()) {
        token = await getAccessToken();
        res = await http.get(Uri.parse('$baseUrl$path'), headers: _headers(token: token));
      }
    }
    return res;
  }

  Future<http.Response> post(String path, {dynamic body, bool auth = true}) async {
    String? token = auth ? await getAccessToken() : null;
    var res = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers(token: token),
      body: body != null ? jsonEncode(body) : null,
    );

    if (res.statusCode == 401 && auth) {
      if (await refreshToken()) {
        token = await getAccessToken();
        res = await http.post(
          Uri.parse('$baseUrl$path'),
          headers: _headers(token: token),
          body: body != null ? jsonEncode(body) : null,
        );
      }
    }
    return res;
  }

  Future<http.Response> patch(String path, {dynamic body, bool auth = true}) async {
    String? token = auth ? await getAccessToken() : null;
    var res = await http.patch(
      Uri.parse('$baseUrl$path'),
      headers: _headers(token: token),
      body: body != null ? jsonEncode(body) : null,
    );

    if (res.statusCode == 401 && auth) {
      if (await refreshToken()) {
        token = await getAccessToken();
        res = await http.patch(
          Uri.parse('$baseUrl$path'),
          headers: _headers(token: token),
          body: body != null ? jsonEncode(body) : null,
        );
      }
    }
    return res;
  }

  Future<http.Response> delete(String path, {bool auth = true}) async {
    String? token = auth ? await getAccessToken() : null;
    var res = await http.delete(Uri.parse('$baseUrl$path'), headers: _headers(token: token));

    if (res.statusCode == 401 && auth) {
      if (await refreshToken()) {
        token = await getAccessToken();
        res = await http.delete(Uri.parse('$baseUrl$path'), headers: _headers(token: token));
      }
    }
    return res;
  }
}