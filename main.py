#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, textwrap, datetime as dt
from typing import List, Optional, Dict, Any
from dateutil import tz
from tenacity import retry, wait_random_exponential, stop_after_attempt
from github import Github
from openai import OpenAI
from dotenv import load_dotenv

# ======================================
# 🔧 1. 환경설정
# ======================================
# .env 파일에서 환경변수 로드 (없으면 무시)
load_dotenv()

# --- [A] 하드코딩 설정 (원하면 이 블록만 수정) ---
DEFAULT_REPOS = [
    "msa-ez/legacy-modernizer-frontend",
    "uengine-oss/legacy-modernizer-backend", 
    "ahnchiyoon87/Antlr-Server"
]
MY_GITHUB_LOGIN = os.getenv("MY_GITHUB_LOGIN", "your-github-id")     # GitHub 로그인 아이디
MY_GITHUB_EMAIL = os.getenv("MY_GITHUB_EMAIL", "you@company.com")     # 커밋 이메일
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")               # OpenAI 모델
BRANCH = os.getenv("BRANCH", "main")                                  # 분석할 브랜치
OUT_DIR = os.getenv("OUT_DIR", "./reports")                           # 결과 저장 폴더
os.makedirs(OUT_DIR, exist_ok=True)

# --- [B] 토큰 관리 ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "ghp_...")                   # GitHub Personal Access Token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")                # OpenAI API Key

if not GITHUB_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("❌ GITHUB_TOKEN 또는 OPENAI_API_KEY가 누락되었습니다. .env에 설정하세요.")

# ======================================
# 📦 2. 데이터 모델 정의 (Pydantic 없이)
# ======================================
class FileFinding:
    def __init__(self, file_path: str, change_type: str, summary: str, risk_level: str, 
                 breaking_changes: List[str] = None, test_impact: List[str] = None, 
                 migration_notes: List[str] = None, owner_guess: Optional[str] = None):
        self.file_path = file_path
        self.change_type = change_type
        self.summary = summary
        self.risk_level = risk_level
        self.breaking_changes = breaking_changes or []
        self.test_impact = test_impact or []
        self.migration_notes = migration_notes or []
        self.owner_guess = owner_guess
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "breaking_changes": self.breaking_changes,
            "test_impact": self.test_impact,
            "migration_notes": self.migration_notes,
            "owner_guess": self.owner_guess
        }

class CommitFinding:
    def __init__(self, repo: str, sha: str, author: Optional[str], author_login: Optional[str], 
                 author_email: Optional[str], date_kst: str, title: str, files: List[FileFinding],
                 overall_summary: str, overall_risk: str):
        self.repo = repo
        self.sha = sha
        self.author = author
        self.author_login = author_login
        self.author_email = author_email
        self.date_kst = date_kst
        self.title = title
        self.files = files
        self.overall_summary = overall_summary
        self.overall_risk = overall_risk

class ReportModel:
    def __init__(self, generated_at: str, model: str, note_date_kst: str, repos: List[str], 
                 branch: str, author_filter: dict, commits: List[CommitFinding]):
        self.generated_at = generated_at
        self.model = model
        self.note_date_kst = note_date_kst
        self.repos = repos
        self.branch = branch
        self.author_filter = author_filter
        self.commits = commits
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "model": self.model,
            "note_date_kst": self.note_date_kst,
            "repos": self.repos,
            "branch": self.branch,
            "author_filter": self.author_filter,
            "commits": [
                {
                    "repo": c.repo,
                    "sha": c.sha,
                    "author": c.author,
                    "author_login": c.author_login,
                    "author_email": c.author_email,
                    "date_kst": c.date_kst,
                    "title": c.title,
                    "files": [f.to_dict() for f in c.files],
                    "overall_summary": c.overall_summary,
                    "overall_risk": c.overall_risk
                } for c in self.commits
            ]
        }

# ======================================
# ⏰ 3. 날짜 계산 (오늘 날짜 자동)
# ======================================
def get_today_kst_bounds():
    kst = tz.gettz("Asia/Seoul")
    now_kst = dt.datetime.now(tz=kst)
    note_date = now_kst.strftime("%Y-%m-%d")
    start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    end_kst = start_kst + dt.timedelta(days=1)
    return note_date, start_kst.astimezone(tz.UTC), end_kst.astimezone(tz.UTC)

