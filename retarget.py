"""Bone-mapping preset storage; solving lives in motion_retarget.py."""
import json


def _presets(preferences):
    try:
        data = json.loads(preferences.saved_presets)
    except json.JSONDecodeError as exc:
        raise ValueError("已保存的骨骼映射预设损坏，请导出备份后修复") from exc
    if not isinstance(data, dict):
        raise ValueError("骨骼映射预设必须是 JSON 对象")
    return data


def save_preset(preferences, name, pairs):
    presets = _presets(preferences)
    presets[name] = pairs
    preferences.saved_presets = json.dumps(presets, ensure_ascii=False)


def load_preset(preferences, name):
    return _presets(preferences).get(name)


def list_presets(preferences):
    return list(_presets(preferences))
