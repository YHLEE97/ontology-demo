import os
import copy
import re
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from config.prompts.extract_graph import (
    GRAPH_EXTRACTION_PROMPT,
    CONTINUE_PROMPT,
    LOOP_PROMPT,
    MAX_GREANING_COUNT,
)

# 환경 변수 로드
load_dotenv()

# 경로 설정
input_parquet_path = "data/processed/sgc_energy_semantic_chunk.parquet"
output_parquet_path = "data/processed/sgc_energy_ner.parquet"

# 폴더 없으면 생성
os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)

# LLM 초기화 (GPT-4o)
llm = ChatOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name=os.environ.get("OPENAI_MODEL", "gpt-4o"),
    temperature=0,
)

try:
    df = pd.read_parquet(input_parquet_path)
except Exception as e:
    print(f"[Error] 파케이 파일 로드 실패: {e}")
    exit(1)

# 엔티티 타입 샘플 정의
ENTITY_TYPES = "ORGANIZATION, PERSON, GEO, EVENT, DOCUMENT, CONCEPT, DATE"

extracted_records = []
global_id = 1

print(f"[System] NER 추출을 시작합니다. (총 청크 수: {len(df)})")

def parse_llm_response(response_text: str, original_file_name: str, chunk_name: str, start_id: int):
    records = []
    current_id = start_id
    
    # Extract tuples inside parenthesis 
    # Tuple format: ("entity"<|>...) or ("relationship"<|>...)
    # The first item inside could be "entity" or "relationship" with or without quotes.
    pattern = re.compile(r'\(\s*"?([^"<]+)"?\s*<\|>(.*?)\)')
    matches = pattern.findall(response_text)
    
    for match in matches:
        item_type = match[0].strip().lower()
        rest = match[1]
        parts = [p.strip() for p in rest.split("<|>")]
        
        if item_type == "entity" and len(parts) >= 3:
            entity_name = parts[0]
            entity_type = parts[1]
            entity_desc = parts[2]
            
            records.append({
                "id": current_id,
                "original_file_name": original_file_name,
                "chunk_name": chunk_name,
                "start_entity": entity_name,
                "relation": entity_type,
                "end_entity": "",
                "score": "",
                "description": entity_desc
            })
            current_id += 1
            
        elif item_type == "relationship" and len(parts) >= 4:
            source_entity = parts[0]
            target_entity = parts[1]
            rel_desc = parts[2]
            rel_score = parts[3] if len(parts) > 3 else ""
            
            records.append({
                "id": current_id,
                "original_file_name": original_file_name,
                "chunk_name": chunk_name,
                "start_entity": source_entity,
                "relation": "RELATED_TO",
                "end_entity": target_entity,
                "score": rel_score,
                "description": rel_desc
            })
            current_id += 1
            
    return records, current_id

for idx, row in df.iterrows():
    chunk_text = row.get("text", "")
    orig_file_name = row.get("original_file_name", "sgc_energy")
    chunk_name = os.path.basename(input_parquet_path).split('.')[0]
    
    if not chunk_text.strip():
        continue
        
    print(f"\n[System] [{idx+1}/{len(df)}] 청크 처리 중...")
    
    # 1. 초기 프롬프트 준비
    formatted_prompt = GRAPH_EXTRACTION_PROMPT.format(
        entity_types=ENTITY_TYPES,
        input_text=chunk_text
    )
    
    messages = [HumanMessage(content=formatted_prompt)]
    
    try:
        response = llm.invoke(messages)
        response_text = response.content
        
        records, global_id = parse_llm_response(response_text, orig_file_name, chunk_name, global_id)
        extracted_records.extend(records)
        print(f"  -> 초기 추출: {len(records)}개 항목. (ID: {global_id})")
        
        messages.append(AIMessage(content=response_text))
        
        # Gleaning 루프
        gleaning_count = 0
        while gleaning_count < MAX_GREANING_COUNT:
            # 2. 루프 질문 (더 남았는가?)
            eval_messages = copy.deepcopy(messages)
            eval_messages.append(HumanMessage(content=LOOP_PROMPT))
            
            eval_response = llm.invoke(eval_messages)
            eval_result = eval_response.content.strip().upper()
            
            if eval_result.startswith("N"):
                print(f"  -> 더 이상 추출할 요소 없음. (Gleaning: {gleaning_count})")
                break
            elif eval_result.startswith("Y"):
                # 3. 추가 추출
                messages.append(HumanMessage(content=CONTINUE_PROMPT))
                continue_response = llm.invoke(messages)
                response_text = continue_response.content
                
                new_records, global_id = parse_llm_response(response_text, orig_file_name, chunk_name, global_id)
                extracted_records.extend(new_records)
                print(f"  -> 추가로 {len(new_records)}개 항목 추출됨. (Gleaning: {gleaning_count+1})")
                
                messages.append(AIMessage(content=response_text))
                gleaning_count += 1
            else:
                print(f"  -> Y/N 이외의 응답 수신으로 Gleaning 조기 종료: {eval_result[:20]}")
                break
                
    except Exception as e:
        print(f"  -> LLM 처리 중 오류 발생: {e}")

if extracted_records:
    result_df = pd.DataFrame(extracted_records)
    result_df.to_parquet(output_parquet_path, engine="pyarrow", index=False)
    print("\n[Success] NER 추출 및 저장 완료!")
    print(f"- 총 추출 건수: {len(result_df)}")
    print(f"- 저장 경로: {output_parquet_path}")
else:
    print("\n[System] 추출된 데이터가 없습니다.")
