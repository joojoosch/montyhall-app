# Saving the participant files: to the private GitHub data repo, or to a
# local folder when testing on my own computer.
#
# File name: data/{mode}/{code}_{sequence}.json
# The sequence is in the name so I can count A and B with one request.
# Every save writes the whole file, so if one save fails, the next one
# contains everything again.

import base64
import json
import os
import random
import sys
import time

API = "https://api.github.com"
API_VERSION = "2026-03-10"


def file_path(mode, pid, sequence):
    return f"data/{mode}/{pid}_{sequence}.json"


def count_from_names(names):
    counts = {"A": 0, "B": 0}
    for n in names:
        if n.endswith("_A.json"):
            counts["A"] += 1
        elif n.endswith("_B.json"):
            counts["B"] += 1
    return counts


def _log(msg):
    print(f"[storage] {msg}", file=sys.stderr, flush=True)


class LocalStorage:
    # for testing on my computer (real mode refuses to run with this)

    kind = "local"

    def __init__(self, root="local_data"):
        self.root = root

    def _full(self, path):
        return os.path.join(self.root, path)

    def save(self, rec):
        path = self._full(file_path(rec["mode"], rec["participant_id"], rec["sequence"]))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True

    def load(self, mode, pid, sequence):
        path = self._full(file_path(mode, pid, sequence))
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def count_sequences(self, mode):
        folder = self._full(f"data/{mode}")
        if not os.path.isdir(folder):
            return {"A": 0, "B": 0}
        return count_from_names(os.listdir(folder))


class GitHubStorage:
    # Writes files into the private repo through the GitHub API.
    # GitHub says writes at the same moment can clash (error 409), so I retry
    # with random waits and fetch the file's current version id (sha) if needed.

    kind = "github"

    def __init__(self, repo, token, branch="main", http=None, sleep=time.sleep,
                 max_attempts=5):
        if http is None:
            import requests
            http = requests.Session()
        self.repo = repo
        self.branch = branch
        self.http = http
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }
        self._sha = {}  # file -> current version id, needed to update a file

    def _url(self, path):
        return f"{API}/repos/{self.repo}/contents/{path}"

    def _get(self, path):
        return self.http.get(self._url(path), headers=self.headers,
                             params={"ref": self.branch}, timeout=15)

    def _refresh_sha(self, path):
        try:
            r = self._get(path)
            if r.status_code == 200:
                self._sha[path] = r.json()["sha"]
            elif r.status_code == 404:
                self._sha.pop(path, None)
        except Exception as e:  # network problem, just try again later
            _log(f"sha refresh failed for {path}: {e}")

    def save(self, rec):
        path = file_path(rec["mode"], rec["participant_id"], rec["sequence"])
        content = base64.b64encode(
            json.dumps(rec, ensure_ascii=False, indent=1).encode("utf-8")).decode("ascii")
        for attempt in range(1, self.max_attempts + 1):
            body = {"message": f"data {rec['participant_id']} {rec['step']}",
                    "content": content, "branch": self.branch}
            if path in self._sha:
                body["sha"] = self._sha[path]
            try:
                r = self.http.put(self._url(path), headers=self.headers, json=body, timeout=20)
                status = r.status_code
            except Exception as e:
                _log(f"attempt {attempt}: network error {e}")
                status = None
            if status in (200, 201):
                self._sha[path] = r.json()["content"]["sha"]
                return True
            if status is not None:
                _log(f"attempt {attempt}: HTTP {status} for {path}")
            if status in (401, 404):
                # wrong token or repo name, retrying won't help
                return False
            if status in (409, 422):
                # clash or outdated version id: get the current one and retry
                self._refresh_sha(path)
            if attempt < self.max_attempts:
                self.sleep(random.uniform(0.5, 1.5) * attempt)
        return False

    def load(self, mode, pid, sequence):
        path = file_path(mode, pid, sequence)
        try:
            r = self._get(path)
        except Exception as e:
            _log(f"load failed: {e}")
            return None
        if r.status_code != 200:
            return None
        data = r.json()
        self._sha[path] = data["sha"]
        return json.loads(base64.b64decode(data["content"]).decode("utf-8"))

    def count_sequences(self, mode):
        try:
            r = self._get(f"data/{mode}")
            if r.status_code == 200:
                return count_from_names(item["name"] for item in r.json())
        except Exception as e:
            _log(f"count failed: {e}")
        return {"A": 0, "B": 0}  # no folder yet or error -> random sequence


def make_storage(secrets):
    # GitHub if the secrets are set, otherwise local
    try:
        token = secrets["GITHUB_TOKEN"]
        repo = secrets["DATA_REPO"]
        branch = secrets.get("DATA_BRANCH", "main") if hasattr(secrets, "get") else "main"
    except Exception:
        return LocalStorage()
    return GitHubStorage(repo, token, branch)
