"""Bounded, resumable Hugging Face downloads with LFS size/hash validation.

This helper is executable by the external Python environment and imports no bpy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request


class _Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        redirected = super().redirect_request(request, fp, code, message, headers, new_url)
        if redirected and urllib.parse.urlsplit(request.full_url).hostname != urllib.parse.urlsplit(new_url).hostname:
            redirected.remove_header("Authorization")
        return redirected


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_repo(repo_id, local_dir=None, token="", cache_root=None):
    headers = {"User-Agent": "Kimodo-Blender-Bridge/1.6", "Accept-Encoding": "identity"}
    if token:
        headers["Authorization"] = "Bearer " + token
    opener = urllib.request.build_opener(_Redirect())
    api = f"https://huggingface.co/api/models/{repo_id}/revision/main?blobs=true"
    with opener.open(urllib.request.Request(api, headers=headers), timeout=45) as response:
        metadata = json.load(response)
    revision = metadata["sha"]
    cache = Path(cache_root or os.environ.get("HF_HUB_CACHE") or
                 Path(os.environ.get("HF_HOME", str(Path.home() / ".cache/huggingface"))) / "hub")
    repository = cache / ("models--" + repo_id.replace("/", "--"))
    destination = Path(local_dir) if local_dir else repository / "snapshots" / revision
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    allowed_root = destination if local_dir else repository.resolve()
    total = sum(file.get("size", 0) for file in metadata["siblings"])
    complete = 0
    for item in metadata["siblings"]:
        relative = item["rfilename"]
        output = (destination / relative).resolve()
        if not output.is_relative_to(allowed_root):
            raise ValueError("Invalid model repository path")
        size = item.get("size")
        checksum = item.get("lfs", {}).get("sha256")
        if output.is_file() and (size is None or output.stat().st_size == size) and (not checksum or _digest(output) == checksum):
            complete += output.stat().st_size
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        partial = output.with_name(output.name + ".part")
        if partial.exists() and size is not None and partial.stat().st_size > size:
            raise RuntimeError("Partial model file is larger than the expected download: " + relative)
        failures = 0
        while size is None or not partial.exists() or partial.stat().st_size < size:
            offset = partial.stat().st_size if partial.exists() else 0
            chunk_end = min(offset + 32 * 1024 * 1024 - 1, size - 1) if size else None
            request_headers = dict(headers)
            if chunk_end is not None:
                request_headers["Range"] = f"bytes={offset}-{chunk_end}"
            url = f"https://huggingface.co/{repo_id}/resolve/{revision}/{urllib.parse.quote(relative, safe='/')}?download=true"
            try:
                with opener.open(urllib.request.Request(url, headers=request_headers), timeout=60) as response:
                    if offset and response.status != 206:
                        raise RuntimeError("Server refused a resumed model download: " + relative)
                    if response.status == 206:
                        expected = f"bytes {offset}-"
                        if not response.headers.get("Content-Range", "").startswith(expected):
                            raise RuntimeError("Model download returned the wrong byte range: " + relative)
                    with partial.open("ab" if offset else "wb") as file:
                        for data in iter(lambda: response.read(1024 * 1024), b""):
                            file.write(data)
                failures = 0
            except (OSError, urllib.error.URLError) as exc:
                failures += 1
                if failures >= 3:
                    raise RuntimeError(f"模型下载失败：{repo_id}/{relative}，请检查网络后重试") from exc
                time.sleep(failures)
                continue
            current = partial.stat().st_size
            percentage = round(100 * (complete + current) / total, 1) if total else 0
            print(f"Downloading {relative}: {percentage}% ({current}/{size or current} bytes)", flush=True)
            if size is None:
                break
            if current <= offset:
                raise RuntimeError("Model download made no progress: " + relative)
        if size is not None and partial.stat().st_size != size:
            raise RuntimeError("Model size verification failed: " + relative)
        if checksum and _digest(partial) != checksum:
            raise RuntimeError("Model SHA256 verification failed: " + relative)
        partial.replace(output)
        complete += output.stat().st_size
    if local_dir is None:
        refs = repository / "refs"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "main").write_text(revision, encoding="utf-8")
    print("MODEL_VERIFIED", repo_id, revision, flush=True)
    return str(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--local-dir")
    args = parser.parse_args()
    download_repo(args.repo, args.local_dir, os.environ.get("HF_TOKEN", ""))
