import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:trender/widgets/tag_widget.dart';
import '../../../model/stock_model.dart';
import '../../../view_model/favorite_stocks.dart';
import 'detail_screen.dart';
import 'group_edit_screen.dart';
import 'group_stock_edit_screen.dart' show StockSearchBottomSheet;
import 'news_detail_screen.dart';

class FavoriteStocksTab extends StatefulWidget {
  const FavoriteStocksTab({super.key});

  @override
  State<FavoriteStocksTab> createState() => _FavoriteStocksTabState();
}

class _FavoriteStocksTabState extends State<FavoriteStocksTab> {
  Timer? _newsPollTimer;

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
      Provider.of<FavoriteStocksViewModel>(context, listen: false).fetchFavoriteStocks()
    );
  }

  void _showAddGroupDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('새 그룹 추가', style: TextStyle(fontWeight: FontWeight.bold)),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: '그룹 이름 입력'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('취소')),
          ElevatedButton(
            onPressed: () {
              final text = controller.text.trim();
              if (text.isNotEmpty) {
                context.read<FavoriteStocksViewModel>().addGroup(text);
                Navigator.pop(ctx);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF5C5CFF)),
            child: const Text('추가', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // 현재 선택된 그룹 탭에 바로 종목을 추가한다 (그룹 추가는 톱니바퀴 편집 화면에서)
  Future<void> _showAddStockSheet(BuildContext context) async {
    final viewModel = context.read<FavoriteStocksViewModel>();
    final groupName = viewModel.selectedGroup;
    if (groupName.isEmpty) return;

    viewModel.searchStocks('');
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => StockSearchBottomSheet(groupName: groupName),
    );
    // 추가한 종목의 시세를 바로 보여준다
    if (context.mounted) {
      await context.read<FavoriteStocksViewModel>().fetchFavoriteStocks();
      _pollNewsForEmptyStocks();
    }
  }

  // 새로 추가한 종목의 뉴스는 백엔드가 백그라운드로 수집하므로(10~30초),
  // 뉴스가 빈 종목이 있으면 잠시 동안 주기적으로 다시 불러온다
  void _pollNewsForEmptyStocks() {
    _newsPollTimer?.cancel();
    var attempts = 0;
    _newsPollTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      if (!mounted) {
        timer.cancel();
        return;
      }
      final viewModel = context.read<FavoriteStocksViewModel>();
      final stocks = viewModel.getStocksByGroup(viewModel.selectedGroup);
      if (++attempts > 12 || stocks.every((s) => s.newsList.isNotEmpty)) {
        timer.cancel();
        return;
      }
      await viewModel.refreshCurrentGroupPrices();
    });
  }

  @override
  void dispose() {
    _newsPollTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Consumer<FavoriteStocksViewModel>(
      builder: (context, viewModel, child) {
        if (viewModel.isLoading && viewModel.groups.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }

        if (viewModel.groups.isEmpty) {
          return Scaffold(
            backgroundColor: Colors.transparent,
            body: const Center(child: Text('등록된 관심 그룹이 없습니다.')),
            floatingActionButton: FloatingActionButton.small(
              backgroundColor: const Color(0xFF5C5CFF),
              onPressed: () => _showAddGroupDialog(context),
              child: const Icon(Icons.add, color: Colors.white),
            ),
          );
        }

        return Scaffold(
          backgroundColor: Colors.transparent,
          floatingActionButton: FloatingActionButton.small(
            backgroundColor: const Color(0xFF5C5CFF),
            elevation: 3,
            tooltip: '종목 추가',
            onPressed: () => _showAddStockSheet(context),
            child: const Icon(Icons.add, color: Colors.white),
          ),
          body: DefaultTabController(
            key: ValueKey(viewModel.groups.length),
            length: viewModel.groups.length,
            child: Builder(
              builder: (context) {
                final TabController tabController = DefaultTabController.of(context);
                tabController.addListener(() {
                  if (!tabController.indexIsChanging) {
                    viewModel.selectGroup(viewModel.groups[tabController.index]);
                  }
                });

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(left: 16.0, right: 8.0, top: 12.0),
                      child: Row(
                        children: [
                          Expanded(
                            child: TabBar(
                              isScrollable: true,
                              tabAlignment: TabAlignment.start,
                              indicatorColor: isDark ? Colors.white : Colors.black,
                              labelColor: isDark ? Colors.white : Colors.black,
                              unselectedLabelColor: Colors.grey.shade400,
                              labelStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              unselectedLabelStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                              dividerColor: Colors.transparent,
                              tabs: viewModel.groups.map((group) => Tab(text: group)).toList(),
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.settings_outlined, color: isDark ? Colors.white70 : Colors.black54),
                            onPressed: () async {
                              // 💡 그룹 편집 창에서 종목을 추가/삭제하고 돌아왔을 때 즉시 시세 재조회!
                              await Navigator.push(
                                context,
                                MaterialPageRoute(builder: (_) => const GroupEditScreen()),
                              );
                              if (context.mounted) {
                                context.read<FavoriteStocksViewModel>().fetchFavoriteStocks();
                              }
                            },
                          ),
                        ],
                      ),
                    ),

                    Expanded(
                      child: TabBarView(
                        children: viewModel.groups.map((group) {
                          final stocks = viewModel.getStocksByGroup(group);
                          if (stocks.isEmpty) {
                            return const Center(child: Text('등록된 관심 종목이 없습니다.'));
                          }

                          // 💡 당겨서 실시간 시세(/api/stock/prices/) 새로고침
                          return RefreshIndicator(
                            onRefresh: () async {
                              await viewModel.refreshCurrentGroupPrices();
                            },
                            child: ListView.builder(
                              physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
                              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
                              itemCount: stocks.length,
                              itemBuilder: (context, index) => _buildStockCard(context, stocks[index], isDark),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        );
      },
    );
  }

  Widget _buildStockCard(BuildContext context, StockModel stock, bool isDark) {
    final recentNews = stock.newsList.take(3).toList();
    final logoText = stock.companyName.length >= 2
        ? stock.companyName.substring(0, 2)
        : stock.companyName;

    return Container(
      margin: const EdgeInsets.only(bottom: 16.0),
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isDark ? 0.25 : 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    stock.companyName,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: isDark ? Colors.white : Colors.black,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // 💡 실제 시세(/api/stock/prices/) 및 전일대비 등락 출력
                  Text(
                    '${stock.price}  ${stock.changeRate}(${stock.changePrice})',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: stock.isPositive ? const Color(0xFFE54B4B) : const Color(0xFF3A7BD5),
                    ),
                  ),
                ],
              ),
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: isDark ? Colors.white24 : Colors.grey.shade300),
                ),
                child: Center(
                  child: Text(
                    logoText,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: isDark ? Colors.white70 : Colors.grey.shade600,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          if (recentNews.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12.0),
              child: Center(
                child: Text('관련 최신 뉴스가 없습니다.', style: TextStyle(color: Colors.grey.shade400, fontSize: 13)),
              ),
            ),
          ...recentNews.asMap().entries.map((entry) {
            final index = entry.key;
            final news = entry.value;

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                InkWell(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => NewsDetailScreen(news: news)),
                    );
                  },
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            TagWidget(tag: news.tag),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                news.title,
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold,
                                  color: isDark ? Colors.white : Colors.black,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 3),
                        Text(news.time, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                        const SizedBox(height: 4),
                        Text(
                          news.summary,
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark ? Colors.white70 : Colors.black87,
                            height: 1.3,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ),
                if (index < recentNews.length - 1)
                  Divider(height: 16, color: isDark ? Colors.white12 : Colors.grey.shade100),
              ],
            );
          }),
          const SizedBox(height: 12),

          InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => StockDetailScreen(stock: stock)),
              );
            },
            borderRadius: BorderRadius.circular(10),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF2B2D42) : const Color(0xFFF7F7F9),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Center(
                child: Text(
                  '더보기',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white70 : Colors.black87,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}