"""Read and validate a small local JSON config without modifying it."""
import argparse
import json
from pathlib import Path
import sys


def validate_config(data):
    if not isinstance(data, dict):
        raise ValueError("최상위 값은 JSON 객체여야 합니다.")
    missing = {"app_name", "retry_count", "enabled"} - data.keys()
    if missing:
        raise ValueError("필수 항목 누락: " + ", ".join(sorted(missing)))
    if not isinstance(data["app_name"], str) or not data["app_name"].strip():
        raise ValueError("app_name은 비어 있지 않은 문자열이어야 합니다.")
    if type(data["retry_count"]) is not int or not 0 <= data["retry_count"] <= 5:
        raise ValueError("retry_count는 0~5의 정수여야 합니다.")
    if type(data["enabled"]) is not bool:
        raise ValueError("enabled는 true 또는 false여야 합니다.")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path,
                        default=Path(__file__).resolve().parent / "config.json")
    args = parser.parse_args()
    try:
        text = args.config.read_text(encoding="utf-8-sig")
        data = json.loads(text)
        config = validate_config(data)
    except json.JSONDecodeError as error:
        print(f"JSON 문법 오류: {error.lineno}행 {error.colno}열: {error.msg}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as error:
        print(f"파일 읽기 실패: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"설정 값 오류: {error}", file=sys.stderr)
        return 1
    print(f"앱: {config['app_name']}")
    print(f"재시도 횟수: {config['retry_count']}")
    print(f"사용 여부: {config['enabled']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
