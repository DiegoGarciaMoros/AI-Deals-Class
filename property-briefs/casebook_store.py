"""Cases added through the app, stored in data/added_cases.json in the GitHub repo.

Streamlit Cloud wipes the app's disk on every restart, so the app saves added cases by
committing them to the repo through the GitHub API. Without a token (e.g. running
locally) it reads and writes the local file instead.

Secrets / env vars:
    GITHUB_TOKEN    fine-grained token with "Contents: read and write" on this repo
    GITHUB_REPO     owner/repo   (default: DiegoGarciaMoros/AI-Deals-Class)
    GITHUB_BRANCH   branch the app deploys from (default: claude/amazing-gauss-ggp9w6)
"""
import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
LOCAL_PATH = HERE / "data" / "added_cases.json"
REPO_PATH = "property-briefs/data/added_cases.json"
DEFAULTS = {"GITHUB_REPO": "DiegoGarciaMoros/AI-Deals-Class",
            "GITHUB_BRANCH": "claude/amazing-gauss-ggp9w6"}


def setting(name, secrets=None):
    try:
        if secrets is not None and name in secrets:
            return secrets[name]
    except Exception:  # noqa: BLE001 - no secrets file when run locally
        pass
    return os.environ.get(name) or DEFAULTS.get(name)


def case_key(name):
    """'Pierson v. Post' and 'PIERSON v POST' -> 'piersonvpost'"""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


class Store:
    def __init__(self, secrets=None):
        self.token = setting("GITHUB_TOKEN", secrets)
        self.repo = setting("GITHUB_REPO", secrets)
        self.branch = setting("GITHUB_BRANCH", secrets)

    @property
    def remote(self):
        return bool(self.token)

    def _api(self, method, body=None):
        url = f"https://api.github.com/repos/{self.repo}/contents/{REPO_PATH}"
        if method == "GET":
            url += f"?ref={urllib.request.quote(self.branch)}"
        req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Accept": "application/vnd.github+json",
                                              "Content-Type": "application/json",
                                              "User-Agent": "property-case-briefer"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def _read_remote(self):
        """(cases, sha); sha is None if the file doesn't exist yet."""
        try:
            data = self._api("GET")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return [], None
            raise
        return json.loads(base64.b64decode(data["content"]) or b"[]"), data["sha"]

    def load(self):
        if self.remote:
            return self._read_remote()[0]
        return json.loads(LOCAL_PATH.read_text()) if LOCAL_PATH.exists() else []

    def add(self, entry, existing_keys=()):
        """Append a case. Returns False if it's already in the casebook."""
        for _ in range(3):  # retry if someone else added a case at the same moment
            cases, sha = self._read_remote() if self.remote else (self.load(), None)
            keys = set(existing_keys) | {case_key(c["case_name"]) for c in cases}
            if case_key(entry["case_name"]) in keys:
                return False
            text = json.dumps(cases + [entry], indent=1) + "\n"
            if not self.remote:
                LOCAL_PATH.write_text(text)
                return True
            body = {"message": f"Add {entry['case_name']} to the casebook (via the app)",
                    "content": base64.b64encode(text.encode()).decode(), "branch": self.branch}
            if sha:
                body["sha"] = sha
            try:
                self._api("PUT", body)
                return True
            except urllib.error.HTTPError as e:
                if e.code not in (409, 422):  # stale sha: re-read and try again
                    raise RuntimeError(f"GitHub said HTTP {e.code}: {e.read().decode(errors='replace')[:200]}") from e
        raise RuntimeError("Couldn't save after 3 tries; please try again.")
