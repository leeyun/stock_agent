import 'package:flutter/material.dart';
import '../model/stock_model.dart';
import '../service/stock_service.dart';

class FavoriteStocksViewModel extends ChangeNotifier {
  final StockService _stockService = StockService();

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  List<WatchlistGroupModel> _groupModels = [];
  List<WatchlistGroupModel> get groupModels => List.unmodifiable(_groupModels);

  String _selectedGroup = '';
  String get selectedGroup => _selectedGroup;

  List<String> get groups => _groupModels.map((g) => g.name).toList();

  final Map<String, List<StockModel>> _stocksByGroup = {};

  List<StockModel> _allStocks = [];
  List<StockModel> get allStocks => _allStocks;

  List<StockModel> get stocks => getStocksByGroup(_selectedGroup);

  List<StockModel> getStocksByGroup(String groupName) {
    return _stocksByGroup[groupName] ?? [];
  }

  WatchlistGroupModel? findGroupByName(String name) {
    try {
      return _groupModels.firstWhere((g) => g.name == name);
    } catch (_) {
      return null;
    }
  }

  String _formatComma(num value) {
    final str = value.toStringAsFixed(0);
    return str.replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
  }

  void selectGroup(String groupName) {
    _selectedGroup = groupName;
    notifyListeners();
    _loadStocksForGroup(groupName);
  }