# ======================================
# 🤖 4. OpenAI & GitHub 클라이언트
# ======================================
gh = Github(GITHUB_TOKEN, per_page=100)
oai = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "당신은 매우 경험 많은 시니어 코드 리뷰어이자 기술 문서 작성자입니다. 파일 변경사항을 매우 상세하고 포괄적으로 분석하여 연구노트 수준의 자세한 설명을 제공하세요. "
    "JSON 형식으로 응답하되: file_path, change_type, summary (최소 300단어 이상), risk_level (low/medium/high), "
    "breaking_changes (배열), test_impact (배열), migration_notes (배열). "
    "한글로 매우 상세하게 다음을 모두 포함하여 설명하세요: "
    "1) 구체적인 코드 변경 내용과 기술적 세부사항, "
    "2) 변경의 배경과 비즈니스적/기술적 필요성, "
    "3) 해결하려는 문제와 기존 이슈, "
    "4) 구현 방식과 아키텍처적 고려사항, "
    "5) 성능, 보안, 유지보수성에 미치는 영향, "
    "6) 다른 모듈이나 시스템과의 연관성, "
    "7) 향후 확장성과 개선 방향, "
    "8) 개발자나 팀에게 미치는 영향, "
    "9) 잠재적 위험과 주의사항, "
    "10) 테스트 전략과 검증 방법. "
    "연구노트 수준의 깊이와 상세함으로 작성하세요."
)

# ======================================
# 🧠 5. LLM 호출
# ======================================
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4))
def analyze_file(file_path: str, change_type: str, patch: str) -> FileFinding:
    resp = oai.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system", "content": SYSTEM_PROMPT},
            {"role":"user", "content": f"file_path: {file_path}\nchange_type: {change_type}\n\nDIFF:\n{patch or ''}"}
        ]
    ).choices[0].message.content
    try:
        data = json.loads(resp)
        return FileFinding(
            file_path=data.get("file_path", file_path),
            change_type=data.get("change_type", change_type),
            summary=data.get("summary", "LLM parsing failed"),
            risk_level=data.get("risk_level", "medium"),
            breaking_changes=data.get("breaking_changes", []),
            test_impact=data.get("test_impact", []),
            migration_notes=data.get("migration_notes", []),
            owner_guess=data.get("owner_guess")
        )
    except Exception:
        return FileFinding(file_path=file_path, change_type=change_type, summary="LLM parsing failed", risk_level="medium")

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4))
def summarize_commit(files: List[FileFinding], meta: dict) -> CommitFinding:
    resp = oai.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":"커밋의 전체적인 작업 내용을 연구노트 수준으로 매우 상세하고 포괄적으로 한글로 서술하세요. 최소 1000단어 이상으로 다음을 모두 포함하여 설명하세요: 1) 수행한 작업의 구체적 내용과 기술적 세부사항, 2) 작업의 배경과 비즈니스적/기술적 필요성, 3) 해결하려는 문제와 기존 이슈의 맥락, 4) 선택한 기술적 접근 방식과 구현 전략, 5) 코드 아키텍처의 변화와 설계 개선점, 6) 성능, 보안, 확장성, 유지보수성에 미치는 영향, 7) 다른 시스템이나 모듈과의 연관성과 의존성, 8) 팀 개발 프로세스와 협업에 미치는 영향, 9) 향후 개발 방향과 확장 가능성, 10) 잠재적 위험과 대응 방안, 11) 테스트 전략과 품질 보증 방법, 12) 문서화와 지식 공유 측면, 13) 비용과 리소스에 미치는 영향, 14) 사용자나 고객에게 미치는 영향. 각 파일의 변경사항을 종합하여 하나의 일관되고 완전한 작업 스토리로 설명하세요. 연구노트의 깊이와 전문성을 유지하세요."},
            {"role":"user","content":json.dumps({"meta":meta,"files":[f.to_dict() for f in files]}, ensure_ascii=False)}
        ]
    ).choices[0].message.content
    data = json.loads(resp)
    return CommitFinding(
        repo=meta["repo"], 
        sha=meta["sha"], 
        author=meta.get("author"),
        author_login=meta.get("author_login"), 
        author_email=meta.get("author_email"),
        date_kst=meta["date_kst"], 
        title=meta["title"], 
        files=files,
        overall_summary=data.get("overall_summary",""), 
        overall_risk=data.get("overall_risk","medium")
    )

