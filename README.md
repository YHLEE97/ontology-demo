# Ontology-Demo

GraphRAG 및 Ontology 기반 데이터를 활용하기 위한 데모 프로젝트입니다.

## 🚀 시작하기 (Getting Started)

프로젝트 환경 설정, 데이터베이스 실행 및 의존성 설치 과정은 다음과 같습니다.

### 1. 패키지 매니저 (`uv`) 및 의존성 설치

이 프로젝트는 패키지 관리 및 의존성 주입을 위해 **`uv`**를 사용합니다. `uv`가 설치되어 있지 않다면 먼저 설치한 후, 프로젝트 의존성을 동기화해야 합니다.

```bash
# 1. uv 설치 (아직 설치되지 않은 경우)
pip install uv

# 2. 의존성 동기화 및 가상 환경 준비
uv sync
```
*`uv sync` 명령어를 실행하면 `pyproject.toml`과 `uv.lock`을 기반으로 의존성이 설치된 가상 환경이 자동으로 생성됩니다.*

### 2. 환경 변수 (`.env`) 설정

연결 정보 및 API 키 등을 관리하기 위해 루트 경로에 `.env` 파일이 필요합니다. `.env.example` 파일을 복사하여 생성하고, 개인 자격 증명을 작성해주세요.

```bash
# Windows(PowerShell)의 경우
Copy-Item .env.example .env

# macOS/Linux의 경우
cp .env.example .env
```

**`.env` 수정 사항 예시:**
- `OPENAI_API_KEY`: 발급받은 OpenAI API Key 입력
- Neo4j 접속 정보도 `docker-compose.yml` 내용과 동일하게 맞춰 줍니다. (예: `NEO4J_PASSWORD=12345678`)

### 3. Docker Compose (Neo4j DB 실행)

그래프 데이터베이스인 **Neo4j**를 로컬 환경에서 실행하기 위해 Docker를 구동합니다.

```bash
# 백그라운드에서 Neo4j 컨테이너 실행
docker-compose up -d
```

- **Neo4j Browser:** [http://localhost:7474](http://localhost:7474) (웹 UI)
- **Bolt URI:** `bolt://localhost:7687`
- **기본 접속 계정:** `neo4j` / `12345678` (Docker 설정 기준)

종료하려면 아래 명령어를 사용합니다.
```bash
docker-compose down
```

---

## 📁 프로젝트 구조 (Project Structure)

프로젝트 디렉토리는 다음과 같이 구성되어 있습니다.

```text
Ontology-Demo/
├── config/                 # 프로젝트 환경설정 및 상수 관리
├── connections/            # 외부 API, DB (Neo4j, LLM 등) 연결 모듈
├── data/                   # 데이터 저장소 (원본, 파싱된 데이터 등)
├── ingestion/              # 데이터 수집, 청킹, 임베딩 파이프라인
├── mcp/                    # MCP (Model Context Protocol) 연동 및 툴
├── neo4j_data/             # Neo4j 도커 컨테이너 데이터 볼륨 (Local DB)
├── notebooks/              # 기능 검증 및 실험을 위한 주피터 노트북 (Jupyter)
├── orchestration/          # 워크플로우 오케스트레이션 (Agent, 라우팅 등)
├── tests/                  # 모듈별 단위 테스트 코드 (Pytest)
├── util/                   # 공통으로 사용하는 유틸리티 함수/클래스 모듈
├── docker-compose.yml      # DB 구동을 위한 도커 컴포즈 파일
├── main.py                 # 프로젝트 메인 실행 파일
├── pyproject.toml          # 프로젝트 의존성 및 메타정보 설정
├── uv.lock                 # 패키지 의존성 잠금(lock) 파일
└── README.md               # 프로젝트 개요 및 설정 안내
```
---

### 1. 사전 준비(notebooks)
1. LLM 연동(O)
2. Embedding Model 연동(O)
3. API Connection Test(O)
4. Neo4j 연동(O)
5. DB Connection Test(O)
6. Neo4j Index 적용(O)

### 2. Data Ingestion
1. PDF to MD 적용(O)
2. MD Chunk(500자) 적용(O)
3. Semantic Chunk 적용(O)
4. NER 수행
5. Neo4j 적재

### 3. LLM Orchestration
1. Native 적용
2. React Prompt 적용
3. MCP Tools List 적용

### 4. MCP 적용
1. Start Node Search MCP
4. Neo4j Search MCP
2. Local Search MCP
3. Global Search MCP

### Raw Data Source
link : https://markets.hankyung.com/consensus
