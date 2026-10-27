"""Install the same offline backend used by the community bridge into a venv.

Run with system Python 3.12. The environment and models stay outside the addon.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import venv


def run(command, env):
    print("RUN", " ".join(str(arg) for arg in command), flush=True)
    subprocess.run([str(arg) for arg in command], env=env, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parents[1] / ".runtime/kimodo-venv")
    parser.add_argument("--models-only", action="store_true")
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    runtime.parent.mkdir(parents=True, exist_ok=True)
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(runtime)
    env = os.environ.copy()
    env.update(HF_HOME=str(runtime / "hf-cache"), HF_HUB_DISABLE_XET="1",
               SKIP_MOTION_CORRECTION_IN_SETUP="1", PYTHONUTF8="1")
    pip = [python, "-m", "pip"]
    if not args.models_only:
        run([python, "-m", "ensurepip", "--upgrade"], env)
        run([*pip, "install", "--upgrade", "pip"], env)
        run([*pip, "install", "torch==2.5.1", "--index-url", "https://download.pytorch.org/whl/cu121"], env)
        run([*pip, "install", "https://github.com/Aero-Ex/kimodo/releases/download/v1.0.0/motion_correction-1.0.0-cp312-cp312-win_amd64.whl"], env)
        for project in ("Aero-Ex/kimodo", "nv-tlabs/kimodo-viser"):
            request = urllib.request.Request(f"https://api.github.com/repos/{project}/commits/main", headers={"User-Agent": "Kimodo-Blender-Bridge"})
            with urllib.request.urlopen(request, timeout=60) as response:
                commit = json.load(response)["sha"]
            run([*pip, "install", f"https://github.com/{project}/archive/{commit}.zip"], env)
        run([*pip, "install", "bitsandbytes>=0.46.1", "safetensors", "psutil"], env)
    model_dir = runtime / "llm2vec-model"
    downloader = Path(__file__).resolve().parents[1] / "model_download.py"
    run([python, downloader, "--repo", "Aero-Ex/KIMODO-Meta3_llm2vec_NF4", "--local-dir", model_dir], env)
    run([python, downloader, "--repo", "nvidia/Kimodo-SOMA-RP-v1"], env)
    wrapper = runtime / "Lib/site-packages/kimodo/model/llm2vec/llm2vec_wrapper.py"
    text = wrapper.read_text(encoding="utf-8")
    placeholder = "path_to_your_Llama_text-encoders"
    if placeholder in text:
        wrapper.write_text(text.replace(placeholder, model_dir.as_posix()), encoding="utf-8")
    elif model_dir.as_posix() not in text:
        raise RuntimeError("Cannot configure the backend text encoder path")
    installed = subprocess.check_output([str(python), "-m", "pip", "freeze"], env=env, text=True)
    (runtime / "installed-requirements.txt").write_text(installed, encoding="utf-8")
    (runtime / ".kimodo_install_complete").write_text("", encoding="utf-8")
    print("KIMODO_RUNTIME_READY", python, flush=True)


if __name__ == "__main__":
    main()
