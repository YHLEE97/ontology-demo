import os
import base64
import yaml
import pymupdf
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 환경 변수 로드
load_dotenv()

# 경로 설정(demo 용 하드코딩)
pdf_path = Path("data/raw/sgc_energy.pdf")
output_parquet_path = Path("data/processed/sgc_energy.parquet")

# 저장할 폴더가 없다면 생성
output_parquet_path.parent.mkdir(parents=True, exist_ok=True)

# VLM (GPT-4o) 초기화
llm = ChatOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name=os.environ.get("OPENAI_VLM_MODEL", "gpt-4o"),
    temperature=0,
)


def load_prompt_from_yaml(file_path: str):
    """YAML 파일에서 프롬프트 설정과 텍스트를 로드합니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


print("[System] PDF 파일 처리를 시작합니다. 대상 파일:", pdf_path.name)

# 결과를 담을 리스트
parsed_data = []

# 시스템 지시문 (프롬프트)
prompt_config = load_prompt_from_yaml("config/prompts/pdf_to_md_prompt.yml")
system_prompt = prompt_config["system_prompt"]

try:
    with pymupdf.open(pdf_path) as doc:
        total_pages = len(doc)
        print(f"[System] 총 {total_pages}페이지를 발견했습니다.")

        for page_num in range(total_pages):
            real_page_num = page_num + 1
            print(f"[System] {real_page_num}/{total_pages} 페이지 변환 중...")

            # 페이지를 이미지로 렌더링 (dpi=150)
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")

            # 이미지를 Base64 인코딩
            base64_image = base64.b64encode(img_bytes).decode("utf-8")

            # VLM에 전달할 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt},
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": "이 이미지의 내용을 마크다운으로 변환해 줘.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ]
                ),
            ]

            # API 호출
            response = llm.invoke(messages)

            # 결과 저장
            parsed_data.append(
                {
                    "page_number": real_page_num,
                    "source_file": pdf_path.name,
                    "markdown_text": response.content,
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    # 추출된 데이터를 Pandas DataFrame으로 변환
    df = pd.DataFrame(parsed_data)

    # Parquet 포맷으로 저장 (pyarrow 엔진 사용)
    df.to_parquet(output_parquet_path, engine="pyarrow", index=False)

    print("\n[System] 작업 완료!")
    print(f"[System] Parquet 파일이 정상적으로 저장되었습니다: {output_parquet_path}")

except Exception as e:
    print(f"[Error] 처리 중 오류가 발생했습니다: {e}")
