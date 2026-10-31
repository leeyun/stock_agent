from rest_framework.pagination import PageNumberPagination


class ZeroIndexedPageNumberPagination(PageNumberPagination):
    """page=0부터 시작, size로 페이지 크기 지정 (예: ?page=0&size=10)."""
    page_query_param = "page"
    page_size_query_param = "size"
    page_size = 20
    max_page_size = 100

    def get_page_number(self, request, paginator):
        raw = request.query_params.get(self.page_query_param, 0)
        try:
            zero_based = int(raw)
        except (TypeError, ValueError):
            zero_based = 0
        return max(zero_based, 0) + 1
