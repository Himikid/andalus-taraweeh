#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


DEFAULT_PROJECT_ID = ""
DEFAULT_API_KEY = ""
DEFAULT_DATABASE_ID = "(default)"
DEFAULT_REQUESTS_COLLECTION = "andalus_transcription_requests"
DEFAULT_RUNTIME_COLLECTION = "andalus_transcription_runtime"
DEFAULT_SESSION_ID = "default"


def _encode_value(value: Any) -> dict[str, Any]:
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_encode_value(item) for item in value]}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {str(k): _encode_value(v) for k, v in value.items()}}}
    return {"stringValue": str(value)}


def _decode_value(node: dict[str, Any]) -> Any:
    if "nullValue" in node:
        return None
    if "booleanValue" in node:
        return bool(node["booleanValue"])
    if "integerValue" in node:
        try:
            return int(str(node["integerValue"]))
        except ValueError:
            return 0
    if "doubleValue" in node:
        try:
            return float(node["doubleValue"])
        except (TypeError, ValueError):
            return 0.0
    if "timestampValue" in node:
        return str(node["timestampValue"])
    if "stringValue" in node:
        return str(node["stringValue"])
    if "arrayValue" in node:
        values = node.get("arrayValue", {}).get("values", [])
        return [_decode_value(item) for item in values if isinstance(item, dict)]
    if "mapValue" in node:
        fields = node.get("mapValue", {}).get("fields", {})
        if not isinstance(fields, dict):
            return {}
        return {key: _decode_value(value) for key, value in fields.items() if isinstance(value, dict)}
    return None


def _decode_document(payload: dict[str, Any]) -> dict[str, Any]:
    fields = payload.get("fields", {})
    result: dict[str, Any] = {}
    if isinstance(fields, dict):
        for key, value in fields.items():
            if isinstance(value, dict):
                result[key] = _decode_value(value)
    if "name" in payload:
        result["_name"] = payload["name"]
    if "createTime" in payload:
        result["_create_time"] = payload["createTime"]
    if "updateTime" in payload:
        result["_update_time"] = payload["updateTime"]
    return result


def _flatten_keys(payload: dict[str, Any], prefix: str = "") -> list[str]:
    keys: list[str] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else key
        keys.append(path)
        if isinstance(value, dict):
            keys.extend(_flatten_keys(value, prefix=path))
    return keys


@dataclass
class FirestoreConfig:
    enabled: bool
    project_id: str
    api_key: str
    database_id: str
    requests_collection: str
    runtime_collection: str
    session_id: str


def load_firestore_config(config_path: Path | None) -> FirestoreConfig:
    payload: dict[str, Any] = {}
    if config_path is not None and config_path.exists():
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            payload = {}

    node = payload.get("firestore")
    if not isinstance(node, dict):
        node = {}
    enabled = bool(node.get("enabled", False))
    project_id = str(node.get("project_id") or DEFAULT_PROJECT_ID).strip()
    api_key = str(node.get("api_key") or DEFAULT_API_KEY).strip()
    database_id = str(node.get("database_id") or DEFAULT_DATABASE_ID).strip()
    requests_collection = str(node.get("requests_collection") or DEFAULT_REQUESTS_COLLECTION).strip()
    runtime_collection = str(node.get("runtime_collection") or DEFAULT_RUNTIME_COLLECTION).strip()
    session_id = str(node.get("session_id") or DEFAULT_SESSION_ID).strip()
    if enabled:
        if not project_id:
            raise RuntimeError("Firestore enabled but firestore.project_id is missing in config.")
        if not api_key:
            raise RuntimeError("Firestore enabled but firestore.api_key is missing in config.")

    return FirestoreConfig(
        enabled=enabled,
        project_id=project_id,
        api_key=api_key,
        database_id=database_id,
        requests_collection=requests_collection,
        runtime_collection=runtime_collection,
        session_id=session_id,
    )


class FirestoreRestClient:
    def __init__(self, config: FirestoreConfig, timeout_seconds: int = 25) -> None:
        self.config = config
        self.timeout_seconds = max(3, int(timeout_seconds))
        self.base = (
            f"https://firestore.googleapis.com/v1/projects/{self.config.project_id}"
            f"/databases/{self.config.database_id}/documents"
        )

    def _request(self, method: str, url: str, *, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query["key"] = self.config.api_key
        response = requests.request(
            method=method,
            url=url,
            params=query,
            json=body,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Firestore REST {method} {url} failed ({response.status_code}): {response.text[:400]}")
        if not response.text:
            return {}
        return response.json()

    def patch_document(self, document_path: str, payload: dict[str, Any]) -> dict[str, Any]:
        doc = document_path.strip("/")
        if not doc:
            raise ValueError("document_path is required")
        url = f"{self.base}/{doc}"
        body = {"fields": {str(key): _encode_value(value) for key, value in payload.items()}}
        update_mask = _flatten_keys(payload)
        params = [("updateMask.fieldPaths", path) for path in update_mask] if update_mask else None
        # requests supports list tuples via params=
        response = requests.patch(
            url,
            params=([("key", self.config.api_key)] + (params or [])),
            json=body,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Firestore REST PATCH {doc} failed ({response.status_code}): {response.text[:400]}")
        return response.json() if response.text else {}

    def get_document(self, document_path: str) -> dict[str, Any] | None:
        doc = document_path.strip("/")
        if not doc:
            raise ValueError("document_path is required")
        url = f"{self.base}/{doc}"
        response = requests.get(
            url,
            params={"key": self.config.api_key},
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise RuntimeError(f"Firestore REST GET {doc} failed ({response.status_code}): {response.text[:400]}")
        return _decode_document(response.json())

    def query_requests(self, *, status: str, limit: int = 5, session_id: str | None = None) -> list[dict[str, Any]]:
        collection_url = f"{self.base}/{self.config.requests_collection}"
        response = requests.get(
            collection_url,
            params={
                "key": self.config.api_key,
                "pageSize": max(10, int(limit) * 10),
            },
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Firestore REST list documents failed ({response.status_code}): {response.text[:400]}"
            )
        rows: list[dict[str, Any]] = []
        payload = response.json()
        documents = payload.get("documents")
        if not isinstance(documents, list):
            return rows
        session = (session_id or self.config.session_id).strip()
        wanted_status = str(status).strip().lower()
        for doc in documents:
            if not isinstance(doc, dict):
                continue
            decoded = _decode_document(doc)
            name = str(doc.get("name", ""))
            if name:
                decoded["_name"] = name
                decoded["_document_path"] = name.split("/documents/", 1)[-1]
            row_session = str(decoded.get("session_id", "")).strip()
            row_status = str(decoded.get("status", "")).strip().lower()
            if row_session != session:
                continue
            if row_status != wanted_status:
                continue
            rows.append(decoded)
        rows.sort(key=lambda item: str(item.get("created_at", "")))
        return rows[: max(1, int(limit))]
