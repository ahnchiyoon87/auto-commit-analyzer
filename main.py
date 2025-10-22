#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, textwrap, datetime as dt
from typing import List, Optional, Dict, Any
from dateutil import tz
from tenacity import retry, wait_random_exponential, stop_after_attempt
from github import Github
from openai import OpenAI, BadRequestError
from dotenv import load_dotenv

# ======================================
# 🔧 1. 환경설정
# ======================================
load_dotenv()

# --- [A] 하드코딩 설정 (원하면 이 블록만 수정) ---
DEFAULT_REPOS = [
    "msa-ez/legacy-modernizer-frontend",
    "uengine-oss/legacy-modernizer-backend",
    "ahnchiyoon87/Antlr-Server"
]
MY_GITHUB_LOGIN = os.getenv("MY_GITHUB_LOGIN", "your-github-id")     # GitHub 로그인 아이디
MY_GITHUB_EMAIL = os.getenv("MY_GITHUB_EMAIL", "you@company.com")     # 커밋 이메일
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")            # OpenAI 모델
BRANCH          = os.getenv("BRANCH", "main")                         # 분석할 브랜치
OUT_DIR         = os.getenv("OUT_DIR", "./reports")                   # 결과 저장 폴더
os.makedirs(OUT_DIR, exist_ok=True)

# 대용량 커밋 요약 시 파일을 나누는 단위(권장: 8~15)
MAX_FILES_PER_CALL = int(os.getenv("MAX_FILES_PER_CALL", "6"))

# --- [B] 토큰 관리 ---
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "ghp_...")                 # GitHub Personal Access Token
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
    "당신은 코드 리뷰어입니다. 파일 변경사항을 분석하고 간단한 요약을 제공하세요. "
    "JSON 형식으로 응답하되: file_path, change_type, summary (최대 30단어), risk_level (low/medium/high). "
    "한글로 간결하게 핵심 변경사항만 설명하세요."
)

# ======================================
# 🧠 5. LLM 호출
# ======================================
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4))
def analyze_file(file_path: str, change_type: str, patch: str) -> FileFinding:
    """파일 단위 요약 (성공적으로 동작 중)"""
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

def _lighten_files(files: List[FileFinding]) -> List[Dict[str, Any]]:
    """커밋 요약 입력을 슬림화 (필요 필드만 포함)"""
    return [
        {
            "file_path": f.file_path,
            "change_type": f.change_type,
            "summary": f.summary,
            "risk_level": f.risk_level
        }
        for f in files
    ]

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4))
def _summarize_chunk(meta: dict, light_files_chunk: List[Dict[str, Any]]) -> Dict[str, Any]:
    """청크 단위 부분 요약"""
    resp = oai.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":"아래 파일 변경 요약을 바탕으로 커밋의 의도/영향을 5줄 내로 JSON으로 반환(overall_summary, overall_risk: low/medium/high)."},
            {"role":"user","content": json.dumps({"meta": {
                "repo": meta.get("repo",""),
                "sha": meta.get("sha",""),
                "title": meta.get("title","")
            }, "files": light_files_chunk}, ensure_ascii=False)}
        ]
    )
    out = resp.choices[0].message.content
    try:
        return json.loads(out)
    except Exception:
        return {"overall_summary":"(부분 요약 파싱 실패)","overall_risk":"medium"}

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4))
def _summarize_merge(partials: List[str]) -> Dict[str, Any]:
    """부분 요약들을 최종 통합"""
    prompt = "\n\n".join(partials)
    resp = oai.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":"부분 요약들을 통합해 최종 overall_summary(6~10문장)와 overall_risk(low/medium/high)만 JSON으로 반환."},
            {"role":"user","content": prompt}
        ]
    )
    out = resp.choices[0].message.content
    try:
        return json.loads(out)
    except Exception:
        return {"overall_summary":"(최종 통합 요약 파싱 실패)","overall_risk":"medium"}

def fallback_summarize_commit(files: List[FileFinding], meta: dict) -> CommitFinding:
    """모델 실패 시 로컬 요약으로 대체"""
    order = {"high":0,"medium":1,"low":2}
    top = sorted(files, key=lambda x: order.get(x.risk_level,1))[:3]
    bullet = "\n".join([f"- {f.file_path} ({f.change_type}, {f.risk_level}): {f.summary}" for f in top])
    overall = (
        f"[로컬요약] {meta.get('title','')}\n"
        f"주요 변경 파일(상위 3개):\n{bullet}"
    )
    return CommitFinding(
        repo=meta["repo"], sha=meta["sha"],
        author=meta.get("author"), author_login=meta.get("author_login"),
        author_email=meta.get("author_email"), date_kst=meta["date_kst"],
        title=meta["title"], files=files,
        overall_summary=overall,
        overall_risk=("high" if any(f.risk_level=="high" for f in files) else "medium")
    )