# ======================================
# 🔍 6. GitHub 커밋 필터
# ======================================
def commit_is_mine(commit) -> bool:
    login = getattr(commit.author, "login", None)
    email = getattr(commit.commit.author, "email", None)
    return (
        (login and login.lower() == MY_GITHUB_LOGIN.lower()) or
        (email and email.lower() == MY_GITHUB_EMAIL.lower())
    )

# ======================================
# 🧾 7. 결과 출력
# ======================================
def render_md(report: ReportModel) -> str:
    lines = [
        f"# 🧠 연구노트 — {report.note_date_kst} (KST)",
        "",
        f"- 생성시각(UTC): {report.generated_at}",
        f"- 모델: `{report.model}`",
        f"- 리포지토리: {', '.join(report.repos)}",
        f"- 브랜치: {report.branch}",
        f"- 작성자: {report.author_filter}",
        ""
    ]
    if not report.commits:
        lines.append("> 오늘은 본인 커밋이 없습니다.")
        return "\n".join(lines)

    current_repo = None
    for c in report.commits:
        if c.repo != current_repo:
            current_repo = c.repo
            lines.append(f"## 📦 {current_repo}\n")
        lines.append(f"### 🔖 {c.sha[:7]} — {c.title}")
        lines.append(f"- Date: {c.date_kst}")
        lines.append(f"- Risk: **{c.overall_risk}**")
        lines.append(f"- Repository: {c.repo}")
        lines.append(f"- Commit Link: https://github.com/{c.repo}/commit/{c.sha}")
        lines.append("")
        lines.append("## 📝 작업 내용 종합 분석")
        lines.append("")
        lines.append("### 🎯 작업 개요")
        lines.append("")
        lines.append("> " + (c.overall_summary or "(요약 없음)").replace("\n", "\n> "))
        lines.append("")
        lines.append("## 📁 파일별 상세 기술 분석")
        lines.append("")
        for f in c.files:
            lines.append(f"### 📄 `{f.file_path}` ({f.change_type})")
            lines.append(f"**위험도:** {f.risk_level}")
            lines.append("")
            lines.append("#### 🔍 기술적 변경 내용")
            lines.append("")
            lines.append(f"{f.summary}")
            lines.append("")
            if f.breaking_changes:
                lines.append("#### ⚠️ 주요 변경사항 및 호환성 영향")
                lines.append("")
                for change in f.breaking_changes:
                    lines.append(f"- {change}")
                lines.append("")
            if f.test_impact:
                lines.append("#### 🧪 테스트 전략 및 영향 분석")
                lines.append("")
                for impact in f.test_impact:
                    lines.append(f"- {impact}")
                lines.append("")
            if f.migration_notes:
                lines.append("#### 🔄 마이그레이션 가이드 및 주의사항")
                lines.append("")
                for note in f.migration_notes:
                    lines.append(f"- {note}")
                lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines)

