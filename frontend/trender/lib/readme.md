lib/
├── main.dart
├── core/
│   └── network/
│       └── api_client.dart            // Ngrok 경고 우회, JWT 토큰 자동 갱신 및 HTTP 공통 클라이언트
├── model/
│   ├── stock_model.dart               // 종목, 시세, 뉴스 및 관심그룹 모델 (기존 UI 100% 호환)
│   └── user_model.dart                // 유저 정보 모델
├── service/
│   ├── auth_service.dart              // 로그인, 회원가입, 닉네임 수정 등 인증 API
│   └── stock_service.dart             // 종목검색, 시세, 관심그룹/종목 CRUD, 뉴스 피드 API
├── view_model/
│   ├── auth_view_model.dart           // 인증 상태 관리
│   ├── main_view_model.dart           // 탭 및 화면 전환 관리
│   └── favorite_stocks.dart           // 관심종목, 시세, 뉴스 연동 핵심 뷰모델
├── view/
│   ├── splash_screen.dart             // 자동 로그인 판정 스플래시
│   ├── login_screen.dart              // 로그인 화면
│   ├── signup_screen.dart             // 회원가입 화면
│   ├── main_screen.dart               // 메인 탭바 화면
│   ├── mypage.dart                    // 프로필 및 로그아웃 화면
│   └── tabs/
│       ├── favorite_tabs/
│       │   ├── favorite_stocks.dart          // 관심종목 메인 탭 (시세/뉴스 카드)
│       │   ├── group_edit_screen.dart        // 관심그룹 편집/추가/삭제
│       │   ├── group_stock_edit_screen.dart  // 그룹 내 종목 추가/삭제/검색
│       │   ├── detail_screen.dart            // 종목 상세 화면
│       │   └── news_detail_screen.dart       // 뉴스 3줄 요약 & 호재/악재 상세 화면
│       ├── news_tab.dart              // 뉴스 모아보기 탭
│       ├── search_tab.dart            // 실시간 종목 탐색 탭
│       └── chatbot_tab.dart           // 챗봇 탭
└── widgets/
    └── tag_widget.dart                // 호재/악재/중립 뱃지 위젯