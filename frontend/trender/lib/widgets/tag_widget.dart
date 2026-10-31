import 'package:flutter/material.dart';

class TagWidget extends StatelessWidget {
  final String tag;

  const TagWidget({super.key, required this.tag});

  @override
  Widget build(BuildContext context) {
    Color tagColor;

    if (tag == '호재') {
      tagColor = const Color(0xFFE54B4B); // 빨간색
    } else if (tag == '악재') {
      tagColor = Colors.blue; // 파란색
    } else {
      tagColor = Colors.grey.shade600; // 중립 (회색)
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: tagColor,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        tag,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}