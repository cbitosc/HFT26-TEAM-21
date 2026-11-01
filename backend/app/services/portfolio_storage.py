"""
Portfolio storage service for SkillProof AI (Module 3).
Provides persistent storage for student portfolios.
- Uses Supabase PostgreSQL 'portfolios' table when configured.
- Provides an automated, thread-safe local JSON storage fallback
  in backend/data/portfolios.json when Supabase credentials are not set.
- Strictly confines each student's read/write operations to their own user_id.
"""

from __future__ import annotations

import os
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.config import get_settings
from app.models import PortfolioResponse, PortfolioStructure

logger = logging.getLogger("skillproof.portfolio.storage")

# Path for local development storage fallback
LOCAL_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
LOCAL_STORAGE_FILE = os.path.join(LOCAL_STORAGE_DIR, "portfolios.json")

_local_lock = threading.Lock()


def _ensure_local_storage() -> None:
    """Ensures local storage directory and JSON file exist."""
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    if not os.path.exists(LOCAL_STORAGE_FILE):
        with open(LOCAL_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _read_local_store() -> Dict[str, Any]:
    _ensure_local_storage()
    with _local_lock:
        try:
            with open(LOCAL_STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Error reading local portfolio store, reinitializing: %s", exc)
            return {}


def _write_local_store(data: Dict[str, Any]) -> None:
    _ensure_local_storage()
    with _local_lock:
        with open(LOCAL_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def get_portfolio(user_id: uuid.UUID) -> Optional[PortfolioResponse]:
    """
    Retrieves the portfolio for the specified user_id.
    Returns None if no portfolio has been uploaded/created.
    """
    settings = get_settings()
    uid_str = str(user_id)

    # 1. Try Supabase if configured
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from app.supabase_client import service_client
            res = service_client().table("portfolios").select("*").eq("user_id", uid_str).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                return PortfolioResponse(
                    id=str(row.get("id")),
                    user_id=uuid.UUID(row["user_id"]),
                    confirmed=bool(row.get("confirmed", False)),
                    confirmed_at=row.get("confirmed_at"),
                    skills_status=row.get("skills_status", "unverified"),
                    data=PortfolioStructure(**row.get("portfolio_data", {})),
                    raw_filename=row.get("raw_filename"),
                    file_type=row.get("file_type"),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                )
        except Exception as exc:
            logger.warning("Supabase portfolio read failed, falling back to local: %s", exc)
            if settings.app_env == "production":
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Production database unavailable. Local fallback disabled.")

    # 2. Local fallback restricted in production
    if settings.app_env == "production":
        return None

    store = _read_local_store()
    entry = store.get(uid_str)
    if not entry:
        return None

    return PortfolioResponse(
        id=entry.get("id"),
        user_id=uuid.UUID(entry["user_id"]),
        confirmed=bool(entry.get("confirmed", False)),
        confirmed_at=datetime.fromisoformat(entry["confirmed_at"]) if entry.get("confirmed_at") else None,
        skills_status=entry.get("skills_status", "unverified"),
        data=PortfolioStructure(**entry.get("data", {})),
        raw_filename=entry.get("raw_filename"),
        file_type=entry.get("file_type"),
        created_at=datetime.fromisoformat(entry["created_at"]) if entry.get("created_at") else None,
        updated_at=datetime.fromisoformat(entry["updated_at"]) if entry.get("updated_at") else None,
    )


def save_portfolio(
    user_id: uuid.UUID,
    portfolio_data: PortfolioStructure,
    confirmed: bool,
    raw_filename: Optional[str] = None,
    file_type: Optional[str] = None,
) -> PortfolioResponse:
    """
    Persists or updates the portfolio for the specified student user_id.
    """
    settings = get_settings()
    uid_str = str(user_id)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    confirmed_at = now_iso if confirmed else None

    # Check for existing entry to preserve id and created_at
    existing = get_portfolio(user_id)
    record_id = existing.id if (existing and existing.id) else str(uuid.uuid4())
    created_at = existing.created_at.isoformat() if (existing and existing.created_at) else now_iso
    final_raw_filename = raw_filename or (existing.raw_filename if existing else "manual_entry")
    final_file_type = file_type or (existing.file_type if existing else "json")

    final_confirmed = confirmed
    final_confirmed_at = now_iso if confirmed else None

    payload_dict = {
        "id": record_id,
        "user_id": uid_str,
        "confirmed": final_confirmed,
        "confirmed_at": final_confirmed_at,
        "skills_status": "unverified",  # Mandatory: skills are unverified until tested
        "portfolio_data": portfolio_data.model_dump(),
        "raw_filename": final_raw_filename,
        "file_type": final_file_type,
        "created_at": created_at,
        "updated_at": now_iso,
    }

    # 1. Try Supabase if configured
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from app.supabase_client import service_client
            service_client().table("portfolios").upsert(
                payload_dict, on_conflict="user_id"
            ).execute()
        except Exception as exc:
            logger.warning("Supabase portfolio upsert failed, saving to local fallback: %s", exc)
            if settings.app_env == "production":
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Production database unavailable. Local fallback disabled.")

    # 2. Local store only maintained in non-production environments
    if settings.app_env != "production":
        store = _read_local_store()
        store[uid_str] = {
            "id": record_id,
            "user_id": uid_str,
            "confirmed": final_confirmed,
            "confirmed_at": final_confirmed_at,
            "skills_status": "unverified",
            "data": portfolio_data.model_dump(),
            "raw_filename": final_raw_filename,
            "file_type": final_file_type,
            "created_at": created_at,
            "updated_at": now_iso,
        }
        _write_local_store(store)

    return PortfolioResponse(
        id=record_id,
        user_id=user_id,
        confirmed=final_confirmed,
        confirmed_at=datetime.fromisoformat(final_confirmed_at) if final_confirmed_at else None,
        skills_status="unverified",
        data=portfolio_data,
        raw_filename=final_raw_filename,
        file_type=final_file_type,
        created_at=datetime.fromisoformat(created_at) if created_at else now,
        updated_at=now,
    )
