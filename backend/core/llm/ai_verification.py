"""Gemini 뉴스 분석기(news_analyzer)의 감성 분류 성능을 정답 데이터셋으로 평가한다.

실행 (backend/ 에서):
    python core/llm/ai_verification.py <dataset.jsonl> [--samples 30] [--seed 42]

데이터셋은 JSONL, 한 줄에 기사 1건. 두 형식을 지원한다.
- 권장: {"stock": "삼성전자", "title": "...", "content": "...", "label": "POSITIVE" | "호재" ...}
- 이전 파인튜닝 형식: {"input": "제목: ...\\n본문: ...", "output": "... **감성**: 호재 ..."}

주의: 정답 라벨을 Gemini가 만든 데이터(예전 teacher_model 결과)로 평가하면 자기 자신과 비교하는 셈이라
의미가 약하다. 사람이 검수한 라벨로 평가해야 모델·프롬프트 비교에 쓸 수 있다.
"""
import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from core.llm.news_analyzer import analyze_article  # noqa: E402

LABELS = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
LABEL_KO = {"POSITIVE": "호재", "NEGATIVE": "악재", "NEUTRAL": "중립"}
KO_TO_CODE = {v: k for k, v in LABEL_KO.items()}


def load_samples(path):
    samples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if "label" in item:
                label = KO_TO_CODE.get(item["label"], item["label"])
                samples.append({"stock": item.get("stock", ""), "title": item.get("title", ""),
                                "content": item["content"], "label": label})
                continue

            # 이전 파인튜닝 형식
            match = re.search(r'\*\*감성\*\*\s*:\s*(호재|악재|중립)', item.get("output", ""))
            if not match:
                continue
            text = item.get("input", "")
            title_match = re.match(r'제목:\s*(.*)', text)
            samples.append({"stock": "", "title": title_match.group(1) if title_match else "",
                            "content": text, "label": KO_TO_CODE[match.group(1)]})
    return [s for s in samples if s["label"] in LABELS]


def run_benchmark(dataset_path, num_samples, seed):
    data = load_samples(dataset_path)
    if not data:
        print("평가할 샘플이 없습니다. 데이터셋 형식을 확인하세요.")
        return

    random.seed(seed)
    samples = random.sample(data, min(num_samples, len(data)))
    cm = {gt: {pred: 0 for pred in LABELS} for gt in LABELS}
    errors = 0
    total_latency = 0.0

    print(f"\nGemini 뉴스 분석기 평가 중... ({len(samples)}건)\n")
    print(f"{'ID':<4} | {'정답':<6} | {'예측':<6} | {'관련도':<6} | {'판정':<4} | 응답시간")
    print("-" * 56)

    for idx, s in enumerate(samples, 1):
        start = time.time()
        try:
            result = analyze_article(s["stock"] or "기사의 주요 종목", s["title"], s["content"])
            pred, relevance = result.sentiment, f"{result.relevance:.2f}"
        except Exception as exc:
            pred, relevance = None, "-"
            errors += 1
            print(f"  -> 분석 오류: {exc}")
        latency = time.time() - start
        total_latency += latency

        if pred:
            cm[s["label"]][pred] += 1
        mark = "O" if pred == s["label"] else "X"
        print(f"{idx:<4} | {LABEL_KO[s['label']]:<6} | {LABEL_KO.get(pred, '오류'):<6} | "
              f"{relevance:<6} | {mark:<4} | {latency:.2f}초")

    total = len(samples)
    correct = sum(cm[label][label] for label in LABELS)
    print("\n" + "=" * 56)
    print(f"정확도: {correct / total * 100:.2f}% ({correct}/{total}), 분석 오류 {errors}건")
    print(f"{'':<6}{'정밀도%':>10}{'재현율%':>10}{'F1%':>10}{'샘플':>6}")

    f1_sum = 0.0
    for label in LABELS:
        tp = cm[label][label]
        fp = sum(cm[o][label] for o in LABELS if o != label)
        fn = sum(cm[label][o] for o in LABELS if o != label)
        support = sum(cm[label].values())
        prec = tp / (tp + fp) * 100 if tp + fp else 0.0
        rec = tp / (tp + fn) * 100 if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        f1_sum += f1
        print(f"{LABEL_KO[label]:<6}{prec:>10.2f}{rec:>10.2f}{f1:>10.2f}{support:>6}")
    print(f"Macro F1: {f1_sum / len(LABELS):.2f}%")

    print("\n혼동 행렬 (행: 정답, 열: 예측)")
    print(f"{'':<8}" + "".join(f"{LABEL_KO[p]:>8}" for p in LABELS))
    for gt in LABELS:
        print(f"{LABEL_KO[gt]:<8}" + "".join(f"{cm[gt][p]:>8}" for p in LABELS))
    print(f"\n평균 응답 시간: {total_latency / total:.2f}초/건")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset", help="JSONL 데이터셋 경로")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_benchmark(args.dataset, args.samples, args.seed)