# ======================================
# 🚀 8. 메인 실행
# ======================================
def main():
    note_date, since_utc, until_utc = get_today_kst_bounds()
    print(f"[INFO] Analyzing commits for {note_date} (KST)...")
    print(f"[INFO] Time range: {since_utc} ~ {until_utc} (UTC)")
    print(f"[INFO] Target repositories: {DEFAULT_REPOS}")
    print(f"[INFO] Branch: {BRANCH}")
    print(f"[INFO] Author filter: {MY_GITHUB_LOGIN} / {MY_GITHUB_EMAIL}")
    print("=" * 60)

    commits_all: List[CommitFinding] = []

    for repo_full in DEFAULT_REPOS:
        print(f"\n[REPO] Processing repository: {repo_full}")
        try:
            repo = gh.get_repo(repo_full)
            print(f"[REPO] ✅ Successfully connected to {repo_full}")
            
            commits = repo.get_commits(sha=BRANCH, since=since_utc, until=until_utc)
            commit_list = list(commits)
            print(f"[REPO] 📊 Found {len(commit_list)} total commits in time range")
            
            my_commits = []
            for i, c in enumerate(commit_list):
                if not commit_is_mine(c):
                    continue
                
                sha = c.sha
                print(f"[COMMIT] 🔍 Processing commit {sha[:7]} ({i+1}/{len(commit_list)})")
                
                co = repo.get_commit(sha)
                title = co.commit.message.splitlines()[0].strip()
                author_name = co.commit.author.name if co.commit.author else None
                author_login = co.author.login if co.author else None
                author_email = co.commit.author.email if co.commit.author else None
                authored_dt = co.commit.author.date.replace(tzinfo=tz.UTC).astimezone(tz.gettz("Asia/Seoul"))
                date_kst_str = authored_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                
                print(f"[COMMIT] 📝 Title: {title}")
                print(f"[COMMIT] 👤 Author: {author_name} ({author_email})")
                print(f"[COMMIT] 📅 Date: {date_kst_str}")

                # 파일별 분석 (README만 제외, 파일 제한 없음)
                important_files = [f for f in co.files if 'readme' not in f.filename.lower()]
                files_to_analyze = important_files
                print(f"[COMMIT] 📁 Analyzing {len(files_to_analyze)} files (out of {len(co.files)} total) - README excluded")
                
                # 처리할 파일이 없으면 건너뛰기
                if len(files_to_analyze) == 0:
                    print(f"[COMMIT] ⏭️  Skipping commit (no files to analyze)")
                    continue
                
                file_findings = []
                for j, f in enumerate(files_to_analyze):
                    print(f"[FILE] 🔍 Analyzing file {j+1}/{len(files_to_analyze)}: {f.filename} ({f.status})")
                    patch = getattr(f, "patch", None)
                    if not patch:
                        print(f"[FILE] ⚠️  No patch available for {f.filename} (binary or no diff)")
                        file_findings.append(FileFinding(file_path=f.filename, change_type=f.status, summary="Binary or no diff", risk_level="medium"))
                    else:
                        print(f"[FILE] 🤖 Sending to LLM for analysis...")
                        file_findings.append(analyze_file(f.filename, f.status, patch))
                        print(f"[FILE] ✅ LLM analysis completed for {f.filename}")

                print(f"[COMMIT] 🤖 Sending commit summary to LLM...")
                meta = {
                    "repo": repo_full,
                    "sha": sha,
                    "title": title,
                    "author": author_name,
                    "author_login": author_login,
                    "author_email": author_email,
                    "date_kst": date_kst_str
                }
                commit_finding = summarize_commit(file_findings, meta)
                commits_all.append(commit_finding)
                my_commits.append(commit_finding)
                print(f"[COMMIT] ✅ Completed analysis for {sha[:7]}")
            
            print(f"[REPO] 📊 Found {len(my_commits)} of your commits in {repo_full}")
            
        except Exception as e:
            print(f"[REPO] ❌ Error processing {repo_full}: {str(e)}")
            print(f"[REPO] 🔄 Continuing with next repository...")
            continue

    print(f"\n[SUMMARY] 📊 Analysis completed!")
    print(f"[SUMMARY] 📈 Total commits analyzed: {len(commits_all)}")
    print(f"[SUMMARY] 📝 Generating report...")

    report = ReportModel(
        generated_at=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        model=OPENAI_MODEL,
        note_date_kst=note_date,
        repos=DEFAULT_REPOS,
        branch=BRANCH,
        author_filter={"login": MY_GITHUB_LOGIN, "email": MY_GITHUB_EMAIL},
        commits=commits_all
    )

    md_path = os.path.join(OUT_DIR, f"research_note_{note_date.replace('-','')}.md")
    json_path = os.path.join(OUT_DIR, f"research_note_{note_date.replace('-','')}.json")

    print(f"[OUTPUT] 📄 Writing markdown report to: {md_path}")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_md(report))
    
    print(f"[OUTPUT] 📄 Writing JSON report to: {json_path}")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))

    print(f"\n✅ 연구노트 생성 완료!")
    print(f"📁 Markdown: {md_path}")
    print(f"📁 JSON: {json_path}")
    print(f"📊 Total commits: {len(commits_all)}")

if __name__ == "__main__":
    main()