  Future<void> fetchFavoriteStocks() async {
    _isLoading = true;
    notifyListeners();

    try {
      _groupModels = await _stockService.getGroups();
      if (_groupModels.isNotEmpty) {
        if (_selectedGroup.isEmpty || !groups.contains(_selectedGroup)) {
          _selectedGroup = _groupModels.first.name;
        }
        for (var g in _groupModels) {
          await _loadStocksForGroup(g.name);
        }
      }
    } catch (e) {
      debugPrint('관심종목 불러오기 실패: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // 💡 [핵심] 종목 시세 조회 + 종목별 최신 뉴스 3개 병합
  Future<void> _loadStocksForGroup(String groupName) async {
    final group = findGroupByName(groupName);
    if (group == null) return;

    final rawStocks = await _stockService.getGroupStocks(group.id);
    if (rawStocks.isEmpty) {
      _stocksByGroup[groupName] = [];
      notifyListeners();
      return;
    }

    // 1. 시세 묶음 일괄 조회
    final stockIds = rawStocks.map((s) => s.id).toList();
    final quotesMap = await _stockService.getPrices(stockIds);

    // 2. 각 종목별 시세와 최신 뉴스 3개 바인딩
    final List<StockModel> completeStocks = [];
    for (var stock in rawStocks) {
      final quote = quotesMap[stock.id];
      String priceStr = '0원';
      String changeRateStr = '0.00%';
      String changePriceStr = '0원';
      bool isPositive = true;

      if (quote != null) {
        final double currPrice = double.tryParse(quote['current_price']?.toString().replaceAll(',', '') ?? '0') ?? 0;
        final double chgAmt = double.tryParse(quote['change_amount']?.toString().replaceAll(',', '') ?? '0') ?? 0;
        final double chgRate = double.tryParse(quote['change_rate']?.toString().replaceAll(',', '') ?? '0') ?? 0;

        priceStr = '${_formatComma(currPrice)}원';
        changeRateStr = '${chgRate >= 0 ? '+' : ''}${chgRate.toStringAsFixed(2)}%';
        changePriceStr = '${chgAmt >= 0 ? '+' : ''}${_formatComma(chgAmt)}원';
        isPositive = chgAmt >= 0;
      }

      // 💡 새로 작성된 백엔드 API에서 해당 종목 뉴스 3개 조회
      final newsList = await _stockService.getStockNews(stock.id, size: 3);

      completeStocks.add(stock.copyWith(
        price: priceStr,
        changeRate: changeRateStr,
        changePrice: changePriceStr,
        isPositive: isPositive,
        newsList: newsList, // 카드에 꽂아 넣음!
      ));
    }

    _stocksByGroup[groupName] = completeStocks;
    notifyListeners();
  }

  Future<void> refreshCurrentGroupPrices() async {
    if (_selectedGroup.isNotEmpty) {
      await _loadStocksForGroup(_selectedGroup);
    }
  }

  Future<void> addGroup(String groupName) async {
    if (groups.contains(groupName)) return;

    final newGroup = await _stockService.addGroup(groupName);
    if (newGroup != null) {
      _groupModels.add(newGroup);
      _stocksByGroup[groupName] = [];
      if (_selectedGroup.isEmpty) {
        _selectedGroup = groupName;
      }
      notifyListeners();
    }
  }

  Future<({bool success, String message})> removeGroup(WatchlistGroupModel group) async {
    if (group.isDefault) {
      return (success: false, message: '기본 그룹은 삭제할 수 없습니다.');
    }

    final success = await _stockService.removeGroup(group.id);
    if (success) {
      _groupModels.removeWhere((g) => g.id == group.id);
      _stocksByGroup.remove(group.name);

      if (_selectedGroup == group.name) {
        _selectedGroup = _groupModels.isNotEmpty ? _groupModels.first.name : '';
        if (_selectedGroup.isNotEmpty) {
          await _loadStocksForGroup(_selectedGroup);
        }
      }
      notifyListeners();
      return (success: true, message: "'${group.name}' 그룹이 삭제되었습니다.");
    }
    return (success: false, message: '그룹 삭제에 실패했습니다.');
  }

  Future<void> reorderGroups(int oldIndex, int newIndex) async {
    if (oldIndex < newIndex) newIndex -= 1;
    final item = _groupModels.removeAt(oldIndex);
    _groupModels.insert(newIndex, item);
    notifyListeners();

    await _stockService.reorderGroups(_groupModels.map((g) => g.id).toList());
  }

  Future<void> searchStocks(String query) async {
    if (query.trim().isEmpty) {
      _allStocks = [];
      notifyListeners();
      return;
    }
    _allStocks = await _stockService.searchStocks(query.trim());
    notifyListeners();
  }

  Future<bool> toggleStockInGroup(String groupName, StockModel stock) async {
    final group = findGroupByName(groupName);
    if (group == null) return false;

    final groupStocks = _stocksByGroup[groupName] ?? [];
    final exists = groupStocks.any((e) => e.id == stock.id || e.code == stock.code);

    if (exists) {
      final success = await _stockService.removeStockFromGroup(group.id, stock.id);
      if (success) {
        groupStocks.removeWhere((e) => e.id == stock.id || e.code == stock.code);
        notifyListeners();
        return false;
      }
    } else {
      final success = await _stockService.addStockToGroup(group.id, stock.id);
      if (success) {
        await _loadStocksForGroup(groupName);
        return true;
      }
    }
    return exists;
  }

  Future<void> removeStockFromGroup(String groupName, StockModel stock) async {
    final group = findGroupByName(groupName);
    if (group == null) return;

    final success = await _stockService.removeStockFromGroup(group.id, stock.id);
    if (success) {
      _stocksByGroup[groupName]?.removeWhere((e) => e.id == stock.id);
      notifyListeners();
    }
  }

  Future<void> reorderStockInGroup(String groupName, int oldIndex, int newIndex) async {
    if (oldIndex < newIndex) newIndex -= 1;
    final group = findGroupByName(groupName);
    final groupStocks = _stocksByGroup[groupName];
    if (group == null || groupStocks == null) return;

    final stock = groupStocks.removeAt(oldIndex);
    groupStocks.insert(newIndex, stock);
    notifyListeners();

    await _stockService.reorderStocksInGroup(
      group.id,
      groupStocks.map((e) => e.id).toList(),
    );
  }
}