import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

LOG_FILE = "assistant_log.json"

_log_entries: list[dict] = []


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("FilesAI")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s  [%(name)s]  %(levelname)-8s  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger


def generate_session_id() -> str:
    return str(uuid.uuid4())


def log_event(
    logger: logging.Logger,
    level: str,
    event_type: str,
    session_id: str,
    source_type: str | None,
    source_identifier: str | None,
    model: str,
    error_message: str | None = None,
    summary_length: int | None = None,
) -> None:
    entry: dict = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "event_type": event_type,
        "session_id": session_id,
        "source_type": source_type,
        "source_identifier": source_identifier,
        "model": model,
        "error_message": error_message,
        "summary_length": summary_length,
    }

    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(f"[{event_type}] source={source_type} id={source_identifier}")

    _log_entries.append(entry)
    _flush_to_file()


def _flush_to_file(filename: str = LOG_FILE) -> None:
    try:
        path = Path(filename)
        path.write_text(json.dumps(_log_entries, indent=2), encoding="utf-8")
    except OSError as exc:
        logging.getLogger("FilesAI").warning(
            "Could not write log file '%s': %s", filename, exc
        )
