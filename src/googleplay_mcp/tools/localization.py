from __future__ import annotations

import io
import mimetypes
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


# --------------------
# Android Publisher client helpers
# --------------------

def _publisher_service():
    """Return an authorized Android Publisher v3 client."""
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    return build("androidpublisher", "v3", credentials=creds, cache_discovery=False)


def _begin_edit(svc, package_name: str) -> str:
    """Insert a new edit and return its id."""
    edit = svc.edits().insert(packageName=package_name, body={}).execute()
    return edit["id"]


def _commit_edit(svc, package_name: str, edit_id: str, *, changes_not_sent_for_review: bool = False) -> Dict[str, Any]:
    return (
        svc.edits()
        .commit(
            packageName=package_name,
            editId=edit_id,
            changesNotSentForReview=changes_not_sent_for_review,
        )
        .execute()
    )


# --------------------
# 1) Locale coverage
# --------------------

def list_locale_coverage_impl(package_name: str, target_locales: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return localized listing languages currently present on the app edit.

    If `target_locales` are provided, compute coverage and missing locales.
    """
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        resp = (
            svc.edits().listings().list(packageName=package_name, editId=edit_id).execute()
        )
        present = sorted({item["language"] for item in resp.get("listings", [])})
        result: Dict[str, Any] = {"present_locales": present, "count": len(present)}
        if target_locales:
            missing = sorted(set(target_locales) - set(present))
            extra = sorted(set(present) - set(target_locales))
            result.update({
                "target_locales": target_locales,
                "missing_from_targets": missing,
                "extra_vs_targets": extra,
            })
        return result
    finally:
        # Read-only; no commit necessary
        pass


# --------------------
# 2) Clone listing between locales (text + optional assets)
# --------------------

def _http_download(url: str, *, timeout: int = 30) -> bytes:
    """Download helper with a short timeout."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content


def clone_listing_to_locale_impl(
        package_name: str,
        src_language: str,
        dst_language: str,
        *,
        copy_text: bool = True,
        copy_video: bool = True,
        copy_assets: bool = False,
        mirror_image_types: Optional[List[str]] = None,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Clone a localized store listing from `src_language` to `dst_language`.

    - Always creates/updates the destination listing via `edits.listings.update`.
    - Optionally mirrors assets by downloading the source image URLs returned by
      `edits.images.list` and re-uploading them to the destination language.
      Note: Google Play does not provide a server-side copy; assets must be re-uploaded.
    """
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)

    # 1) Read source listing
    src_listing = (
        svc.edits()
        .listings()
        .get(packageName=package_name, editId=edit_id, language=src_language)
        .execute()
    )

    body: Dict[str, Any] = {}
    if copy_text:
        for k_src, k_dst in (
                ("title", "title"),
                ("shortDescription", "shortDescription"),
                ("fullDescription", "fullDescription"),
        ):
            if k_src in src_listing:
                body[k_dst] = src_listing[k_src]
    if copy_video and "video" in src_listing:
        body["video"] = src_listing["video"]

    # 2) Upsert destination listing
    dst_listing = (
        svc.edits()
        .listings()
        .update(
            packageName=package_name,
            editId=edit_id,
            language=dst_language,
            body=body,
        )
        .execute()
    )

    # 3) Optionally mirror assets (by type)
    mirrored_assets: Dict[str, Any] = {}
    if copy_assets:
        mirror_image_types = mirror_image_types or [
            "phoneScreenshots",
            "sevenInchScreenshots",
            "tenInchScreenshots",
            "tvScreenshots",
            "wearScreenshots",
            "featureGraphic",
            "icon",
            "tvBanner",
        ]
        for image_type in mirror_image_types:
            listing_images = (
                svc.edits()
                .images()
                .list(
                    packageName=package_name,
                    editId=edit_id,
                    language=src_language,
                    imageType=image_type,
                )
                .execute()
            )
            # Clear destination assets of this type
            svc.edits().images().deleteall(
                packageName=package_name,
                editId=edit_id,
                language=dst_language,
                imageType=image_type,
            ).execute()

            uploaded: List[Dict[str, Any]] = []
            for image_obj in listing_images.get("images", []):
                url = image_obj.get("url")
                if not url:
                    continue
                content = _http_download(url)
                # Guess MIME type by remote filename if provided; fallback to PNG
                mime = mimetypes.guess_type(url)[0] or "image/png"
                with io.BytesIO(content) as buf:
                    media = MediaIoBaseUpload(buf, mimetype=mime, resumable=False)
                    uploaded_img = (
                        svc.edits()
                        .images()
                        .upload(
                            packageName=package_name,
                            editId=edit_id,
                            language=dst_language,
                            imageType=image_type,
                            media_body=media,
                            media_mime_type=mime,
                        )
                        .execute()
                    )
                    uploaded.append(uploaded_img)
            mirrored_assets[image_type] = {
                "count": len(uploaded),
                "items": uploaded,
            }

    _commit_edit(
        svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review
    )

    return {
        "dst_listing": dst_listing,
        "mirrored_assets": mirrored_assets,
    }


# --------------------
# 3) Metadata policy validation (lint)
# --------------------

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF]"
)
_REPEAT_PUNCT_RE = re.compile(r"([!?*~_\-]{2,}|\.{3,})")

_BANNED_WORDS = {
    # Performance / ranking / promo terms (non-exhaustive):
    "#1", "no.1", "best", "top", "popular", "award", "editor's choice",
    "free", "sale", "discount", "cashback", "% off", "limited time",
}


@dataclass
class PolicyIssue:
    level: str  # "error" | "warning"
    field: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


def validate_metadata_policy_impl(
        *,
        title: Optional[str] = None,
        short_description: Optional[str] = None,
        full_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate metadata strings against common Google Play policy and length limits.

    Rules (kept in sync with Play Console Help):
      - Title: ≤ 30 chars; disallow emojis, emoticons, repeated punctuation.
      - Short description: ≤ 80 chars; avoid emojis/emoticons/special sequences;
      - Full description: ≤ 4000 chars (soft limit from Play docs).
      - All fields: flag promo/ranking/best-of claims.
    Returns structured issues and basic metrics.
    """
    issues: List[PolicyIssue] = []
    metrics: Dict[str, Any] = {}

    def _len(s: Optional[str]) -> int:
        return len(s) if s is not None else 0

    # Title checks
    if title is not None:
        l = _len(title)
        metrics["title_length"] = l
        if l > 30:
            issues.append(PolicyIssue("error", "title", "Title exceeds 30 characters", "TITLE_LEN"))
        if _EMOJI_RE.search(title or ""):
            issues.append(PolicyIssue("error", "title", "Title contains emojis/emoticons", "TITLE_EMOJI"))
        if _REPEAT_PUNCT_RE.search(title or ""):
            issues.append(PolicyIssue("warning", "title", "Avoid repeated punctuation in title", "TITLE_PUNCT"))
        if any(w in title.lower() for w in _BANNED_WORDS):
            issues.append(PolicyIssue("error", "title", "Disallowed performance/promo terms in title", "TITLE_PROMO"))

    # Short description checks
    if short_description is not None:
        l = _len(short_description)
        metrics["short_description_length"] = l
        if l > 80:
            issues.append(
                PolicyIssue("error", "short_description", "Short description exceeds 80 characters", "SHORT_LEN"))
        if _EMOJI_RE.search(short_description or ""):
            issues.append(
                PolicyIssue("error", "short_description", "Short description contains emojis/emoticons", "SHORT_EMOJI"))
        if _REPEAT_PUNCT_RE.search(short_description or ""):
            issues.append(PolicyIssue("warning", "short_description", "Avoid repeated punctuation in short description",
                                      "SHORT_PUNCT"))
        if any(w in (short_description or "").lower() for w in _BANNED_WORDS):
            issues.append(
                PolicyIssue("error", "short_description", "Disallowed performance/promo terms in short description",
                            "SHORT_PROMO"))

    # Full description checks
    if full_description is not None:
        l = _len(full_description)
        metrics["full_description_length"] = l
        if l > 4000:
            issues.append(
                PolicyIssue("error", "full_description", "Full description exceeds 4000 characters", "FULL_LEN"))
        if any(w in (full_description or "").lower() for w in _BANNED_WORDS):
            issues.append(
                PolicyIssue("warning", "full_description", "Avoid performance/promo terms in full description",
                            "FULL_PROMO"))

    return {
        "issues": [issue.__dict__ for issue in issues],
        "metrics": metrics,
        "ok": not any(i.level == "error" for i in issues),
    }


# --------------------
# 4) Asset spec check (local file)
# --------------------

#: Canonical requirements derived from Play Console Help
ICON_SPEC = {
    "mime": {"image/png"},
    "exact_size": (512, 512),
}
FEATURE_GRAPHIC_SPEC = {
    "mime": {"image/png", "image/jpeg"},
    "exact_size": (1024, 500),
}
SCREENSHOT_SPEC = {
    "mime": {"image/png", "image/jpeg"},
    "min_px": 320,
    "max_px": 3840,
    "max_dim_ratio": 2.0,  # max dimension cannot be more than 2x min
}


def _image_info(fp: str) -> Tuple[str, Tuple[int, int]]:
    mime = mimetypes.guess_type(fp)[0] or "application/octet-stream"
    with Image.open(fp) as im:
        w, h = im.size
    return mime, (w, h)


def asset_spec_check_impl(image_type: str, file_path: str) -> Dict[str, Any]:
    """Validate a local asset against Google Play specs.

    `image_type` one of: 'icon', 'featureGraphic', 'phoneScreenshots',
    'sevenInchScreenshots', 'tenInchScreenshots', 'tvScreenshots', 'wearScreenshots'.
    For screenshots, all types share the same base constraints.
    """
    assert os.path.isfile(file_path), f"File not found: {file_path}"
    issues: List[str] = []

    mime, (w, h) = _image_info(file_path)

    if image_type == "icon":
        spec = ICON_SPEC
        if mime not in spec["mime"]:
            issues.append(f"Icon must be PNG (got {mime})")
        if (w, h) != spec["exact_size"]:
            issues.append(f"Icon must be exactly {spec['exact_size'][0]}x{spec['exact_size'][1]} (got {w}x{h})")
    elif image_type == "featureGraphic":
        spec = FEATURE_GRAPHIC_SPEC
        if mime not in spec["mime"]:
            issues.append(f"Feature graphic must be JPEG or PNG (got {mime})")
        if (w, h) != spec["exact_size"]:
            issues.append(
                f"Feature graphic must be exactly {spec['exact_size'][0]}x{spec['exact_size'][1]} (got {w}x{h})")
    else:
        # Screenshots
        spec = SCREENSHOT_SPEC
        if mime not in spec["mime"]:
            issues.append(f"Screenshot must be JPEG or 24-bit PNG (got {mime})")
        min_px, max_px = spec["min_px"], spec["max_px"]
        long_side, short_side = max(w, h), min(w, h)
        if short_side < min_px:
            issues.append(f"Shortest side must be ≥ {min_px}px (got {short_side}px)")
        if long_side > max_px:
            issues.append(f"Longest side must be ≤ {max_px}px (got {long_side}px)")
        if long_side > short_side * spec["max_dim_ratio"]:
            issues.append(
                f"Longest side cannot exceed {spec['max_dim_ratio']}x shortest side (got {long_side}/{short_side})"
            )

    return {
        "file_path": file_path,
        "image_type": image_type,
        "mime": mime,
        "width": w,
        "height": h,
        "ok": len(issues) == 0,
        "issues": issues,
    }
