"""Single-process logging practice. Only writes to a logs folder beside this file."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def make_logger(log_dir):
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("logging_practice")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    for handler in (console, file_handler):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate-error", action="store_true")
    args = parser.parse_args()
    log_dir = Path(__file__).resolve().parent / "logs"
    logger = make_logger(log_dir)
    logger.info("작업 시작")
    logger.debug("입력 준비: item_count=%d", 3)
    try:
        value = int("not-a-number" if args.simulate_error else "42")
    except ValueError:
        logger.exception("숫자 변환 실패")
        return 1
    logger.info("작업 완료: result=%d", value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
