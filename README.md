# 🧠 자동 깃허브 커밋 분석기

GitHub 커밋을 자동으로 분석하고 연구노트를 생성하는 도구입니다. OpenAI GPT를 활용하여 커밋의 변경사항을 분석하고, 위험도와 영향도를 평가합니다.

## ✨ 주요 기능

- **자동 커밋 분석**: 지정된 리포지토리의 오늘 커밋을 자동으로 분석
- **AI 기반 분석**: OpenAI GPT를 활용한 코드 변경사항 분석
- **위험도 평가**: 각 파일과 커밋의 위험도를 자동 평가
- **연구노트 생성**: 마크다운과 JSON 형태로 분석 결과 저장
- **한국 시간 기준**: KST 기준으로 오늘 날짜의 커밋만 분석
- **스마트 필터링**: README 파일 자동 제외로 핵심 변경사항에 집중
- **대용량 커밋 처리**: 파일이 많은 커밋을 청크 단위로 분할 분석
- **커밋 링크**: GitHub 커밋 링크 자동 생성

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`env.template` 파일을 `.env`로 복사하고 필요한 값들을 설정하세요:

```bash
cp env.template .env
```

`.env` 파일에서 다음 값들을 설정하세요:

```env
# GitHub 설정
GITHUB_TOKEN=ghp_your_github_token_here
MY_GITHUB_LOGIN=your-github-username
MY_GITHUB_EMAIL=your-email@company.com

# OpenAI 설정
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 분석 설정
BRANCH=main
OUT_DIR=./reports
```

### 3. 분석할 리포지토리 설정

`main.py` 파일의 `DEFAULT_REPOS` 리스트를 수정하여 분석할 리포지토리를 설정하세요:

```python
DEFAULT_REPOS = [
    "msa-ez/legacy-modernizer-frontend",
    "uengine-oss/legacy-modernizer-backend", 
    "ahnchiyoon87/Antlr-Server"
]
```

**참고**: 환경변수로는 설정할 수 없으며, 코드에서 직접 수정해야 합니다.

## 📖 사용법

### 기본 실행

```bash
python main.py
```

### 실행 결과

- `./reports/` 폴더에 분석 결과가 저장됩니다
- 마크다운 파일: `research_note_YYYYMMDD.md`
- JSON 파일: `research_note_YYYYMMDD.json`

## 📊 출력 예시

### 마크다운 출력

```markdown
# 🧠 연구노트 — 2025-10-22 (KST)

- 생성시각(UTC): 2025-10-22 13:30:38 UTC
- 모델: `gpt-4o-mini`
- 리포지토리: msa-ez/legacy-modernizer-frontend, uengine-oss/legacy-modernizer-backend, ahnchiyoon87/Antlr-Server
- 브랜치: main
- 작성자: {'login': 'ahnchiyoon87', 'email': 'ahnpybara@uengine.org'}

## 📦 uengine-oss/legacy-modernizer-backend

### 🔖 57a4c6e — rule 파일화
- Date: 2025-10-22 18:11:46 KST
- Risk: **medium**
- Repository: uengine-oss/legacy-modernizer-backend
- Commit Link: https://github.com/uengine-oss/legacy-modernizer-backend/commit/57a4c6e9ae3798458193042da60ac548fc7528f4

> This commit introduces significant enhancements to the project, including the addition of new package versions and refactoring of the controller generation code.

- `Pipfile` (modified, risk=medium)
  - pyyaml과 jinja2 패키지 버전 추가.
```

## 🔧 설정 옵션

### 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | 필수 |
| `MY_GITHUB_LOGIN` | GitHub 사용자명 | 필수 |
| `MY_GITHUB_EMAIL` | GitHub 이메일 | 필수 |
| `OPENAI_API_KEY` | OpenAI API 키 | 필수 |
| `OPENAI_MODEL` | 사용할 OpenAI 모델 | `gpt-4o-mini` |
| `BRANCH` | 분석할 브랜치 | `main` |
| `OUT_DIR` | 결과 저장 폴더 | `./reports` |
| `MAX_FILES_PER_CALL` | 대용량 커밋 분석 시 파일 분할 단위 | `6` |

### 코드 설정

`main.py`에서 다음 값들을 수정할 수 있습니다:

- `DEFAULT_REPOS`: 분석할 리포지토리 목록 (코드에서 직접 설정)
- `MY_GITHUB_LOGIN`: GitHub 로그인 아이디 (환경변수 우선)
- `MY_GITHUB_EMAIL`: 커밋 이메일 (환경변수 우선)
- `MAX_FILES_PER_CALL`: 대용량 커밋 분석 시 파일 분할 단위 (기본값: 6)

## 📁 프로젝트 구조

```
report-generator/
├── main.py              # 메인 분석 스크립트
├── requirements.txt     # Python 의존성
├── env.template        # 환경변수 템플릿
├── README.md           # 프로젝트 문서
└── reports/            # 분석 결과 저장 폴더
    ├── research_note_20251022.md
    └── research_note_20251022.json
```

## 🛠️ 개발 정보

### 필요한 API 키

1. **GitHub Personal Access Token**
   - GitHub Settings > Developer settings > Personal access tokens
   - `repo` 권한 필요

2. **OpenAI API Key**
   - OpenAI Platform에서 발급
   - GPT-4o-mini 모델 사용 권장 (비용 효율적)

### 분석 프로세스

1. 오늘 날짜(KST) 기준으로 커밋 조회
2. 본인 커밋만 필터링
3. README 파일 자동 제외
4. 각 파일의 diff를 OpenAI로 분석
5. 대용량 커밋의 경우 청크 단위로 분할 처리
6. 커밋 전체 요약 생성
7. GitHub 커밋 링크 자동 생성
8. 마크다운과 JSON으로 결과 저장

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.
