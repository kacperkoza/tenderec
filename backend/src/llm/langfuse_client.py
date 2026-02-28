"""Lightweight Langfuse client using the REST ingestion API.

The official Langfuse Python SDK relies on Pydantic V1 internally, which is
incompatible with Python 3.14.  This module talks directly to the
``POST /api/public/ingestion`` endpoint so we can record traces without the SDK.
"""

import logging
import time
import uuid
from datetime import datetime, timezone

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

_INGESTION_URL = f"{settings.langfuse_base_url}/api/public/ingestion"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _new_id() -> str:
    return str(uuid.uuid4())


class LangfuseTrace:
    """Accumulates events for a single trace, then flushes them in one batch."""

    def __init__(
        self,
        name: str,
        user_id: str | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        self.trace_id = _new_id()
        self.name = name
        self.user_id = user_id
        self.session_id = session_id
        self.tags = tags or []
        self._events: list[dict[str, object]] = []
        self._start_time = time.perf_counter()
        self._start_iso = _now_iso()

    # -- public helpers to record observations --------------------------------

    def add_generation(
        self,
        *,
        name: str,
        model: str,
        input_messages: object,
        output_message: str,
        start_time: str | None = None,
        end_time: str | None = None,
        usage_input_tokens: int | None = None,
        usage_output_tokens: int | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        gen_id = _new_id()
        body: dict[str, object] = {
            "id": gen_id,
            "traceId": self.trace_id,
            "name": name,
            "model": model,
            "input": input_messages,
            "output": output_message,
            "startTime": start_time or _now_iso(),
            "endTime": end_time or _now_iso(),
        }
        if usage_input_tokens is not None or usage_output_tokens is not None:
            body["usage"] = {
                "input": usage_input_tokens,
                "output": usage_output_tokens,
            }
        if metadata:
            body["metadata"] = metadata
        self._events.append(
            {
                "id": _new_id(),
                "type": "generation-create",
                "timestamp": _now_iso(),
                "body": body,
            }
        )
        return gen_id

    def add_span(
        self,
        *,
        name: str,
        input_data: object = None,
        output_data: object = None,
        start_time: str | None = None,
        end_time: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        span_id = _new_id()
        body: dict[str, object] = {
            "id": span_id,
            "traceId": self.trace_id,
            "name": name,
            "startTime": start_time or _now_iso(),
            "endTime": end_time or _now_iso(),
        }
        if input_data is not None:
            body["input"] = input_data
        if output_data is not None:
            body["output"] = output_data
        if metadata:
            body["metadata"] = metadata
        self._events.append(
            {
                "id": _new_id(),
                "type": "span-create",
                "timestamp": _now_iso(),
                "body": body,
            }
        )
        return span_id

    # -- flush ----------------------------------------------------------------

    async def flush(
        self,
        *,
        input_data: object = None,
        output_data: object = None,
    ) -> None:
        """Send the trace and all accumulated observations to Langfuse."""
        if not settings.langfuse_enabled or not settings.langfuse_secret_key:
            return

        end_iso = _now_iso()

        trace_body: dict[str, object] = {
            "id": self.trace_id,
            "name": self.name,
            "timestamp": self._start_iso,
        }
        if input_data is not None:
            trace_body["input"] = input_data
        if output_data is not None:
            trace_body["output"] = output_data
        if self.user_id:
            trace_body["userId"] = self.user_id
        if self.session_id:
            trace_body["sessionId"] = self.session_id
        if self.tags:
            trace_body["tags"] = self.tags

        trace_event: dict[str, object] = {
            "id": _new_id(),
            "type": "trace-create",
            "timestamp": end_iso,
            "body": trace_body,
        }

        batch = [trace_event, *self._events]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    _INGESTION_URL,
                    json={"batch": batch},
                    auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
                )
                if response.status_code >= 400:
                    logger.warning(
                        "Langfuse ingestion failed: %s %s",
                        response.status_code,
                        response.text,
                    )
                else:
                    logger.debug(
                        "Langfuse trace %s flushed (%d events)",
                        self.trace_id,
                        len(batch),
                    )
        except Exception:
            logger.warning("Failed to send trace to Langfuse", exc_info=True)
