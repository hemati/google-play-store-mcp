from __future__ import annotations

import csv
import io
import json
import os
import random
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Iterable

from .listings import (
    patch_listing_impl,
    images_deleteall_impl,
    images_upload_impl,
    list_localized_listings_impl,
)

# --------------------
# File persistence (simple JSON store)
# --------------------

EXPERIMENTS_DIR = os.environ.get("MCP_EXPERIMENTS_DIR", os.path.join(os.getcwd(), "experiments_store"))


def _ensure_dir():
    os.makedirs(EXPERIMENTS_DIR, exist_ok=True)


def _plan_path(plan_id: str) -> str:
    return os.path.join(EXPERIMENTS_DIR, f"{plan_id}.json")


# --------------------
# Data models (runtime dataclasses; Pydantic models are in models.py)
# --------------------

@dataclass
class VariantSpec:
    variant_id: str
    label: str
    # Text fields (send only those you want to modify)
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    video: Optional[str] = None
    # Asset plan (list of tuples): [(image_type, file_path), ...]
    assets: Optional[List[Tuple[str, str]]] = None


@dataclass
class ExperimentPlan:
    plan_id: str
    package_name: str
    language: str  # BCP-47 locale (e.g., "en-US")
    name: str
    hypothesis: Optional[str]
    metric: str  # e.g., "cvr" or "acquisitions"
    traffic_proportion: float  # 0..1 (Console supports configuring traffic split)
    type: str  # "text", "graphics", or "mixed"
    variants: List[VariantSpec]
    status: str  # "draft" | "running" | "stopped" | "applied" | "archived"
    created_at: float
    updated_at: float
    notes: Optional[str] = None

    # latest evaluation
    last_results: Optional[Dict[str, Any]] = None


# --------------------
# Utilities
# --------------------

def _save_plan(plan: ExperimentPlan) -> None:
    _ensure_dir()
    with open(_plan_path(plan.plan_id), "w", encoding="utf-8") as f:
        json.dump(asdict(plan), f, ensure_ascii=False, indent=2)


def _load_plan(plan_id: str) -> ExperimentPlan:
    with open(_plan_path(plan_id), "r", encoding="utf-8") as f:
        data = json.load(f)
    data["variants"] = [VariantSpec(**v) for v in data.get("variants", [])]
    return ExperimentPlan(**data)


def _list_plan_ids() -> List[str]:
    _ensure_dir()
    return [fn.split(".")[0] for fn in os.listdir(EXPERIMENTS_DIR) if fn.endswith(".json")]


# --------------------
# 0) Readiness guard (policy/language presence)
# --------------------

def guard_experiment_readiness_impl(package_name: str, language: str) -> Dict[str, Any]:
    """Check that target locale exists and current listing passes basic metadata lint rules."""
    listings = list_localized_listings_impl(package_name)
    langs = {li.get("language") for li in listings.get("listings", [])}
    locale_present = language in langs

    # Lint: we don't know the current listing text here; rely on caller to pass proposed strings
    # This guard just reports locale presence.
    return {
        "locale_present": locale_present,
        "present_locales": sorted(langs),
    }


# --------------------
# 1) Create/list/get/delete experiment plans
# --------------------

