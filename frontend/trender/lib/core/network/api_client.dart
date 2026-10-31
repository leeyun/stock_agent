import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiClient {
  static const String baseUrl = 'https://pearlie-overfervent-nonimputatively.ngrok-free.dev';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

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

  Future<void> saveTokens({required String access, required String refresh}) async {
    await _storage.write(key: 'jwt_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
  }

  Future<String?> getAccessToken() async => await _storage.read(key: 'jwt_token');
  Future<String?> getRefreshToken() async => await _storage.read(key: 'refresh_token');
  Future<void> clearTokens() async => await _storage.deleteAll();

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
        await _storage.write(key: 'jwt_token', value: data['access']);
        if (data['refresh'] != null) {
          await _storage.write(key: 'refresh_token', value: data['refresh']);
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