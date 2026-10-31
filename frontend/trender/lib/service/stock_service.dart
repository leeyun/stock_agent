import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';
import '../model/stock_model.dart';

class StockService {
  final ApiClient client;
  StockService({ApiClient? client}) : client = client ?? ApiClient();

  // 관심그룹 목록 조회
  Future<List<WatchlistGroupModel>> getGroups() async {
    final res = await client.get('/api/watchlist/groups/');
    if (res.statusCode == 200) {
      final List data = jsonDecode(utf8.decode(res.bodyBytes));
      return data.map((e) => WatchlistGroupModel.fromJson(e)).toList();
    }
    return [];
  }

  // 관심그룹 생성
  Future<WatchlistGroupModel?> addGroup(String name) async {
    final res = await client.post('/api/watchlist/groups/', body: {'name': name});
    if (res.statusCode == 201) {
      return WatchlistGroupModel.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
    }
    return null;
  }

  // 관심그룹 삭제
  Future<bool> removeGroup(int groupId) async {
    final res = await client.delete('/api/watchlist/groups/$groupId/');
    return res.statusCode == 204;
  }

  // 관심그룹 순서 변경
  Future<bool> reorderGroups(List<int> orderedIds) async {
    final res = await client.patch('/api/watchlist/groups/order/', body: {'order': orderedIds});
    return res.statusCode == 200;
  }

  // 그룹 내 종목 목록 조회
  Future<List<StockModel>> getGroupStocks(int groupId) async {
    final res = await client.get('/api/watchlist/groups/$groupId/items/?page=0&size=50');
    if (res.statusCode == 200) {
      final data = jsonDecode(utf8.decode(res.bodyBytes));
      final List results = data['results'] ?? [];
      return results.map<StockModel>((item) {
        final stockJson = item['stock'];
        return StockModel(
          id: stockJson['id'],
          code: stockJson['code'] ?? '',
          companyName: stockJson['name'] ?? '',
          price: '0원',
          changeRate: '0.00%',
          changePrice: '0원',
          isPositive: true,
          newsList: [],
        );
      }).toList();
    }
    return [];
  }

  // 실시간 시세 묶음 조회 API (/api/stock/prices/?ids=1,2,3)
  Future<Map<int, Map<String, dynamic>>> getPrices(List<int> stockIds) async {
    if (stockIds.isEmpty) return {};

    final idsParam = stockIds.join(',');
    final path = '/api/stock/prices/?ids=$idsParam';

    debugPrint('📡 [시세 API 요청] $path');
    final res = await client.get(path);
    debugPrint('📥 [시세 API 응답] HTTP ${res.statusCode} -> ${res.body}');

    if (res.statusCode == 200) {
      final dynamic decoded = jsonDecode(utf8.decode(res.bodyBytes));
      if (decoded is List) {
        final map = <int, Map<String, dynamic>>{};
        for (var item in decoded) {
          if (item is Map<String, dynamic>) {
            final sId = int.tryParse(item['stock_id']?.toString() ?? '');
            if (sId != null) {
              map[sId] = item;
            }
          }
        }
        return map;
      }
    }
    return {};
  }

  // 💡 [새로 추가된 뉴스 API 연동] 종목별 최신 뉴스 3개 조회
  Future<List<NewsModel>> getStockNews(int stockId, {int size = 3}) async {
    final path = '/api/news/?stock_id=$stockId&page=0&size=$size';
    debugPrint('📰 [종목별 뉴스 API 요청] $path');

    try {
      final res = await client.get(path);
      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        final List results = data['results'] ?? [];
        debugPrint('📰 [뉴스 로드 성공] 종목ID: $stockId -> 총 ${results.length}건 수신');
        return results.map((e) => NewsModel.fromJson(e)).toList();
      }
    } catch (e) {
      debugPrint('⚠️ [뉴스 조회 실패] $e');
    }
    return [];
  }

  // 종목 검색
  Future<List<StockModel>> searchStocks(String query) async {
    if (query.trim().isEmpty) return [];
    final res = await client.get('/api/stock/?query=${Uri.encodeComponent(query)}');
    if (res.statusCode == 200) {
      final List list = jsonDecode(utf8.decode(res.bodyBytes));
      return list.map((e) => StockModel.fromSearchJson(e)).toList();
    }
    return [];
  }

  // 그룹에 종목 추가
  Future<bool> addStockToGroup(int groupId, int stockId) async {
    final res = await client.post('/api/watchlist/groups/$groupId/items/', body: {'stock_id': stockId});
    return res.statusCode == 201;
  }

  // 그룹에서 종목 삭제
  Future<bool> removeStockFromGroup(int groupId, int stockId) async {
    final res = await client.delete('/api/watchlist/groups/$groupId/items/$stockId/');
    return res.statusCode == 204;
  }

  // 그룹 내 종목 순서 변경
  Future<bool> reorderStocksInGroup(int groupId, List<int> orderedStockIds) async {
    final res = await client.patch('/api/watchlist/groups/$groupId/items/order/', body: {'order': orderedStockIds});
    return res.statusCode == 200;
  }
}