def experiments_create_plan_impl(
        package_name: str,
        language: str,
        name: str,
        hypothesis: Optional[str],
        metric: str,
        traffic_proportion: float,
        type: str,
        variants: List[Dict[str, Any]],
        notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a local experiment plan. This does **not** start a Console experiment."""
    plan = ExperimentPlan(
        plan_id=str(uuid.uuid4()),
        package_name=package_name,
        language=language,
        name=name,
        hypothesis=hypothesis,
        metric=metric,
        traffic_proportion=max(0.1, min(1.0, traffic_proportion or 1.0)),
        type=type,
        variants=[VariantSpec(variant_id=str(uuid.uuid4()), **v) for v in variants],
        status="draft",
        created_at=time.time(),
        updated_at=time.time(),
        notes=notes,
    )
    _save_plan(plan)
    return {"plan": asdict(plan)}


def experiments_list_plans_impl() -> Dict[str, Any]:
    ids = _list_plan_ids()
    plans = [asdict(_load_plan(pid)) for pid in ids]
    return {"plans": plans}


def experiments_get_plan_impl(plan_id: str) -> Dict[str, Any]:
    return {"plan": asdict(_load_plan(plan_id))}


def experiments_delete_plan_impl(plan_id: str) -> Dict[str, Any]:
    path = _plan_path(plan_id)
    if os.path.exists(path):
        os.remove(path)
        return {"deleted": True}
    return {"deleted": False}


# --------------------
# 2) Manual start helper (Console instructions)
# --------------------

def experiments_start_manual_impl(plan_id: str) -> Dict[str, Any]:
    """Return step-by-step Console instructions to start the experiment with the prepared variants.

    The Play Console randomizes traffic for you. We only orchestrate content & later promotion.
    """
    plan = _load_plan(plan_id)
    plan.status = "running"
    plan.updated_at = time.time()
    _save_plan(plan)

    # Human-friendly instructions to mirror the plan in Console
    steps = [
        "Open Google Play Console → Select app",
        "Store presence → Store listing → Experiments",
        f"Create new experiment: {plan.type} | Locale: {plan.language} | Traffic: {int(plan.traffic_proportion * 100)}%",
        f"Name: {plan.name}",
        "Add variants and paste the following fields per variant:",
    ]

    vrows = []
    for v in plan.variants:
        vrows.append({
            "variant_id": v.variant_id,
            "label": v.label,
            "title": v.title,
            "short_description": v.short_description,
            "full_description": v.full_description,
            "video": v.video,
            "assets": v.assets,
        })

    return {
        "plan_id": plan.plan_id,
        "status": plan.status,
        "instructions": steps,
        "variants": vrows,
        "note": "Once the Console declares a winner, use experiments_apply_winner to promote.",
    }


# --------------------
# 3) Significance calculation (Bayesian best-of probability)
# --------------------

def _bayes_best_probability(metrics: Dict[str, Dict[str, int]], samples: int = 20000) -> Dict[str, Any]:
    """Compute P(variant is best) with Beta(1,1) priors.

    metrics = {variant_id: {"visitors": int, "conversions": int}}
    """
    variant_ids = list(metrics.keys())
    post = {}
    for vid, m in metrics.items():
        a = 1 + int(m.get("conversions", 0))
        b = 1 + int(m.get("visitors", 0)) - int(m.get("conversions", 0))
        post[vid] = (a, b)

    wins = {vid: 0 for vid in variant_ids}
    for _ in range(samples):
        draws = {vid: random.betavariate(a, b) for vid, (a, b) in post.items()}
        best = max(draws.items(), key=lambda kv: kv[1])[0]
        wins[best] += 1

    probs = {vid: wins[vid] / samples for vid in variant_ids}
    lifts = {}
    # compute expected rates
    means = {vid: (post[vid][0]) / (post[vid][0] + post[vid][1]) for vid in variant_ids}
    baseline = variant_ids[0]
    for vid in variant_ids:
        if means[baseline] == 0:
            lifts[vid] = None
        else:
            lifts[vid] = (means[vid] / means[baseline]) - 1.0

    winner = max(probs.items(), key=lambda kv: kv[1])[0]

    return {
        "winner": winner,
        "winner_probability": probs[winner],
        "probabilities": probs,
        "mean_rates": means,
        "relative_lift_vs_baseline": lifts,
    }


def experiments_compute_significance_impl(plan_id: str, metrics: Dict[str, Dict[str, int]], samples: int = 20000) -> \
Dict[str, Any]:
    """Given variant metrics, compute winner probability & lifts.

    metrics example:
        {
          "<variant_id_A>": {"visitors": 10000, "conversions": 1234},
          "<variant_id_B>": {"visitors": 9800, "conversions": 1400}
        }
    """
    plan = _load_plan(plan_id)
    res = _bayes_best_probability(metrics, samples=samples)

    # Recommendation thresholds (tunable):
    action = "continue"
    if res["winner_probability"] >= 0.95:
        action = "promote_winner"
    elif any(m.get("visitors", 0) < 1000 for m in metrics.values()):
        action = "collect_more_data"

    plan.last_results = {
        "metrics": metrics,
        "bayes": res,
        "recommendation": action,
        "evaluated_at": time.time(),
    }
    _save_plan(plan)

    return {
        "plan_id": plan.plan_id,
        "result": plan.last_results,
    }


# --------------------
# 4) Apply winner (promote variant content to live listing)
# --------------------

def experiments_apply_winner_impl(
        plan_id: str,
        variant_id: str,
        *,
        changes_not_sent_for_review: bool = False,
) -> Dict[str, Any]:
    """Promote a winning variant by applying its text + assets to the live listing for the locale."""
    plan = _load_plan(plan_id)
    variant = next((v for v in plan.variants if v.variant_id == variant_id), None)
    assert variant is not None, f"Unknown variant_id: {variant_id}"

    # 1) Update text (only provided fields)
    patch_resp = patch_listing_impl(
        package_name=plan.package_name,
        language=plan.language,
        title=variant.title,
        short_description=variant.short_description,
        full_description=variant.full_description,
        video=variant.video,
        changes_not_sent_for_review=changes_not_sent_for_review,
    )

    # 2) Update assets
    uploads: List[Dict[str, Any]] = []
    if variant.assets:
        # We clear and re-upload per image_type
        by_type: Dict[str, List[str]] = {}
        for (image_type, file_path) in (variant.assets or []):
            by_type.setdefault(image_type, []).append(file_path)
        for image_type, files in by_type.items():
            images_deleteall_impl(
                package_name=plan.package_name,
                language=plan.language,
                image_type=image_type,
                changes_not_sent_for_review=changes_not_sent_for_review,
            )
            for fp in files:
                up = images_upload_impl(
                    package_name=plan.package_name,
                    language=plan.language,
                    image_type=image_type,
                    file_path=fp,
                    changes_not_sent_for_review=changes_not_sent_for_review,
                )
                uploads.append(up)

    plan.status = "applied"
    plan.updated_at = time.time()
    _save_plan(plan)

    return {
        "plan_id": plan.plan_id,
        "applied_variant": variant.variant_id,
        "text_patch": patch_resp,
        "asset_uploads": uploads,
        "status": plan.status,
    }


# --------------------
# 5) Stop/archive a plan (no content change)
# --------------------

def experiments_stop_impl(plan_id: str) -> Dict[str, Any]:
    plan = _load_plan(plan_id)
    plan.status = "stopped"
    plan.updated_at = time.time()
    _save_plan(plan)
    return {"plan_id": plan.plan_id, "status": plan.status}


# --------------------
# Helpers for GCS CSV ingestion
# --------------------

def _list_gcs_objects(bucket: str, prefix: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
    """List object names under a prefix; optionally filter by YYYY-MM date window in the object name."""
    client = storage.Client()
    blobs = client.list_blobs(bucket, prefix=prefix)
    out: List[str] = []
    for b in blobs:
        name = b.name
        if start_date or end_date:
            # naive filter if filenames contain dates like YYYYMM or YYYY-MM
            ymd = "".join(ch for ch in name if ch.isdigit())
            # Keep everything if we cannot parse
            if len(ymd) >= 6 and (start_date or end_date):
                ym = ymd[:6]
                if start_date and ym < start_date.replace("-", "")[:6]:
                    continue
                if end_date and ym > end_date.replace("-", "")[:6]:
                    continue
        out.append(name)
    return out


def _read_gcs_csv(bucket: str, object_name: str) -> Iterable[Dict[str, str]]:
    client = storage.Client()
    blob = client.bucket(bucket).blob(object_name)
    data = blob.download_as_bytes()
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


# --------------------
# Flexible schema accessors (column names differ across exports)
# --------------------

CANDIDATE_DATE = ["date", "Date", "day", "Day"]
CANDIDATE_LANGUAGE = ["language", "Language", "dimension_language"]
CANDIDATE_COUNTRY = ["country", "Country", "dimension_country"]
CANDIDATE_LISTING = ["store_listing", "Store listing", "dimension_store_listing", "listing"]
CANDIDATE_VISITORS = ["store_listing_visitors", "Store listing visitors", "visitors"]
CANDIDATE_ACQ = ["store_listing_acquisitions", "Store listing acquisitions", "acquisitions"]


def _pick(row: Dict[str, str], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in row:
            return row[k]
    return None


# --------------------
# Aggregation core
# --------------------

@dataclass
class DailyPoint:
    date: dt.date
    visitors: int
    acquisitions: int


def _parse_date(s: str) -> dt.date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    raise ValueError(f"Unsupported date format: {s}")


def _collect_timeseries(
    bucket: str,
    objects: List[str],
    *,
    language: Optional[str] = None,
    store_listing: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[dt.date, DailyPoint]:
    series: Dict[dt.date, DailyPoint] = {}
    for obj in objects:
        for row in _read_gcs_csv(bucket, obj):
            d = _pick(row, CANDIDATE_DATE)
            if not d:
                continue
            try:
                day = _parse_date(d)
            except Exception:
                continue
            lang = (_pick(row, CANDIDATE_LANGUAGE) or "").strip()
            if language and lang and lang.lower() != language.lower():
                continue
            lst = (_pick(row, CANDIDATE_LISTING) or "").strip()
            if store_listing and lst and lst.lower() != store_listing.lower():
                continue
            ctry = (_pick(row, CANDIDATE_COUNTRY) or "").strip()
            if country and ctry and ctry.lower() != country.lower():
                continue
            vis = int(float((_pick(row, CANDIDATE_VISITORS) or "0") or 0))
            acq = int(float((_pick(row, CANDIDATE_ACQ) or "0") or 0))
            if day in series:
                # Sum duplicates across files
                p = series[day]
                series[day] = DailyPoint(day, p.visitors + vis, p.acquisitions + acq)
            else:
                series[day] = DailyPoint(day, vis, acq)
    return series


# --------------------
# Trends computation per experiment plan
# --------------------

def _window_stats(series: Dict[dt.date, DailyPoint], start: dt.date, end: dt.date) -> Dict[str, Any]:
    visitors = 0
    acquisitions = 0
    for t, p in series.items():
        if start <= t <= end:
            visitors += p.visitors
            acquisitions += p.acquisitions
    cvr = (acquisitions / visitors) if visitors > 0 else 0.0
    return {"visitors": visitors, "acquisitions": acquisitions, "cvr": cvr}


def experiments_trends_report_impl(
    *,
    bucket: str,
    prefix: str,
    plan_ids: Optional[List[str]] = None,
    store_listing: Optional[str] = None,
    country: Optional[str] = None,
    default_window_days: int = 7,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_visitors: int = 100,
) -> Dict[str, Any]:
    """Compute trends across past experiments using acquisition exports from GCS.

    For each plan, we derive three windows (if possible):
      - baseline: days immediately before the experiment (same length as test window)
      - during: from plan.created_at to plan.updated_at (if status in {applied, stopped}); else `default_window_days`
      - post: days immediately after the experiment (same length as test window)

    The function aggregates visitors, acquisitions, and CVR per window, then produces
    a summary across all selected plans, grouped by test type and language.
    """
    # Resolve plans
    selected = plan_ids or _list_plan_ids()
    plans = []
    for pid in selected:
        try:
            plans.append(_load_plan(pid))
        except Exception:
            continue
    # List & fetch objects once
    objects = _list_gcs_objects(bucket, prefix, start_date, end_date)

    results: List[Dict[str, Any]] = []
    by_type: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_lang: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)

    for plan in plans:
        # Determine window
        start_ts = int(plan.created_at)
        end_ts = int(plan.updated_at) if plan.status in ("applied", "stopped") else (start_ts + default_window_days * 86400)
        start_day = dt.date.fromtimestamp(start_ts)
        end_day = dt.date.fromtimestamp(end_ts)
        window_len = max(1, (end_day - start_day).days + 1)

        # Series filtered by language/store_listing/country
        series = _collect_timeseries(
            bucket,
            objects,
            language=plan.language,
            store_listing=store_listing,
            country=country,
        )

        baseline_start = start_day - dt.timedelta(days=window_len)
        baseline_end = start_day - dt.timedelta(days=1)
        post_start = end_day + dt.timedelta(days=1)
        post_end = end_day + dt.timedelta(days=window_len)

        baseline = _window_stats(series, baseline_start, baseline_end)
        during = _window_stats(series, start_day, end_day)
        post = _window_stats(series, post_start, post_end)

        entry = {
            "plan_id": plan.plan_id,
            "name": plan.name,
            "language": plan.language,
            "type": plan.type,
            "status": plan.status,
            "hypothesis": plan.hypothesis,
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
            "window_days": window_len,
            "baseline": baseline,
            "during": during,
            "post": post,
            "delta_cvr_vs_baseline": (during["cvr"] - baseline["cvr"]),
            "delta_cvr_post_vs_during": (post["cvr"] - during["cvr"]),
        }
        # Filter out very low-traffic experiments if desired
        if during["visitors"] >= min_visitors:
            results.append(entry)
            by_type[plan.type].append(entry)
            by_lang[plan.language].append(entry)

    def _agg(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not entries:
            return {"count": 0}
        def _sum(path: Tuple[str, ...]) -> float:
            s = 0.0
            for e in entries:
                ref = e
                for p in path:
                    ref = ref[p]
                s += float(ref)
            return s
        total_visitors = _sum(("during", "visitors"))
        total_acq = _sum(("during", "acquisitions"))
        total_cvr = (total_acq / total_visitors) if total_visitors > 0 else 0.0
        avg_lift = sum(e["delta_cvr_vs_baseline"] for e in entries) / len(entries)
        return {
            "count": len(entries),
            "total_visitors": int(total_visitors),
            "total_acquisitions": int(total_acq),
            "pooled_cvr": total_cvr,
            "avg_delta_cvr_vs_baseline": avg_lift,
        }

    summary_by_type = {k: _agg(v) for k, v in by_type.items()}
    summary_by_lang = {k: _agg(v) for k, v in by_lang.items()}

    return {
        "plans_considered": [p.plan_id for p in plans],
        "results": results,
        "summary_by_type": summary_by_type,
        "summary_by_language": summary_by_lang,
    }