def summarize_commit(files: List[FileFinding], meta: dict) -> CommitFinding:
    """
    커밋 요약:
    - 입력 슬림화
    - 파일 많을 경우 청크 요약 → 최종 통합
    - 실패 시 BadRequest 메시지 출력 + 로컬 Fallback
    """
    light_files = _lighten_files(files)
    try:
        # 파일 수가 적으면 1회 호출로 끝내기
        if len(light_files) <= MAX_FILES_PER_CALL:
            partial = _summarize_chunk(meta, light_files)
            final = partial
        else:
            # 청크 요약
            chunks = [light_files[i:i+MAX_FILES_PER_CALL] for i in range(0, len(light_files), MAX_FILES_PER_CALL)]
            partial_summaries = []
            for idx, ch in enumerate(chunks, 1):
                partial = _summarize_chunk(meta, ch)
                partial_summaries.append(partial.get("overall_summary",""))
            final = _summarize_merge(partial_summaries)

        return CommitFinding(
            repo=meta["repo"],
            sha=meta["sha"],
            author=meta.get("author"),
            author_login=meta.get("author_login"),
            author_email=meta.get("author_email"),
            date_kst=meta["date_kst"],
            title=meta["title"],
            files=files,
            overall_summary=final.get("overall_summary",""),
            overall_risk=final.get("overall_risk","medium")
        )
    except BadRequestError as e:
        # 상세 메시지 최대한 표시
        msg = getattr(e, "message", str(e))
        print(f"[COMMIT] ❌ BadRequest while summarizing {meta['sha'][:7]}: {msg}")
        return fallback_summarize_commit(files, meta)
    except Exception as e:
        print(f"[COMMIT] ❌ Unexpected error while summarizing {meta['sha'][:7]}: {e}")
        return fallback_summarize_commit(files, meta)

# ======================================
# 🔍 6. GitHub 커밋 필터
# ======================================
def commit_is_mine(commit) -> bool:
    login = getattr(commit.author, "login", None)
    email = getattr(commit.commit.author, "email", None)
    return (
        (login and login.strip().lower() == MY_GITHUB_LOGIN.strip().lower()) or
        (email and email.strip().lower() == MY_GITHUB_EMAIL.strip().lower())
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
        lines.append("> " + (c.overall_summary or "(요약 없음)").replace("\n", "\n> "))
        lines.append("")
        lines.append("**📁 변경된 파일들:**")
        for f in c.files:
            lines.append(f"- `{f.file_path}` ({f.change_type}, risk={f.risk_level})")
            lines.append(f"  - {f.summary}")
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

            my_commits_count = 0

            for i, c in enumerate(commit_list):
                if not commit_is_mine(c):
                    continue

                # 커밋 단위 예외 처리(레포 전체 중단 방지)
                try:
                    sha = c.sha
                    print(f"[COMMIT] 🔍 Processing commit {sha[:7]} ({i+1}/{len(commit_list)})")

                    co = repo.get_commit(sha)
                    title = co.commit.message.splitlines()[0].strip()
                    author_name  = co.commit.author.name if co.commit.author else None
                    author_login = co.author.login if co.author else None
                    author_email = co.commit.author.email if co.commit.author else None
                    authored_dt  = co.commit.author.date.replace(tzinfo=tz.UTC).astimezone(tz.gettz("Asia/Seoul"))
                    date_kst_str = authored_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

                    print(f"[COMMIT] 📝 Title: {title}")
                    print(f"[COMMIT] 👤 Author: {author_name} ({author_email})")
                    print(f"[COMMIT] 📅 Date: {date_kst_str}")

                    # 파일별 분석 (README 제외)
                    important_files = [f for f in co.files if 'readme' not in f.filename.lower()]
                    files_to_analyze = important_files
                    print(f"[COMMIT] 📁 Analyzing {len(files_to_analyze)} files (out of {len(co.files)} total) - README excluded")

                    if len(files_to_analyze) == 0:
                        print(f"[COMMIT] ⏭️  Skipping commit (no files to analyze)")
                        continue

                    file_findings: List[FileFinding] = []
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
                    my_commits_count += 1
                    print(f"[COMMIT] ✅ Completed analysis for {sha[:7]}")

                except BadRequestError as e:
                    msg = getattr(e, "message", str(e))
                    print(f"[COMMIT] ❌ BadRequest on {c.sha[:7]}: {msg}")
                    # 파일 분석은 끝났다면 Fallback으로라도 기록
                    try:
                        commit_finding = fallback_summarize_commit(file_findings, meta)  # type: ignore
                        commits_all.append(commit_finding)
                        my_commits_count += 1
                        print(f"[COMMIT] 🔁 Fallback summary added for {c.sha[:7]}")
                    except Exception as fe:
                        print(f"[COMMIT] ⚠️ Fallback failed on {c.sha[:7]}: {fe}")
                    continue
                except Exception as e:
                    print(f"[COMMIT] ❌ Error on {c.sha[:7]}: {e}")
                    # 원하면 여기서도 fallback 시도 가능
                    continue

            print(f"[REPO] 📊 Found {my_commits_count} of your commits in {repo_full}")

        except Exception as e:
            print(f"[REPO] ❌ Error processing {repo_full}: {str(e)}")
            print(f"[REPO] 🔄 Continuing with next repository...")
            continue

    print(f"\n[SUMMARY] 📊 Analysis completed!")
    print(f"[SUMMARY] 📈 Total commits analyzed: {len(commits_all)}")
    print(f"[SUMMARY] 📝 Generating report...")

    report = ReportModel(
        generated_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
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
