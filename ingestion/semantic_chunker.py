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

print(f"[System] 청킹 프로세스를 시작합니다. (입력 행 수: {len(df)})")

for idx, row in df.iterrows():
    # 입력 데이터에서 기존 정보 추출 (없을 경우 기본값 설정)
    page_num = row.get("page_number", 0)
    src_file = row.get("source_file", "unknown")
    raw_md = row["markdown_text"]

    # --- Step 1: 1차 청킹 (Header 기반) ---
    header_splits = md_splitter.split_text(raw_md)

    for doc in header_splits:
        content = doc.page_content
        token_len = dict_token_count(content)

        # --- Step 2: 2차 청킹 여부 판단 ---
        if token_len > 1200:
            # 1200 토큰이 넘으면 2차 청킹 수행 (chunk_type: 2)
            sub_splits = recursive_splitter.split_text(content)
            for sub_text in sub_splits:
                processed_chunks.append(
                    {
                        "page_number": page_num,
                        "source_file": src_file,
                        "markdown_text": sub_text,
                        "processed_at": current_time,
                        "chunk_type": 2,  # 2차 청킹 결과물
                        "token_count": dict_token_count(sub_text),
                    }
                )
        else:
            # 적절한 길이면 1차 청킹으로 마감 (chunk_type: 1)
            processed_chunks.append(
                {
                    "page_number": page_num,
                    "source_file": src_file,
                    "markdown_text": content,
                    "processed_at": current_time,
                    "chunk_type": 1,  # 1차 청킹 결과물
                    "token_count": token_len,
                }
            )

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
