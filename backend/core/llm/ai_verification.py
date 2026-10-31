import os
import sys
import requests
import re
import time
import json
import random
from pathlib import Path
from dotenv import load_dotenv

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


def run_benchmark(dataset_path: str, num_samples: int = 12):
    # 데이터셋 불러오기
    data = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    # 난수 시드 고정 (재현성 확보)
    SEED = 42
    random.seed(SEED)
    samples = random.sample(data, min(num_samples, len(data)))
    
    results = []
    correct_count = 0
    total_latency = 0

    # 혼동 행렬 초기화 [실제][예측]
    labels = ["호재", "악재", "중립"]
    cm = {gt: {pred: 0 for pred in labels} for gt in labels}

    print("\n⏳ Ollama AI 성능 평가 테스트 진행 중...\n")

    for idx, item in enumerate(samples, 1):
        input_text = item.get("input", "")
        ground_truth_text = item.get("output", "")
        
        # 정답(Ground Truth) 감성 추출
        gt_match = re.search(r'\*\*감성\*\*\s*:\s*(호재|악재|중립)', ground_truth_text)
        ground_truth = gt_match.group(1) if gt_match else ("호재" if "호재" in ground_truth_text else ("악재" if "악재" in ground_truth_text else "중립"))

        # 모델 추론
        pred = analyze_news_with_ollama(input_text)
        pred_sentiment = pred["sentiment"] if not pred["error"] else "중립"
        
        # 일치 여부 확인
        is_correct = (pred_sentiment == ground_truth) and not pred["error"]
        if is_correct:
            correct_count += 1
        total_latency += pred["latency"]

        # 혼동 행렬 카운트
        if ground_truth in labels and pred_sentiment in labels:
            cm[ground_truth][pred_sentiment] += 1

        # 예측 결과 출력용 텍스트
        pred_display = f"{pred['sentiment']}({pred['score']:+d}점)" if not pred["error"] else "오류"

        results.append({
            "id": idx,
            "gt": ground_truth,
            "pred": pred_display,
            "match": "✅ 성공" if is_correct else "❌ 실패",
            "latency": f"{pred['latency']}초"
        })

    total_samples = len(samples)
    accuracy = round((correct_count / total_samples) * 100, 2)
    avg_latency = round(total_latency / total_samples, 2)

    # 1. 샘플별 상세 평가 표 출력
    print("=" * 70)
    print("📊 [샘플별 AI 감성 분류 예측 상세 결과 (-50~+50 점수 반영)]")
    print("=" * 70)
    print(f"{'ID':<4} | {'정답(Ground Truth)':<18} | {'예측 및 점수(Prediction)':<22} | {'판정':<8} | {'응답시간':<8}")
    print("-" * 70)
    for r in results:
        print(f"{r['id']:<4} | {r['gt']:<18} | {r['pred']:<22} | {r['match']:<8} | {r['latency']:<8}")
    print("=" * 70)

    # 2. 클래스별 성능 지표 (Precision, Recall, F1) 계산
    stats = {}
    for label in labels:
        tp = cm[label][label]
        fp = sum(cm[other][label] for other in labels if other != label)
        fn = sum(cm[label][other] for other in labels if other != label)
        support = sum(cm[label][other] for other in labels)

        prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        stats[label] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": support
        }

    # Macro & Weighted Avg 계산
    macro_prec = sum(stats[l]["precision"] for l in labels) / len(labels)
    macro_rec = sum(stats[l]["recall"] for l in labels) / len(labels)
    macro_f1 = sum(stats[l]["f1"] for l in labels) / len(labels)

    weighted_prec = sum(stats[l]["precision"] * stats[l]["support"] for l in labels) / total_samples if total_samples > 0 else 0
    weighted_rec = sum(stats[l]["recall"] * stats[l]["support"] for l in labels) / total_samples if total_samples > 0 else 0
    weighted_f1 = sum(stats[l]["f1"] * stats[l]["support"] for l in labels) / total_samples if total_samples > 0 else 0

    # 3. 성능 평가표 출력
    print("\n" + "=" * 65)
    print(f"📊 [AI 감성 분석 모델 성능 평가표] (전체 정확도: {accuracy:.2f}%)")
    print("=" * 65)
    print(f"{'':<10}{'정밀도 (Precision %)':>20}{'재현율 (Recall %)':>18}{'F1 점수 (F1-Score %)':>20}{'샘플 수':>8}")
    print("-" * 65)
    for label in labels:
        s = stats[label]
        print(f"{label:<10}{s['precision']:>20.2f}{s['recall']:>18.2f}{s['f1']:>20.2f}{s['support']:>8}")
    print(f"{'전체 정확도 (Accuracy)':<12}{accuracy:>20.2f}{accuracy:>18.2f}{accuracy:>20.2f}{total_samples:>8}")
    print(f"{'단순 평균 (Macro Avg)':<12}{macro_prec:>20.2f}{macro_rec:>18.2f}{macro_f1:>20.2f}{total_samples:>8}")
    print(f"{'가중 평균 (Weighted Avg)':<12}{weighted_prec:>20.2f}{weighted_rec:>18.2f}{weighted_f1:>20.2f}{total_samples:>8}")
    print("=" * 65)

    # 4. 혼동 행렬 (Confusion Matrix) 출력
    print("\n" + "=" * 65)
    print("🧩 [혼동 행렬 (Confusion Matrix)]")
    print("=" * 65)
    print(f"{'':<14}{'예측: 호재':<12}{'예측: 악재':<12}{'예측: 중립':<12}")
    print("-" * 65)
    for gt_label in labels:
        c_hojae = cm[gt_label]["호재"]
        c_akjae = cm[gt_label]["악재"]
        c_jounglip = cm[gt_label]["중립"]
        print(f"실제: {gt_label:<8}{c_hojae:^12}{c_akjae:^12}{c_jounglip:^12}")
    print("=" * 65)
    print(f"• 평균 추론 속도 : {avg_latency} 초 / 개\n")


if __name__ == "__main__":
    # 데이터셋 파일 경로 지정
    DATASET_PATH = "backend/core/llm/data/combined_dataset.jsonl"
    
    # 10개 샘플 테스트 실행
    run_benchmark(DATASET_PATH, num_samples=10)