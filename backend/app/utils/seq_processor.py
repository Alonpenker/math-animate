import json
from http.client import HTTPConnection, HTTPException
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from structlog.typing import EventDict

from app.configs.app_settings import settings

_seq_available: bool = True


class SeqProcessor:
    _executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)

    def __call__(self, logger: Any, method: str, event_dict: EventDict) -> EventDict:
        self._ship_async(self._to_clef(dict(event_dict)))
        return event_dict

    @staticmethod
    def _clef_level(level: str) -> str:
        _special = {"info": "Information", "critical": "Fatal"}
        return _special.get(level, level.capitalize())

    @staticmethod
    def _to_clef(event_dict: dict[str, Any]) -> str:
        clef: dict[str, Any] = {
            "@t": event_dict.pop("timestamp", ""),
            "@mt": event_dict.pop("event", ""),
            "@l": SeqProcessor._clef_level(event_dict.pop("level", "info")),
        }
        clef.update(event_dict)
        return json.dumps(clef)

    def _ship_async(self, clef_line: str) -> None:
        if settings.environment == "prod" or not _seq_available:
            return
        self._executor.submit(self._send, clef_line)

    def _send(self, clef_line: str) -> None:
        global _seq_available
        try:
            conn = HTTPConnection("seq", port=5341, timeout=2.0)
            conn.request(
                "POST",
                "/api/events/raw",
                body=clef_line.encode("utf-8"),
                headers={"Content-Type": "application/vnd.serilog.clef"},
            )
            conn.getresponse()
        except (OSError, HTTPException, TimeoutError):
            _seq_available = False
