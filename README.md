# 🧠 자동 깃허브 커밋 분석기

GitHub 커밋을 자동으로 분석하고 연구노트를 생성하는 도구입니다. OpenAI GPT를 활용하여 커밋의 변경사항을 분석하고, 위험도와 영향도를 평가합니다.

## ✨ 주요 기능

- **자동 커밋 분석**: 지정된 리포지토리의 오늘 커밋을 자동으로 분석
- **AI 기반 분석**: OpenAI GPT를 활용한 코드 변경사항 분석
- **위험도 평가**: 각 파일과 커밋의 위험도를 자동 평가
- **연구노트 생성**: 마크다운과 JSON 형태로 분석 결과 저장
- **한국 시간 기준**: KST 기준으로 오늘 날짜의 커밋만 분석

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
    "your-org/your-repo1",
    "your-org/your-repo2"
]
```

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
# 🧠 연구노트 — 2024-01-15 (KST)

- 생성시각(UTC): 2024-01-15 03:30:00 UTC
- 모델: `gpt-4o-mini`
- 리포지토리: your-org/your-repo
- 브랜치: main
- 작성자: {'login': 'your-username', 'email': 'your@email.com'}

## 📦 your-org/your-repo

### 🔖 a1b2c3d — feat: 새로운 기능 추가
- Date: 2024-01-15 12:30:00 KST
- Risk: **low**

> 새로운 API 엔드포인트를 추가하고 관련 테스트를 작성했습니다.

- `src/api/users.py` (added, risk=low)
  - 새로운 사용자 관리 API 엔드포인트 추가
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

### 코드 설정

`main.py`에서 다음 값들을 수정할 수 있습니다:

- `DEFAULT_REPOS`: 분석할 리포지토리 목록
- `MY_GITHUB_LOGIN`: GitHub 로그인 아이디 (환경변수 우선)
- `MY_GITHUB_EMAIL`: 커밋 이메일 (환경변수 우선)

## 📁 프로젝트 구조

```
report-generator/
├── main.py              # 메인 분석 스크립트
├── requirements.txt     # Python 의존성
├── env.template        # 환경변수 템플릿
├── README.md           # 프로젝트 문서
├── .gitignore          # Git 무시 파일
└── reports/            # 분석 결과 저장 폴더
    ├── research_note_20240115.md
    └── research_note_20240115.json
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
3. 각 파일의 diff를 OpenAI로 분석
4. 커밋 전체 요약 생성
5. 마크다운과 JSON으로 결과 저장

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
