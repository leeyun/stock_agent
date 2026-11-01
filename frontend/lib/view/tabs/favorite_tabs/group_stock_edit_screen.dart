import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../view_model/favorite_stocks.dart';
import '../../../widgets/responsive_center.dart';

class GroupStockEditScreen extends StatelessWidget {
  final String groupName;

  const GroupStockEditScreen({super.key, required this.groupName});

  void _showSearchBottomSheet(BuildContext context) {
    context.read<FavoriteStocksViewModel>().searchStocks('');
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StockSearchBottomSheet(groupName: groupName),
    );
  }

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<FavoriteStocksViewModel>();
    final stocks = viewModel.getStocksByGroup(groupName);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Trender'),
        centerTitle: true,
      ),
      body: ResponsiveCenter(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Container(
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(vertical: 20.0, horizontal: 16.0),
            child: Column(
              children: [
                Text(
                  groupName == '관심종목' ? '관심 주식' : groupName,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: stocks.isEmpty
                      ? const Center(child: Text('등록된 종목이 없습니다. 아래 + 버튼을 눌러 추가하세요.'))
                      : ReorderableListView.builder(
                          itemCount: stocks.length,
                          onReorder: (oldIndex, newIndex) {
                            context.read<FavoriteStocksViewModel>().reorderStockInGroup(groupName, oldIndex, newIndex);
                          },
                          itemBuilder: (context, index) {
                            final stock = stocks[index];
                            return ListTile(
                              key: ValueKey(stock.id),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 8.0),
                              title: Text(stock.companyName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline, color: Colors.grey, size: 22),
                                    onPressed: () {
                                      context.read<FavoriteStocksViewModel>().removeStockFromGroup(groupName, stock);
                                    },
                                  ),
                                  const Icon(Icons.drag_handle, color: Colors.grey, size: 22),
                                ],
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF5C5CFF),
        onPressed: () => _showSearchBottomSheet(context),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}

class StockSearchBottomSheet extends StatefulWidget {
  final String groupName;
  const StockSearchBottomSheet({super.key, required this.groupName});

  @override
  State<StockSearchBottomSheet> createState() => _StockSearchBottomSheetState();
}

class _StockSearchBottomSheetState extends State<StockSearchBottomSheet> {
  final TextEditingController _controller = TextEditingController();
  // 빠른 즉각 반응을 위한 로컬 Set
  final Set<int> _localFavoriteIds = {};

  @override
  void initState() {
    super.initState();
    final currentStocks = context.read<FavoriteStocksViewModel>().getStocksByGroup(widget.groupName);
    _localFavoriteIds.addAll(currentStocks.map((s) => s.id));
  }

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<FavoriteStocksViewModel>();
    final allStocks = viewModel.allStocks;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF2B2D42) : const Color(0xFFF1F3F5),
              borderRadius: BorderRadius.circular(24),
            ),
            child: TextField(
              controller: _controller,
              autofocus: true,
              style: TextStyle(color: isDark ? Colors.white : Colors.black),
              onChanged: (val) {
                context.read<FavoriteStocksViewModel>().searchStocks(val);
              },
              decoration: const InputDecoration(
                hintText: '종목 이름 (예: NAVER, 삼성전자)',
                hintStyle: TextStyle(color: Colors.grey),
                prefixIcon: Icon(Icons.search, color: Colors.grey),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
          const SizedBox(height: 16),

          Expanded(
            child: allStocks.isEmpty
                ? const Center(child: Text('종목을 검색해 주세요.', style: TextStyle(color: Colors.grey)))
                : ListView.separated(
                    itemCount: allStocks.length,
                    separatorBuilder: (_, __) => Divider(color: isDark ? Colors.white10 : const Color(0xFFEEEEEE)),
                    itemBuilder: (context, index) {
                      final stock = allStocks[index];
                      final isFavorite = _localFavoriteIds.contains(stock.id);

                      return ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 8.0),
                        title: Text(
                          stock.companyName,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: isDark ? Colors.white : Colors.black87,
                          ),
                        ),
                        subtitle: Text(stock.code, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                        trailing: IconButton(
                          icon: Icon(
                            Icons.favorite,
                            color: isFavorite ? const Color(0xFFE54B4B) : const Color(0xFFD9D9D9),
                            size: 26,
                          ),
                          onPressed: () async {
                            // 💡 1. 로컬 UI 즉각 토글 (딜레이 없이 하트 반응)
                            setState(() {
                              if (isFavorite) {
                                _localFavoriteIds.remove(stock.id);
                              } else {
                                _localFavoriteIds.add(stock.id);
                              }
                            });

                            // 💡 2. 뷰모델 및 백엔드 반영
                            final added = await context.read<FavoriteStocksViewModel>().toggleStockInGroup(widget.groupName, stock);
                            
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  duration: const Duration(milliseconds: 1000),
                                  content: Text(added 
                                      ? "'${stock.companyName}' 그룹에 추가되었습니다." 
                                      : "'${stock.companyName}' 그룹에서 제거되었습니다."),
                                ),
                              );
                            }
                          },
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}