import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import time

# Windows 기본 콘솔(cp949)에서 이모지 print 시 UnicodeEncodeError 나는 것 방지
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 1. 경로 설정 및 .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

# 2. Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    import django
    django.setup()
    from django.conf import settings
except Exception:
    class FallbackSettings:
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    settings = FallbackSettings()


def analyze_news_with_ollama(news_content: str) -> dict:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    # Few-Shot 예시 및 비판적 분석 기법 적용
    prompt = f"""너는 매우 냉정하고 엄격한 주식 리스크 분석가다. 뉴스를 읽고 긍정적인 면에 속지 말고 **손실, 급락, 리스크, 불확실성(악재)**을 최우선으로 검증하여 점수를 매겨라.

[점수 부여 가이드라인]
- 악재 (음수 -1 ~ -50): 실적 악화, 급락, 적자, 소송, 유상증자, 비용 증가, 악재성 이슈
- 중립 (0점): 단순 동향, 인사이동, 시장 상황 정리, 개별 종목 주가 영향 없음
- 호재 (양수 +1 ~ +50): 실적 대폭 상승, 초대형 수주, 명확한 기업 가치 상승

[분석 예시 (Few-Shot)]
예시 1 (악재 뉴스)
기사: "A기업, 3분기 영업이익 적자 전환... 주가 15% 급락"
응답: {{"summary": "A기업의 3분기 영업이익이 적자로 전환되며 주가가 급락했습니다.", "reason": "영업이익 적자 전환으로 인한 실적 악화 악재가 크게 작용함.", "score": -35}}

예시 2 (중립 뉴스)
기사: "한국거래소, 다음 달 신규 상장 종목 설명회 개최 예정"
응답: {{"summary": "한국거래소가 신규 상장 종목 설명회를 개최할 예정입니다.", "reason": "개별 기업 가치에 직접적인 영향이 없는 단순 행사 안내임.", "score": 0}}

예시 3 (호재 뉴스)
기사: "B기업, 미국 기업과 1조원 규모 대형 공급 계약 체결"
응답: {{"summary": "B기업이 미국 기업과 1조원 규모의 공급 계약을 체결했습니다.", "reason": "대규모 수수로 인한 향후 실적 개선 기대감이 큼.", "score": 35}}

[분석할 뉴스 기사]
{news_content[:2000]}

[작성 규칙]
1. summary는 기사 내용의 사실 관계 요약, reason은 주가 관점에서의 판단 이유로 완전히 다르게 작성하라.
2. 기사에 손실/급락/악재성 내용이 포함되어 있다면 주저 없이 음수(-) 점수를 부여하라.

반드시 위 JSON 포맷으로만 응답하라:
{{"summary": "<기사 핵심 요약>", "reason": "<감성 판단 이유>", "score": <숫자>}}"""

    payload = {
        "model": "stock-llm",
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.05  # 결정론적 판단을 위해 더욱 하향
        }
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        latency = round(time.time() - start_time, 2)
        raw_text = response.json().get('response', '')

        # JSON direct parsing
        res_json = json.loads(raw_text)
        score = int(res_json.get("score", 0))
        reason = res_json.get("reason", "이유 미작성")
        summary = res_json.get("summary", "요약 미작성")

        # 점수 기준 감성 분류 매핑
        if score > 0:
            sentiment = "호재"
        elif score < 0:
            sentiment = "악재"
        else:
            sentiment = "중립"

        return {
            "score": score,
            "sentiment": sentiment,
            "reason": reason,
            "summary": summary,
            "latency": latency,
            "error": False
        }

    except Exception as e:
        latency = round(time.time() - start_time, 2)
        print(f"[Ollama Error] API 호출 실패: {e}")
        return {
            "score": 0,
            "sentiment": "중립",
            "reason": f"API 처리 중 오류 발생: {e}",
            "summary": "요약 생성 실패",
            "latency": latency,
            "error": True
        }


