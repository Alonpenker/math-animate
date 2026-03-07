import re
from typing import Optional
from pathlib import Path
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.services.files_storage_service import FilesStorageService

BYTE_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _invalid_range_error(file_size: int, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
        detail=detail,
        headers={"Content-Range": f"bytes */{file_size}"},
    )


def _handle_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    match = BYTE_RANGE_RE.fullmatch(range_header.strip())
    if match is None:
        raise _invalid_range_error(
            file_size,
            "Invalid Range header format. Use bytes=<start>-<end>.",
        )

    start_str, end_str = match.groups()
    if not start_str and not end_str:
        raise _invalid_range_error(
            file_size,
            "Invalid Range header format. Use bytes=<start>-<end>.",
        )

    if start_str:
        start = int(start_str)
        if start >= file_size:
            raise _invalid_range_error(file_size, "Range start is out of bounds.")

        end = int(end_str) if end_str else file_size - 1
        if end < start:
            raise _invalid_range_error(file_size, "Range end must be >= start.")

        end = min(end, file_size - 1)
        return start, end

    # Suffix range: bytes=-N (last N bytes)
    suffix_length = int(end_str)
    if suffix_length <= 0:
        raise _invalid_range_error(file_size, "Range suffix must be greater than zero.")

    if suffix_length >= file_size:
        return 0, file_size - 1

    return file_size - suffix_length, file_size - 1


def build_video_stream_response(
    storage: FilesStorageService,
    artifact_path: str,
    range_header: Optional[str],
) -> StreamingResponse:
    file_name = Path(artifact_path).name
    file_size = storage.get_artifact_size(artifact_path)
    if not file_size:
        raise HTTPException(
            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
            detail="Range is not satisfiable for an empty file.",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    def iterfile(stream, chunk_size: int = 1024 * 1024):
        try:
            while True:
                data = stream.read(chunk_size)
                if not data:
                    break
                yield data
        finally:
            stream.close()
            release_conn = getattr(stream, "release_conn", None)
            if callable(release_conn):
                release_conn()

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{file_name}"',
    }

    if range_header:
        start, end = _handle_range_header(range_header, file_size)
        length = end - start + 1
        stream = storage.open_artifact_stream(artifact_path, offset=start, length=length)
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        headers["Content-Length"] = str(length)
        return StreamingResponse(
            iterfile(stream),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type="video/mp4",
            headers=headers,
        )

    stream = storage.open_artifact_stream(artifact_path)
    headers["Content-Length"] = str(file_size)
    return StreamingResponse(
        iterfile(stream),
        status_code=status.HTTP_200_OK,
        media_type="video/mp4",
        headers=headers,
    )
