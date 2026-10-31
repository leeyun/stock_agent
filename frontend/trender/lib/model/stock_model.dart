class WatchlistGroupModel {
  final int id;
  final String name;
  final bool isDefault;
  final int order;

  WatchlistGroupModel({
    required this.id,
    required this.name,
    required this.isDefault,
    required this.order,
  });

  factory WatchlistGroupModel.fromJson(Map<String, dynamic> json) {
    return WatchlistGroupModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      isDefault: json['is_default'] ?? false,
      order: json['order'] ?? 0,
    );
  }
}

class StockModel {
  final int id;
  final String code;
  final String companyName;
  final String price;
  final String changeRate;
  final String changePrice;
  final bool isPositive;
  final List<NewsModel> newsList;

  StockModel({
    required this.id,
    required this.code,
    required this.companyName,
    required this.price,
    required this.changeRate,
    required this.changePrice,
    required this.isPositive,
    required this.newsList,
  });

  factory StockModel.fromSearchJson(Map<String, dynamic> json) {
    return StockModel(
      id: json['id'] ?? 0,
      code: json['code'] ?? '',
      companyName: json['name'] ?? '',
      price: '0원',
      changeRate: '0.00%',
      changePrice: '0원',
      isPositive: true,
      newsList: [],
    );
  }

  StockModel copyWith({
    String? price,
    String? changeRate,
    String? changePrice,
    bool? isPositive,
    List<NewsModel>? newsList,
  }) {
    return StockModel(
      id: id,
      code: code,
      companyName: companyName,
      price: price ?? this.price,
      changeRate: changeRate ?? this.changeRate,
      changePrice: changePrice ?? this.changePrice,
      isPositive: isPositive ?? this.isPositive,
      newsList: newsList ?? this.newsList,
    );
  }
}

class NewsModel {
  final int id;
  final String date;
  final String time; // "15분 전" 또는 시간 표시
  final String title;
  final String tag; // "호재", "악재", "중립"
  final String summary;
  final String media; // 언론사 (예: 한국경제)
  final String originalUrl;
  final List<String> bulletSummaries; // ✨ 3줄 요약
  final String aiReason; // ✨ AI 호재/악재 사유

  NewsModel({
    required this.id,
    required this.date,
    required this.time,
    required this.title,
    required this.tag,
    required this.summary,
    required this.media,
    required this.originalUrl,
    required this.bulletSummaries,
    required this.aiReason,
  });

  // 상대적 시간 포맷팅 ("15분 전", "1시간 전" 등)
  static String _formatRelativeTime(DateTime dateTime) {
    final diff = DateTime.now().difference(dateTime);
    if (diff.inMinutes < 1) return '방금 전';
    if (diff.inMinutes < 60) return '${diff.inMinutes}분 전';
    if (diff.inHours < 24) return '${diff.inHours}시간 전';
    if (diff.inDays < 7) return '${diff.inDays}일 전';
    return "${dateTime.month}월 ${dateTime.day}일";
  }

  factory NewsModel.fromJson(Map<String, dynamic> json) {
    final publishedAt = DateTime.tryParse(json['published_at']?.toString() ?? '')?.toLocal() ?? DateTime.now();
    final dateStr = "${publishedAt.year}.${publishedAt.month.toString().padLeft(2, '0')}.${publishedAt.day.toString().padLeft(2, '0')}";
    final relativeTimeStr = _formatRelativeTime(publishedAt);

    // 💡 백엔드 NewsDetailSerializer의 bullet_summaries 파싱
    List<String> bullets = [];
    if (json['bullet_summaries'] is List) {
      bullets = (json['bullet_summaries'] as List).map((e) => e.toString()).toList();
    }
    if (bullets.isEmpty && json['summary'] != null && json['summary'].toString().isNotEmpty) {
      bullets = [json['summary'].toString()];
    }

    return NewsModel(
      id: json['id'] ?? 0,
      date: dateStr,
      time: relativeTimeStr,
      title: json['title'] ?? '',
      tag: json['sentiment_tag'] ?? '중립',
      summary: json['summary'] ?? '',
      media: json['press'] ?? '경제뉴스',
      originalUrl: json['origin_url'] ?? json['url'] ?? '',
      bulletSummaries: bullets,
      aiReason: json['ai_reason'] ?? 'AI 감성 분석 결과입니다.',
    );
  }
}