if __name__ == "__main__":
    test_news ="제목: 삼성전자 \"차세대 ASML 노광장비로 D램 만든다\"\n본문: ASML과 차세대 표준 구축 나서 \n공정 제약 해소 및 생산성 극대화 \n2028년 D램에 업계 최초로 적용\n한국경제신문의 투자 전문 유료 플랫폼 \n'한경 프리미엄9'\n(www.hankyung.com/premium9)에 실린 기사입니다. \n'한경 프리미엄9'\n을 구독하시면 더 많은 주식 투자 기사를 찾아볼 수 있습니다.\nASML의 EUV 노광장비. ASML 제공\n삼성전자가 세계 최대 반도체 노광장비 기업 ASML과 반도체 노광 공정의 판도를 바꿀 차세대 표준 구축에 나선다. 수십 년간 반도체 미세 공정의 표준으로 자리 잡은 6인치 포토마스크를 12인치로 전환하는 프로젝트다. 삼성전자는 2028년 업계 최초로 차세대 장비인 하이-NA EUV(극자외선) 장비를 첨단 D램 양산에 적용한다는 방침이다.\n삼성전자는 8일 ASML의 12인치 포토마스크 공동 개발을 위한 협의체에 합류해 차세대 노광 표준 및 기술 개발에 협력하기로 했다고 밝혔다. 이 협의체에는 삼성전자를 비롯해 TSMC, 인텔 등 첨단 반도체 생산을 주도하는 기업이 모두 참여한다. SK하이닉스도 참여를 긍정적으로 검토하고 있다.\n포토마스크는 웨이퍼에 미세 회로 패턴을 새기기 위한 정밀 ‘틀’이다. 반도체 성능과 수율을 결정짓는 핵심 도구라는 평가를 받고 있다. 그동안 반도체 노광 공정에는 6인치 마스크가 표준으로 쓰여왔다. 그러나 대당 4억달러(약 5300억원)에 달하는 차세대 노광 장비 하이-NA EUV 도입이 본격화하면서 기존 마스크의 물리적 한계가 발생했다. 하이-NA EUV는 빛의 개구수(NA·렌즈가 빛을 얼마나 많이 모을 수 있는지 나타내는 수치)를 기존 0.33에서 0.55로 높여 회로 선폭을 8㎚(나노미터·1㎚는 10억분의 1m) 수준까지 한층 정밀하게 새길 수 있지만, 기존 6인치 마스크를 사용한다면 한 번에 새길 수 있는 노광 면적이 절반으로 줄어든다. 이 때문에 회로를 나누어 새긴 뒤 다시 연결하는 ‘다이 스티칭’ 공정이 필수적이었고, 이는 생산 기간 연장과 불량률, 원가 상승의 주요 원인으로 지목돼 왔다.\n12인치 대형 포토마스크로 전환할 경우 한 번에 더 넓은 면적의 회로를 새길 수 있어 스티칭 제약을 해소할 수 있다. 설계 단계에서 수백억 개의 트랜지스터를 정밀 배치하는 첨단 인공지능(AI) 및 데이터센터용 반도체의 팹 생산성을 대폭 높이고 제조 비용을 낮출 수 있는 것이다.\n글로벌 주요 기업 역시 로드맵에 맞춰 차세대 표준을 전환하고 있다. TSMC는 2031년까지 파일럿 라인을 구축하고 2033년부터 첨단 노드 대량 생산에 적용할 계획이다. 2030년부터는 첨단 노드 고부가 물량 생산에 하이-NA 기술을 도입한다.\n삼성전자는 차세대 노광 기술 선점에도 속도를 낸다. 삼성전자는 지난해 3월 국내 최초로 하이-NA EUV 장비를 반입한 데 이어 2028년 세계 최초로 D램 양산 제품에 적용한다. 실제 양산 제품을 통해 공정 조건, 수율, 생산성을 선제적으로 검증함으로써 차세대 D램 미세화 경쟁에서 확실한 우위를 점하겠다는 전략이다. SK하이닉스도 2028년 D램 제품에 하이-NA EUV를 적용할 계획이다."

    print("=" * 50)
    print("🚀 학습 모델 대응 Ollama API 테스트")
    print("=" * 50)

    result = analyze_news_with_ollama(test_news)

    print(f"• 감성 평가: {result['sentiment']} ({result['score']:+d}점)")
    print(f"• 판단 이유: {result['reason']}")
    print(f"• 요약 내용:\n{result['summary']}")
    print("=" * 50)