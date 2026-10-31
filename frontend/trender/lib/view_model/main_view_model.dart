import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class MainViewModel extends ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  int _currentPage = 1;
  final int _maxPage = 5;
  bool _isSettingsMode = false;

  ThemeMode _themeMode = ThemeMode.system;
  ThemeMode get themeMode => _themeMode;

  MainViewModel() {
    _loadThemeMode();
  }

  int get currentPage => _currentPage;
  bool get isSettingsMode => _isSettingsMode;

  Future<void> _loadThemeMode() async {
    final saved = await _storage.read(key: 'theme_mode');
    if (saved == 'dark') {
      _themeMode = ThemeMode.dark;
    } else if (saved == 'light') {
      _themeMode = ThemeMode.light;
    } else {
      _themeMode = ThemeMode.system;
    }
    notifyListeners();
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    notifyListeners();
    String value = 'system';
    if (mode == ThemeMode.dark) value = 'dark';
    if (mode == ThemeMode.light) value = 'light';
    await _storage.write(key: 'theme_mode', value: value);
  }

  void setPage(int page) {
    if (page >= 1 && page <= _maxPage) {
      _currentPage = page;
      notifyListeners();
    }
  }

  void nextPage() {
    if (_currentPage < _maxPage) {
      _currentPage++;
      notifyListeners();
    }
  }

  void prevPage() {
    if (_currentPage > 1) {
      _currentPage--;
      notifyListeners();
    }
  }

  void toggleSettings() {
    _isSettingsMode = !_isSettingsMode;
    notifyListeners();
  }

  void disableSettings() {
    if (_isSettingsMode) {
      _isSettingsMode = false;
      notifyListeners();
    }
  }
}