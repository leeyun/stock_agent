import 'package:flutter/material.dart';

/// 넓은 브라우저 창에서 콘텐츠가 화면 끝까지 늘어나지 않도록 가운데 정렬 + 최대 폭 제한.
/// 화면이 maxWidth보다 좁으면(모바일 브라우저) 아무 영향 없음.
class ResponsiveCenter extends StatelessWidget {
  final Widget child;
  final double maxWidth;

  const ResponsiveCenter({super.key, required this.child, this.maxWidth = 720});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: SizedBox(width: double.infinity, child: child),
      ),
    );
  }
}
