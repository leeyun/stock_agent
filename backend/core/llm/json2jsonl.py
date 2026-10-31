import json
import glob

# 1) 읽어올 여러 JSON 파일 패턴 및 저장할 최종 JSONL 파일 경로 설정
input_files = glob.glob('data/trained_data/*.json')  # 폴더 내 모든 json 파일 탐색
output_file = 'data/combined_dataset.jsonl'

instruction = "다음 뉴스 기사를 분석하여 핵심 요약, 감성(호재/악재/중립), 그리고 이유를 작성하세요."

# 2) 아웃풋 파일을 열어두고 여러 인풋 파일을 순회하며 쓰기
with open(output_file, 'w', encoding='utf-8') as outfile:
    for file_path in input_files:
        # 새로 생성할 output_file 자신을 다시 읽는 것을 방지
        if file_path == output_file:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
                
                # 파일 내용이 단일 객체({ ... })인 경우 리스트([ { ... } ]) 형태로 통일
                if isinstance(data, dict):
                    data = [data]
                    
                for item in data:
                    input_text = f"제목: {item.get('title', '')}\n본문: {item.get('content', '')}"
                    
                    analysis = item.get('llm_analysis', {})
                    summary_list = analysis.get('summary', [])
                    summary_formatted = "\n".join([f"- {s}" for s in summary_list])
                    
                    output_text = (
                        f"**요약**\n{summary_formatted}\n\n"
                        f"**감성**: {analysis.get('sentiment', '')}\n\n"
                        f"**이유**: {analysis.get('reason', '')}"
                    )
                    
                    formatted_item = {
                        "instruction": instruction,
                        "input": input_text,
                        "output": output_text
                    }
                    
                    # 하나의 아웃풋 파일에 계속 누적하여 쓰기
                    outfile.write(json.dumps(formatted_item, ensure_ascii=False) + '\n')
                    
        except Exception as e:
            print(f"파일 읽기 오류 ({file_path}): {e}")

print(f"총 {len(input_files)}개 파일 병합 및 변환 완료!")