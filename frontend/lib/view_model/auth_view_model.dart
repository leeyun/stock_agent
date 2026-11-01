import 'package:flutter/material.dart';
import '../model/user_model.dart';
import '../service/auth_service.dart';

class AuthViewModel extends ChangeNotifier {
  final AuthService _authService = AuthService();

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  bool _isLoggedIn = false;
  bool get isLoggedIn => _isLoggedIn;

  UserModel? _user;
  UserModel? get user => _user;

  String get nickname => _user?.username ?? '사용자';
  String get email => _user?.email ?? '';

  Future<bool> tryAutoLogin() async {
    _isLoading = true;
    notifyListeners();

    final user = await _authService.getMe();
    if (user != null) {
      _user = user;
      _isLoggedIn = true;
      _isLoading = false;
      notifyListeners();
      return true;
    }

    _isLoggedIn = false;
    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    final success = await _authService.login(email, password);
    if (success) {
      _user = await _authService.getMe();
      _isLoggedIn = true;
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  AuthService get authService => _authService;

  Future<({bool success, String? errorMessage})> loginWithGoogle(String idToken) async {
    _isLoading = true;
    notifyListeners();

    final result = await _authService.loginWithGoogle(idToken);
    if (result.success) {
      _user = await _authService.getMe();
      _isLoggedIn = true;
    }

    _isLoading = false;
    notifyListeners();
    return result;
  }

  // 💡 에러 메시지 튜플 반환
  Future<({bool success, String? errorMessage})> signUp(
    String username,
    String email,
    String password,
    String password2,
  ) async {
    _isLoading = true;
    notifyListeners();

    final result = await _authService.signUp(username, email, password, password2);
    if (result.success) {
      _user = await _authService.getMe();
      _isLoggedIn = true;
    }

    _isLoading = false;
    notifyListeners();
    return result;
  }

  Future<bool> updateNickname(String newNickname) async {
    if (newNickname.isEmpty || newNickname == nickname) return false;

    _isLoading = true;
    notifyListeners();

    final success = await _authService.updateUsername(newNickname);
    if (success) {
      _user = await _authService.getMe();
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    _isLoggedIn = false;
    notifyListeners();
  }
}
