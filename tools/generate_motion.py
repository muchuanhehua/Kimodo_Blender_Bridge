"""Generate verification motions through the exact addon subprocess bridge."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("kimodo_verification_client", root / "subprocess_client.py")
    client = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = client
    spec.loader.exec_module(client)
    python = args.runtime / "Scripts/python.exe"
    args.output.mkdir(parents=True, exist_ok=True)
    record = []
    try:
        ok, message = client.start(str(python.resolve()), "Kimodo-SOMA-RP-v1", use_offload=False,
                                   progress_callback=lambda message: print(message, flush=True))
        if not ok:
            raise RuntimeError(message)
        for name, prompt in (("walk", "A person walks forward at a natural pace."),
                             ("wave", "A person stands still and waves their right hand.")):
            ok, result = client.generate_motion(prompt, 3.0, 42, output_format="bvh",
                bvh_standard_tpose=True, progress_callback=lambda message: print(message, flush=True))
            if not ok:
                raise RuntimeError(result)
            source = Path(result)
            destination = args.output / (name + ".bvh")
            shutil.copy2(source, destination)
            source.unlink()
            record.append({"name": name, "prompt": prompt, "seconds": 3.0, "seed": 42,
                           "file": destination.name, "bytes": destination.stat().st_size})
            print("GENERATED", json.dumps(record[-1]), flush=True)
        (args.output / "generation.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    finally:
        client.stop()


if __name__ == "__main__":
    main()
