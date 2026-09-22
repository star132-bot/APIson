"""
tools/updater.py
检查并执行来自 GitHub 的自动更新。
"""

import subprocess
from pathlib import Path
from typing import Optional

_REPO_OWNER = "star132-bot"
_REPO_NAME = "APIson"
_BRANCH = "main"
_GITHUB_API = f"https://api.github.com/repos/{_REPO_OWNER}/{_REPO_NAME}/commits/{_BRANCH}"
_REMOTE_CHANGELOG = f"https://raw.githubusercontent.com/{_REPO_OWNER}/{_REPO_NAME}/{_BRANCH}/CHANGELOG.md"

_ROOT = Path(__file__).parent.parent
_VERSION_FILE = _ROOT / "VERSION"


def _latest_changelog_section(text: str) -> str:
    """Return the newest version section instead of showing the entire history."""
    lines = text.strip().splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## ")), None)
    if start is None:
        return text.strip()
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def get_local_version() -> Optional[str]:
    """Use Git HEAD in a checkout; VERSION is only a packaged-build fallback."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_ROOT, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    if _VERSION_FILE.exists():
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    return None


def get_remote_version() -> dict:
    """从 GitHub API 获取最新 commit 信息"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "缺少 requests 库"}
    try:
        resp = requests.get(
            _GITHUB_API,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=8,
        )
        if resp.status_code != 200:
            return {"success": False, "error": f"GitHub API 返回 {resp.status_code}"}
        data = resp.json()
        full_sha = data.get("sha", "")
        commit_info = data.get("commit", {})
        message = commit_info.get("message", "").split("\n")[0]
        date = commit_info.get("committer", {}).get("date", "")
        changelog = ""
        try:
            notes_resp = requests.get(_REMOTE_CHANGELOG, timeout=8)
            if notes_resp.status_code == 200:
                changelog = _latest_changelog_section(notes_resp.text)
        except Exception:
            pass
        return {"success": True, "sha": full_sha[:7], "full_sha": full_sha,
                "message": message, "date": date, "changelog": changelog}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_update() -> dict:
    """检查是否有新版本"""
    local = get_local_version()
    remote = get_remote_version()
    if not remote.get("success"):
        return {"has_update": False, "error": remote.get("error"), "local_sha": (local or "未知")[:7]}
    full_sha = remote.get("full_sha", "")
    local_short = (local or "")[:7]
    has_update = bool(full_sha and local and not full_sha.startswith(local))
    return {
        "has_update": has_update,
        "local_sha": local_short or "未知",
        "remote_sha": remote.get("sha", ""),
        "remote_message": remote.get("message", ""),
        "remote_date": remote.get("date", ""),
        "release_notes": remote.get("changelog", "") or remote.get("message", ""),
        "full_remote_sha": full_sha,
        "error": None,
    }


def do_update() -> dict:
    """执行 git pull 拉取最新代码"""
    try:
        check = subprocess.run(
            ["git", "status"], cwd=_ROOT, capture_output=True, text=True, timeout=5,
        )
        if check.returncode != 0:
            return {"success": False, "error": "当前目录不是 git 仓库，请访问 GitHub 手动下载最新版本。"}
        result = subprocess.run(
            ["git", "pull", "origin", _BRANCH],
            cwd=_ROOT, capture_output=True, text=True, timeout=60,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            try:
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=_ROOT, capture_output=True, text=True, timeout=5,
                )
                if sha_result.returncode == 0:
                    _VERSION_FILE.write_text(sha_result.stdout.strip(), encoding="utf-8")
            except Exception:
                pass
            notes = ""
            changelog_file = _ROOT / "CHANGELOG.md"
            if changelog_file.exists():
                notes = _latest_changelog_section(changelog_file.read_text(encoding="utf-8"))
            return {"success": True, "output": output, "release_notes": notes}
        else:
            return {"success": False, "error": output or "git pull 失败"}
    except FileNotFoundError:
        return {"success": False, "error": "未找到 git 命令，请手动访问 GitHub 下载。"}
    except Exception as e:
        return {"success": False, "error": str(e)}
