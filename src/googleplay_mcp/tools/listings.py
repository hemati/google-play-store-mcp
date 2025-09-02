from __future__ import annotations

import mimetypes
from typing import Any, Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


# ---------- Internal helpers ----------

def _publisher_service():
    """Return an authorized Android Publisher v3 client."""
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    return build("androidpublisher", "v3", credentials=creds, cache_discovery=False)


def _begin_edit(svc, package_name: str) -> str:
    """Insert a new edit and return its id."""
    edit = svc.edits().insert(packageName=package_name, body={}).execute()
    return edit["id"]


def _commit_edit(svc, package_name: str, edit_id: str, *, changes_not_sent_for_review: bool = False) -> Dict[str, Any]:
    """Commit an edit. Set `changes_not_sent_for_review=True` to avoid auto-review when required by Play."""
    return (
        svc.edits()
        .commit(
            packageName=package_name,
            editId=edit_id,
            changesNotSentForReview=changes_not_sent_for_review,
        )
        .execute()
    )


# ---------- Listings (text/video) ----------

def list_localized_listings_impl(package_name: str) -> Dict[str, Any]:
    """Return all localized store listings attached to a fresh edit.

    This is read-only; no commit is required.
    """
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        resp = svc.edits().listings().list(packageName=package_name, editId=edit_id).execute()
        return resp
    finally:
        # No commit for read ops; edits expire shortly by themselves.
        pass


def get_listing_impl(package_name: str, language: str) -> Dict[str, Any]:
    """Get a single localized listing by BCP-47 language (e.g., "en-US")."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        return (
            svc.edits()
            .listings()
            .get(packageName=package_name, editId=edit_id, language=language)
            .execute()
        )
    finally:
        pass


def patch_listing_impl(
        package_name: str,
        language: str,
        *,
        title: Optional[str] = None,
        short_description: Optional[str] = None,
        full_description: Optional[str] = None,
        video: Optional[str] = None,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Patch a localized listing. Only non-null fields are updated.

    Title limit ~30 chars, short description ~80, full description ~4000 (policy may change).
    """
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)

    body: Dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if short_description is not None:
        body["shortDescription"] = short_description
    if full_description is not None:
        body["fullDescription"] = full_description
    if video is not None:
        body["video"] = video

    try:
        resp = (
            svc.edits()
            .listings()
            .patch(
                packageName=package_name,
                editId=edit_id,
                language=language,
                body=body,
            )
            .execute()
        )
        _commit_edit(svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review)
        return resp
    except HttpError as e:
        raise RuntimeError(f"Failed to patch listing for {package_name} [{language}]: {e}")


def update_listing_impl(
        package_name: str,
        language: str,
        *,
        title: str,
        short_description: str,
        full_description: str,
        video: Optional[str] = None,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Create or replace a localized listing (full update)."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)

    body: Dict[str, Any] = {
        "title": title,
        "shortDescription": short_description,
        "fullDescription": full_description,
    }
    if video:
        body["video"] = video

    try:
        resp = (
            svc.edits()
            .listings()
            .update(
                packageName=package_name,
                editId=edit_id,
                language=language,
                body=body,
            )
            .execute()
        )
        _commit_edit(svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review)
        return resp
    except HttpError as e:
        raise RuntimeError(f"Failed to update listing for {package_name} [{language}]: {e}")


# ---------- Images (assets) ----------

def images_list_impl(package_name: str, language: str, image_type: str) -> Dict[str, Any]:
    """List images for a language and AppImageType (e.g., 'phoneScreenshots', 'featureGraphic', 'icon')."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        return (
            svc.edits()
            .images()
            .list(
                packageName=package_name,
                editId=edit_id,
                language=language,
                imageType=image_type,
            )
            .execute()
        )
    finally:
        pass


def images_deleteall_impl(
        package_name: str,
        language: str,
        image_type: str,
        *,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Delete all images for a language and image type."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        resp = (
            svc.edits()
            .images()
            .deleteall(
                packageName=package_name,
                editId=edit_id,
                language=language,
                imageType=image_type,
            )
            .execute()
        )
        _commit_edit(svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review)
        return resp
    except HttpError as e:
        raise RuntimeError(
            f"Failed to delete images for {package_name} [{language}/{image_type}]: {e}"
        )


def images_upload_impl(
        package_name: str,
        language: str,
        image_type: str,
        file_path: str,
        *,
        mime_type: Optional[str] = None,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Upload an image (icon/screenshot/featureGraphic) to the edit and commit.

    Args:
        package_name: App package name.
        language: BCP-47 language tag (e.g., "en-US").
        image_type: AppImageType (e.g., 'phoneScreenshots', 'sevenInchScreenshots', 'tenInchScreenshots',
            'tvScreenshots', 'wearScreenshots', 'icon', 'featureGraphic', 'tvBanner').
        file_path: Local path to the image file.
        mime_type: Optional explicit MIME type; guessed from filename if omitted.
        changes_not_sent_for_review: Commit with changesNotSentForReview flag when required by Play after rejections.
    """
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    guessed = mime_type or (mimetypes.guess_type(file_path)[0] or "application/octet-stream")

    try:
        media = MediaFileUpload(filename=file_path, mimetype=guessed, chunksize=-1, resumable=False)
        resp = (
            svc.edits()
            .images()
            .upload(
                packageName=package_name,
                editId=edit_id,
                language=language,
                imageType=image_type,
                media_body=media,
                media_mime_type=guessed,
            )
            .execute()
        )
        _commit_edit(svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review)
        return resp
    except HttpError as e:
        raise RuntimeError(
            f"Failed to upload image for {package_name} [{language}/{image_type}] from {file_path}: {e}"
        )


# ---------- App details (default language & support contacts) ----------

def details_get_impl(package_name: str) -> Dict[str, Any]:
    """Fetch app details (default language and support contacts)."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)
    try:
        return (
            svc.edits().details().get(packageName=package_name, editId=edit_id).execute()
        )
    finally:
        pass


def details_update_impl(
        package_name: str,
        *,
        default_language: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_website: Optional[str] = None,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Update app details. Only non-null fields are sent (PATCH-like behavior via `update`)."""
    svc = _publisher_service()
    edit_id = _begin_edit(svc, package_name)

    body: Dict[str, Any] = {}
    if default_language is not None:
        body["defaultLanguage"] = default_language
    if contact_email is not None:
        body["contactEmail"] = contact_email
    if contact_phone is not None:
        body["contactPhone"] = contact_phone
    if contact_website is not None:
        body["contactWebsite"] = contact_website

    try:
        # `update` replaces the whole object; sending partial fields is allowed by API semantics.
        resp = (
            svc.edits()
            .details()
            .update(packageName=package_name, editId=edit_id, body=body)
            .execute()
        )
        _commit_edit(svc, package_name, edit_id, changes_not_sent_for_review=changes_not_sent_for_review)
        return resp
    except HttpError as e:
        raise RuntimeError(f"Failed to update app details for {package_name}: {e}")
