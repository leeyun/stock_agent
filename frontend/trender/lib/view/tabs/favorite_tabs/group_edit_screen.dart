import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../model/stock_model.dart';
import '../../../view_model/favorite_stocks.dart';
import 'group_stock_edit_screen.dart';

class GroupEditScreen extends StatelessWidget {
  const GroupEditScreen({super.key});

  // 💡 그룹 삭제 확인 다이얼로그
  void _showDeleteConfirmDialog(BuildContext context, WatchlistGroupModel group) {
    if (group.isDefault) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('기본 그룹은 삭제할 수 없습니다.')),
      );
      return;
    }

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('그룹 삭제', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        content: Text("'${group.name}' 그룹을 정말 삭제하시겠습니까?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('취소', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              final result = await context.read<FavoriteStocksViewModel>().removeGroup(group);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(result.message)),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFE54B4B)),
            child: const Text('삭제', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
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

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<FavoriteStocksViewModel>();
    final groupModels = viewModel.groupModels;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Trender'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(20),
          ),
          padding: const EdgeInsets.symmetric(vertical: 20.0, horizontal: 16.0),
          child: Column(
            children: [
              const Text(
                '그룹 편집',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: ReorderableListView.builder(
                  itemCount: groupModels.length,
                  onReorder: (oldIndex, newIndex) {
                    context.read<FavoriteStocksViewModel>().reorderGroups(oldIndex, newIndex);
                  },
                  itemBuilder: (context, index) {
                    final group = groupModels[index];
                    return ListTile(
                      key: ValueKey(group.id),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => GroupStockEditScreen(groupName: group.name),
                          ),
                        );
                      },
                      contentPadding: const EdgeInsets.symmetric(horizontal: 8.0),
                      title: Text(
                        group.name,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: Icon(
                              Icons.delete_outline,
                              // 기본 그룹은 연한 회색, 삭제 가능한 그룹은 일반 회색
                              color: group.isDefault ? Colors.grey.shade300 : Colors.grey,
                              size: 22,
                            ),
                            onPressed: () => _showDeleteConfirmDialog(context, group),
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
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF5C5CFF),
        onPressed: () => _showAddGroupDialog(context),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}