import pandas as pd
import tiktoken
from datetime import datetime
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


# 1. 토큰 계산 함수 (GPT-4o 기준)
def dict_token_count(text: str, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


# 2. 데이터 로드 (Parquet)
input_path = "data/processed/sgc_energy.parquet"
df = pd.read_parquet(input_path)

# 3. 청킹 설정
# 1차: 마크다운 헤더 기준
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

# 2차: 1200 토큰 초과 시 재분할
recursive_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-4o", chunk_size=1200, chunk_overlap=100
)

processed_chunks = []
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
chunk_id_counter = 1

print(f"[System] 청킹 프로세스를 시작합니다. (입력 행 수: {len(df)})")

for idx, row in df.iterrows():
    # 입력 데이터에서 기존 정보 추출 (없을 경우 기본값 설정)
    page_num = row.get("page_number", 0)
    src_file = row.get("source_file", "unknown")
    raw_md = row["markdown_text"]

    print(idx)
    print(page_num)

    # --- Step 1: 1차 청킹 (Header 기반) ---
    header_splits = md_splitter.split_text(raw_md)

    for doc in header_splits:
        content = doc.page_content
        content_token_len = dict_token_count(content)

        # --- Step 2: 분할 방식에 따른 chunk_type 결정 ---
        if content_token_len < 1200:
            # 1200 토큰 미만이라 1차 청킹으로 마감
            processed_chunks.append(
                {
                    "original_file_name": "sgc_energy",
                    "chunk_id": chunk_id_counter,
                    "md_id": f"sgc_energy_page_{page_num}",
                    "text": content,
                    "processed_at": current_time,
                    "chunk_type": 1,
                    "token_count": content_token_len,
                }
            )
            chunk_id_counter += 1
        else:
            # 1200 토큰 이상이라 재분할(2차 청킹) 수행
            sub_splits = recursive_splitter.split_text(content)

            for i, sub_text in enumerate(sub_splits):
                sub_token_len = dict_token_count(sub_text)

                # chunk_type 결정 (맨 처음 1200은 1, 이후는 계속 2)
                if i == 0:
                    chunk_type = 1
                else:
                    # 중간에 꽉 차게 잘린 조각들
                    chunk_type = 2

                processed_chunks.append(
                    {
                        "original_file_name": "sgc_energy",
                        "chunk_id": chunk_id_counter,
                        "md_id": f"sgc_energy_page_{page_num}",
                        "text": sub_text,
                        "processed_at": current_time,
                        "chunk_type": chunk_type,
                        "token_count": sub_token_len,
                    }
                )
                chunk_id_counter += 1

# 4. 결과 저장 및 확인
output_df = pd.DataFrame(processed_chunks)
output_path = "data/processed/sgc_energy_semantic_chunk.parquet"
output_df.to_parquet(output_path, index=False)

print("-" * 30)
print(f"[Success] 청킹 완료!")
print(f"- 저장 경로: {output_path}")
print(f"- 전체 청크 수: {len(output_df)}")
print(f"- 1차 청킹 수: {len(output_df[output_df['chunk_type'] == 1])}")
print(f"- 2차 청킹 수: {len(output_df[output_df['chunk_type'] == 2])}")
print("-" * 30)

# 최종 결과물 스키마 확인 샘플
print(output_df.head(2))
