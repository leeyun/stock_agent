"""빌드된 Flutter Web(frontend/build/web)을 Django가 직접 서빙한다.

ngrok 터널 하나(포트 8000)로 웹 화면과 API를 같은 주소에서 제공하기 위한 것이다.
웹 빌드는 scripts\\manager.bat 의 "웹 빌드" 메뉴로 만든다 (API_BASE_URL을 비워 같은 출처의 API를 쓴다).
"""
from django.conf import settings
from django.http import HttpResponseNotFound
from django.views.static import serve

NOT_BUILT = "웹 빌드가 없습니다. scripts\\manager.bat 에서 '웹 빌드'를 실행하세요."


def frontend(request, path=""):
    build_dir = settings.FRONTEND_BUILD_DIR
    if not (build_dir / "index.html").is_file():
        return HttpResponseNotFound(NOT_BUILT, content_type="text/plain; charset=utf-8")

    target = (build_dir / path).resolve()
    if path and target.is_file() and target.is_relative_to(build_dir.resolve()):
        return serve(request, path, document_root=build_dir)
    # Flutter 라우트 경로나 없는 파일은 앱 진입점으로 보낸다
    response = serve(request, "index.html", document_root=build_dir)
    response["Cache-Control"] = "no-cache"
    return response
