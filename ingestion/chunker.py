import pandas as pd
from datetime import datetime
from pathlib import Path

# 경로 설정
input_parquet_path = Path("data/processed/sgc_energy.parquet")
output_parquet_path = Path("data/processed/sgc_energy_chunk.parquet")

def run_chunker():
    print(f"[System] {input_parquet_path.name} 로딩 중...")
    
    if not input_parquet_path.exists():
        print(f"[Error] 파일을 찾을 수 없습니다: {input_parquet_path}")
        return

    # 1. Parquet 파일 로드
    df = pd.read_parquet(input_parquet_path)
    source_file_name = df.iloc[0]['source_file'] if not df.empty else "unknown"

    # 2. 모든 markdown_text를 하나로 합침
    full_text = "\n\n".join(df['markdown_text'].fillna("").tolist())
    
    print(f"[System] 전체 텍스트 길이: {len(full_text)}자")

    # 3. 500자씩 분할
    chunk_size = 500
    chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]
    
    # 4. 새로운 데이터 구성 (양식 동일하게 유지)
    chunked_data = []
    for i, chunk_content in enumerate(chunks):
        chunked_data.append({
            "page_number": i + 1,  # 여기서는 Chunk 순서로 사용
            "source_file": source_file_name,
            "markdown_text": chunk_content,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # 5. DataFrame 변환 및 저장
    chunk_df = pd.DataFrame(chunked_data)
    chunk_df.to_parquet(output_parquet_path, engine="pyarrow", index=False)

    print(f"[System] 작업 완료! {len(chunks)}개 청크로 분리되었습니다.")
    print(f"[System] 저장 경로: {output_parquet_path}")

if __name__ == "__main__":
    run_chunker()
