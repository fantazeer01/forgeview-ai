"""Wallet copyability feasibility research sprint.

This module runs bounded public-data research only. It does not connect
wallets, use private keys, place orders, copy trades, monitor live activity,
compute profitability, or make trading recommendations.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .client import PolymarketPublicClient
from .lifecycle import run_lifecycle_fixture_reconstruction
from .lifecycle_metrics import run_lifecycle_metrics
from .schema import WATCHED_WALLETS_FIELDS, WatchedWallet
from .trade_history import (
    _payload_rows,
    canonical_json,
    classify_trade_market,
    file_sha256,
    normalize_fixture_pages,
    summarize_trade_records,
    validation_gate_results,
    write_csv,
    write_raw_jsonl,
)
from .wallet_score import run_wallet_score_fixture
from .wallet_watchlist import run_wallet_watchlist


DEFAULT_SEED_WALLETS = Path("polymarket/wallet_intelligence/watched_wallets.example.csv")
DEFAULT_BROADER_WALLETS = Path("polymarket/wallet_intelligence/watched_wallets_broader_v1.example.csv")
DEFAULT_WALLET_PROFILES = Path("polymarket/data/wallet_intelligence/v1/wallet_profiles.csv")
DEFAULT_TRADE_OUTPUT = Path("polymarket/data/wallet_intelligence/trade_history_broader_v1")
DEFAULT_LIFECYCLE_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1")
DEFAULT_METRICS_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1")
DEFAULT_SCORE_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1")
DEFAULT_WATCHLIST_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_watchlist_broader_v1")
DEFAULT_COPYABILITY_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1")

SPRINT_VERSION = "wallet_copyability_feasibility_sprint_v1"
MAX_WALLETS = 30
MAX_PRIMARY_PAGES_PER_WALLET = 2
PRIMARY_PAGE_SIZE = 100
MAX_PRIMARY_ROWS_PER_WALLET = 200
MAX_PRIMARY_ROWS_TOTAL = 6000
MAX_CROSS_CHECK_PAGES_PER_WALLET = 1
CROSS_CHECK_PAGE_SIZE = 100
MAX_CROSS_CHECK_ROWS_TOTAL = 3000
DISCOVERY_TRADE_ROWS = 250

COPYABILITY_FIELDS = [
    "wallet_id",
    "profile_url",
    "score",
    "priority_bucket",
    "watchlist_inclusion",
    "reason_codes",
    "structural_strengths",
    "structural_weaknesses",
    "confidence_level",
    "missing_evidence",
    "recommendation",
    "observed",
    "unknown",
]

FORBIDDEN_FRAGMENTS = (
    "pnl",
    "roi",
    "sharpe",
    "profit",
    "alpha",
    "expected_return",
    "investment_advice",
    "trade_recommendation",
)

FORBIDDEN_CLAIM_PHRASES = (
    "profitable wallet",
    "expected return",
    "copyability success",
    "trade recommendation",
    "investment advice",
    "proven edge",
    "proven alpha",
)


def run_wallet_copyability_sprint(
    *,
    client: PolymarketPublicClient | None = None,
    seed_wallets_path: Path = DEFAULT_SEED_WALLETS,
    broader_wallets_path: Path = DEFAULT_BROADER_WALLETS,
    trade_output_dir: Path = DEFAULT_TRADE_OUTPUT,
    lifecycle_output_dir: Path = DEFAULT_LIFECYCLE_OUTPUT,
    metrics_output_dir: Path = DEFAULT_METRICS_OUTPUT,
    score_output_dir: Path = DEFAULT_SCORE_OUTPUT,
    watchlist_output_dir: Path = DEFAULT_WATCHLIST_OUTPUT,
    copyability_output_dir: Path = DEFAULT_COPYABILITY_OUTPUT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    client = client or PolymarketPublicClient(delay_seconds=0.5, timeout_seconds=20)
    copyability_output_dir.mkdir(parents=True, exist_ok=True)

    wallets, discovery_summary = load_or_discover_wallets(
        client=client,
        seed_wallets_path=seed_wallets_path,
        broader_wallets_path=broader_wallets_path,
        generated_at=generated_at,
    )
    ingestion_summary = ingest_broader_trade_history(
        client=client,
        wallets=wallets,
        output_dir=trade_output_dir,
        generated_at=generated_at,
    )
    lifecycle_summary = run_lifecycle_fixture_reconstruction(
        trade_output_dir / "trade_history_normalized.csv",
        lifecycle_output_dir,
        generated_at=generated_at,
    )
    metrics_summary = run_lifecycle_metrics(
        lifecycle_output_dir / "lifecycle_positions.csv",
        metrics_output_dir,
        generated_at=generated_at,
    )
    score_summary = run_wallet_score_fixture(
        metrics_output_dir / "wallet_metrics.csv",
        score_output_dir,
        generated_at=generated_at,
    )
    watchlist_summary = run_wallet_watchlist(
        score_output_dir / "wallet_scores.csv",
        watchlist_output_dir,
        generated_at=generated_at,
    )

    research_rows, summary = build_copyability_research(
        scores_path=score_output_dir / "wallet_scores.csv",
        watchlist_path=watchlist_output_dir / "wallet_watchlist.csv",
        metrics_path=metrics_output_dir / "wallet_metrics.csv",
        ingestion_summary=ingestion_summary,
        discovery_summary=discovery_summary,
        generated_at=generated_at,
    )
    summary.update(
        {
            "pipeline_outputs": {
                "trade_history": str(trade_output_dir),
                "lifecycle_reconstruction": str(lifecycle_output_dir),
                "lifecycle_metrics": str(metrics_output_dir),
                "wallet_score": str(score_output_dir),
                "wallet_watchlist": str(watchlist_output_dir),
                "copyability_research": str(copyability_output_dir),
            },
            "pipeline_summaries": {
                "ingestion": _compact_ingestion_summary(ingestion_summary),
                "lifecycle": {
                    "input_rows": lifecycle_summary.get("input_rows"),
                    "lifecycle_positions": lifecycle_summary.get("lifecycle_positions"),
                    "status_counts": lifecycle_summary.get("status_counts"),
                    "validation": lifecycle_summary.get("validation"),
                },
                "metrics": {
                    "wallets_analyzed": metrics_summary.get("wallets_analyzed"),
                    "aggregate": metrics_summary.get("aggregate"),
                    "validation": metrics_summary.get("validation"),
                },
                "score": {
                    "wallets_scored": score_summary.get("wallets_scored"),
                    "score_band_counts": score_summary.get("score_band_counts"),
                    "validation": score_summary.get("validation"),
                },
                "watchlist": {
                    "wallets_included": watchlist_summary.get("wallets_included"),
                    "priority_bucket_counts": watchlist_summary.get("priority_bucket_counts"),
                    "validation": watchlist_summary.get("validation"),
                },
            },
        }
    )
    write_copyability_outputs(copyability_output_dir, research_rows, summary)
    return summary


def load_or_discover_wallets(
    *,
    client: PolymarketPublicClient,
    seed_wallets_path: Path,
    broader_wallets_path: Path,
    generated_at: str,
) -> tuple[list[WatchedWallet], dict[str, Any]]:
    if broader_wallets_path.exists():
        wallets = _read_wallet_manifest(broader_wallets_path)
        return wallets[:MAX_WALLETS], {
            "wallet_source": str(broader_wallets_path),
            "wallets_selected": min(len(wallets), MAX_WALLETS),
            "discovery_rows_read": 0,
            "discovery_endpoint": "",
            "selection_note": "existing broader wallet manifest reused",
        }

    seeds = _read_wallet_manifest(seed_wallets_path)
    profile_resolution = _profile_resolution_map(DEFAULT_WALLET_PROFILES)
    selected: dict[str, WatchedWallet] = {}
    for seed in seeds:
        wallet_id = profile_resolution.get(seed.profile_url, _normalize_wallet_id(seed.wallet_id, seed.profile_url))
        selected[wallet_id] = WatchedWallet(
            wallet_id=wallet_id,
            profile_url=seed.profile_url,
            label=seed.label or "seed_wallet",
            source="existing_seed",
            notes=seed.notes or "existing seed wallet",
        )

    response = client.get_json("/trades", {"limit": DISCOVERY_TRADE_ROWS, "offset": 0})
    rows = _payload_rows(response.payload)
    candidates: list[tuple[int, str, WatchedWallet]] = []
    for row in rows:
        wallet = str(row.get("proxyWallet") or "").lower()
        if not wallet.startswith("0x") or len(wallet) != 42 or wallet in selected:
            continue
        title = str(row.get("title") or "")
        slug = str(row.get("slug") or "")
        market_type, asset_class, up_down = classify_trade_market(title, slug)
        if up_down:
            priority = 0
            reason = f"fast_crypto_candidate:{asset_class}"
        elif market_type in {"crypto_other", "weather"}:
            priority = 1
            reason = f"mixed_control:{market_type}"
        else:
            priority = 2
            reason = "public_trade_control"
        candidates.append(
            (
                priority,
                wallet,
                WatchedWallet(
                    wallet_id=wallet,
                    profile_url=f"https://polymarket.com/{wallet}",
                    label="broader_public_candidate",
                    source="polymarket_public_trades_bounded_discovery",
                    notes=reason,
                ),
            )
        )

    for _, wallet, candidate in sorted(candidates, key=lambda item: (item[0], item[1])):
        if len(selected) >= MAX_WALLETS:
            break
        selected.setdefault(wallet, candidate)

    wallets = list(selected.values())[:MAX_WALLETS]
    _write_wallet_manifest(broader_wallets_path, wallets)
    return wallets, {
        "wallet_source": str(broader_wallets_path),
        "wallets_selected": len(wallets),
        "discovery_rows_read": len(rows),
        "discovery_endpoint": response.url,
        "selection_note": "seed wallets plus bounded public /trades discovery; no private or authenticated data",
        "generated_at_utc": generated_at,
    }


def ingest_broader_trade_history(
    *,
    client: PolymarketPublicClient,
    wallets: list[WatchedWallet],
    output_dir: Path,
    generated_at: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    primary_pages: list[dict[str, Any]] = []
    cross_check_pages: list[dict[str, Any]] = []
    endpoint_errors: dict[str, list[str]] = {}
    for wallet in wallets[:MAX_WALLETS]:
        wallet_id = _normalize_wallet_id(wallet.wallet_id, wallet.profile_url)
        for page_index in range(MAX_PRIMARY_PAGES_PER_WALLET):
            offset = page_index * PRIMARY_PAGE_SIZE
            fetched_at = datetime.now(UTC).replace(microsecond=0).isoformat()
            try:
                response = client.activity_trades(wallet_id, limit=PRIMARY_PAGE_SIZE, offset=offset)
                rows = _payload_rows(response.payload)
                primary_pages.append(
                    {
                        "wallet_id": wallet_id,
                        "profile_url": wallet.profile_url,
                        "source_endpoint": response.url,
                        "source_endpoint_name": "activity_primary",
                        "source_fetch_timestamp": fetched_at,
                        "page_index": page_index,
                        "limit": PRIMARY_PAGE_SIZE,
                        "offset": offset,
                        "rows": rows,
                    }
                )
            except Exception as exc:  # pragma: no cover - network-specific
                endpoint_errors.setdefault(wallet_id, []).append(f"activity:{type(exc).__name__}:{exc}")
        fetched_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        try:
            response = client.get_json("/trades", {"user": wallet_id, "limit": CROSS_CHECK_PAGE_SIZE, "offset": 0})
            cross_check_pages.append(
                {
                    "wallet_id": wallet_id,
                    "profile_url": wallet.profile_url,
                    "source_endpoint": response.url,
                    "source_endpoint_name": "trades_cross_check",
                    "source_fetch_timestamp": fetched_at,
                    "page_index": 0,
                    "limit": CROSS_CHECK_PAGE_SIZE,
                    "offset": 0,
                    "rows": _payload_rows(response.payload),
                }
            )
        except Exception as exc:  # pragma: no cover - network-specific
            endpoint_errors.setdefault(wallet_id, []).append(f"trades:{type(exc).__name__}:{exc}")

    records, metadata = normalize_fixture_pages(primary_pages)
    raw_pages = primary_pages + cross_check_pages
    limit_violations = _broader_limit_violations(wallets, metadata, cross_check_pages)

    raw_path = output_dir / "trade_history_raw.jsonl"
    cross_path = output_dir / "trade_history_cross_check_raw.jsonl"
    csv_path = output_dir / "trade_history_normalized.csv"
    summary_path = output_dir / "trade_history_summary.json"
    report_json_path = output_dir / "broader_ingestion_report.json"
    report_md_path = output_dir / "broader_ingestion_report.md"
    gate_path = output_dir / "validation_gate_results.json"
    hash_path = output_dir / "reproducibility_hashes.json"

    write_raw_jsonl(raw_path, raw_pages)
    write_raw_jsonl(cross_path, cross_check_pages)
    write_csv(csv_path, records)
    first_hash = file_sha256(csv_path)
    write_csv(csv_path, records)
    second_hash = file_sha256(csv_path)
    deterministic = first_hash == second_hash

    gates = validation_gate_results(
        records,
        duplicate_rows_removed=int(metadata["duplicate_rows_removed"]),
        limit_violations=limit_violations,
        deterministic_export=deterministic,
    )
    gates["cross_check_bounded_scope"] = {
        "passed": _cross_check_rows(cross_check_pages) <= MAX_CROSS_CHECK_ROWS_TOTAL,
        "cross_check_rows": _cross_check_rows(cross_check_pages),
        "cross_check_pages": len(cross_check_pages),
    }
    gates["all_validation_passed"] = all(value.get("passed") for value in gates.values() if isinstance(value, dict))
    row_summary = summarize_trade_records(records)
    summary = {
        "task": "Wallet Public Trade History Broader Evidence v1",
        "generated_at_utc": generated_at,
        "output_dir": str(output_dir),
        "wallets_attempted": len(wallets),
        "wallets_with_primary_pages": len({page["wallet_id"] for page in primary_pages}),
        "wallets_with_primary_rows": len([wallet for wallet, count in metadata["rows_by_wallet"].items() if count > 0]),
        "primary_pages_fetched": len(primary_pages),
        "primary_rows_fetched": metadata["input_rows"],
        "primary_rows_normalized": metadata["normalized_rows"],
        "cross_check_pages_fetched": len(cross_check_pages),
        "cross_check_rows_fetched": _cross_check_rows(cross_check_pages),
        "duplicate_rows_removed": metadata["duplicate_rows_removed"],
        "rows_by_wallet": metadata["rows_by_wallet"],
        "pages_by_wallet": metadata["pages_by_wallet"],
        "endpoint_errors": endpoint_errors,
        "limits": {
            "max_wallets": MAX_WALLETS,
            "max_primary_pages_per_wallet": MAX_PRIMARY_PAGES_PER_WALLET,
            "max_primary_rows_per_wallet": MAX_PRIMARY_ROWS_PER_WALLET,
            "max_primary_rows_total": MAX_PRIMARY_ROWS_TOTAL,
            "max_cross_check_pages_per_wallet": MAX_CROSS_CHECK_PAGES_PER_WALLET,
            "max_cross_check_rows_total": MAX_CROSS_CHECK_ROWS_TOTAL,
        },
        "row_summary": row_summary,
        "validation_gates": gates,
        "validation_gates_passed": gates["all_validation_passed"],
        "fields_unavailable": _missing_evidence_layers(),
        "strict_rules_observed": [
            "public read-only Data API activity and trades endpoints",
            "bounded wallet sample",
            "bounded primary activity pages",
            "bounded trades cross-check pages",
            "no wallet/private-key connection",
            "no order placement",
            "no automatic trade copying",
            "no live monitoring",
            "no capture campaign",
            "no holdout inspection",
            "no holdout evaluation",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    gate_path.write_text(json.dumps(gates, indent=2, sort_keys=True), encoding="utf-8")
    hashes = {
        "trade_history_raw_jsonl_sha256": file_sha256(raw_path),
        "trade_history_cross_check_raw_jsonl_sha256": file_sha256(cross_path),
        "trade_history_normalized_csv_sha256": file_sha256(csv_path),
        "trade_history_summary_json_sha256": file_sha256(summary_path),
        "broader_ingestion_report_json_sha256": file_sha256(report_json_path),
        "validation_gate_results_json_sha256": file_sha256(gate_path),
        "csv_repeat_export_hash_match": deterministic,
    }
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    report_md_path.write_text(_build_ingestion_report(summary, hashes), encoding="utf-8")
    return summary


def build_copyability_research(
    *,
    scores_path: Path,
    watchlist_path: Path,
    metrics_path: Path,
    ingestion_summary: dict[str, Any],
    discovery_summary: dict[str, Any],
    generated_at: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    scores = _read_csv(scores_path)
    watchlist = {row["wallet_id"]: row for row in _read_csv(watchlist_path)}
    metrics = {row["wallet_id"]: row for row in _read_csv(metrics_path)}
    rows: list[dict[str, str]] = []
    for score in scores:
        wallet_id = score["wallet_id"]
        metric = metrics.get(wallet_id, {})
        watch = watchlist.get(wallet_id)
        row = _copyability_row(score, metric, watch, ingestion_summary)
        rows.append(row)
    rows = sorted(rows, key=lambda row: (_recommendation_order(row["recommendation"]), -_decimal(row["score"]), row["wallet_id"]))
    validation = validate_copyability_research(rows)
    analysis = analyze_copyability_rows(rows, scores)
    summary = {
        "task": "Wallet Copyability Feasibility Sprint v1",
        "sprint_version": SPRINT_VERSION,
        "generated_at_utc": generated_at,
        "master_question": "Can publicly observable Polymarket wallet activity contain enough information to identify wallets worth monitoring for future copy-trading research?",
        "wallet_count": len(rows),
        "evidence_size": {
            "wallets_selected": discovery_summary.get("wallets_selected"),
            "primary_rows_normalized": ingestion_summary.get("primary_rows_normalized"),
            "cross_check_rows_fetched": ingestion_summary.get("cross_check_rows_fetched"),
            "lifecycle_rows_input_to_score": len(scores),
        },
        "classification_counts": dict(sorted(Counter(row["recommendation"] for row in rows).items())),
        "priority_bucket_counts": dict(sorted(Counter(row["priority_bucket"] for row in rows).items())),
        "confidence_counts": dict(sorted(Counter(row["confidence_level"] for row in rows).items())),
        "validation": validation,
        "analysis": analysis,
        "observed_vs_unknown": {
            "observed": [
                "public activity/trade rows",
                "normalized trade fields",
                "visible lifecycle structure",
                "visible BUY/SELL side counts",
                "fast-crypto exposure",
                "structural Wallet Score components",
                "watchlist inclusion reason codes",
            ],
            "unknown": _missing_evidence_layers(),
        },
        "forbidden_claims": [
            "no performance claim",
            "no market-advantage claim",
            "no copy outcome claim",
            "no return claim",
            "no trading instruction",
            "no financial advice",
        ],
        "research_conclusion": _research_conclusion(rows, analysis),
        "recommended_next_sprint": "Wallet Expiry And Outcome Join Feasibility Sprint v1",
    }
    return rows, summary


def validate_copyability_research(rows: list[dict[str, str]]) -> dict[str, Any]:
    deterministic_order = rows == sorted(rows, key=lambda row: (_recommendation_order(row["recommendation"]), -_decimal(row["score"]), row["wallet_id"]))
    schema_complete = all(set(row.keys()) == set(COPYABILITY_FIELDS) for row in rows)
    reason_codes = all(bool(row["reason_codes"]) and row["reason_codes"] != "none" for row in rows)
    classified = all(row["recommendation"] in {"monitor_candidate", "needs_more_history", "insufficient_signal", "exclude_for_now"} for row in rows)
    forbidden_fields = [
        field
        for field in COPYABILITY_FIELDS
        for fragment in FORBIDDEN_FRAGMENTS
        if fragment in field.lower()
    ]
    content = "\n".join(canonical_json(row).lower() for row in rows)
    forbidden_claims = [phrase for phrase in FORBIDDEN_CLAIM_PHRASES if phrase in content]
    return {
        "deterministic_ordering": deterministic_order,
        "output_schema_completeness": schema_complete,
        "every_wallet_classified": classified,
        "reason_codes_present": reason_codes,
        "no_forbidden_metric_fields": not forbidden_fields,
        "forbidden_metric_fields": forbidden_fields,
        "no_forbidden_claims": not forbidden_claims,
        "forbidden_claim_phrases": forbidden_claims,
        "all_validation_passed": deterministic_order and schema_complete and classified and reason_codes and not forbidden_fields and not forbidden_claims,
    }


def analyze_copyability_rows(rows: list[dict[str, str]], scores: list[dict[str, str]]) -> dict[str, Any]:
    bands = Counter(row["priority_bucket"] for row in rows)
    recommendations = Counter(row["recommendation"] for row in rows)
    component_names = [
        "coverage_component",
        "fast_crypto_component",
        "lifecycle_activity_component",
        "event_density_component",
        "specialization_component",
    ]
    penalty_names = [
        "bounded_history_penalty",
        "still_open_penalty",
        "small_sample_penalty",
        "concentration_penalty",
        "near_flat_ambiguity_penalty",
    ]
    component_ranges = {
        name: _range([_decimal(row.get(name)) for row in scores])
        for name in component_names + penalty_names
    }
    strongest_influence = sorted(component_ranges.items(), key=lambda item: (-item[1]["range"], item[0]))
    weak_raw = [
        row["wallet_id"]
        for row in scores
        if row.get("score_band") in {"medium_priority", "high_priority"}
        and (_decimal(row.get("total_lifecycle_positions")) < Decimal("10") or _decimal(row.get("percentage_still_open_positions")) >= Decimal("0.9"))
    ]
    return {
        "A_monitor_candidate_count": recommendations.get("monitor_candidate", 0),
        "B_exclude_for_now_count": recommendations.get("exclude_for_now", 0),
        "C_score_separation": _score_separation_statement(bands),
        "D_most_influential_metrics": [name for name, _ in strongest_influence[:5]],
        "D_component_ranges": component_ranges,
        "E_almost_useless_metrics": [
            name
            for name, data in component_ranges.items()
            if data["range"] == 0
        ],
        "F_interesting_despite_weak_raw_evidence": weak_raw,
        "G_largest_remaining_blockers": _missing_evidence_layers(),
        "observed": "bounded public trade history separates wallets structurally by visible lifecycle coverage, fast-crypto share, partial exits, still-open share, concentration, and bounded-history artifacts",
        "unknown": "realized outcomes, expiry behavior, observation delay, fill/slippage feasibility, liquidity, and full history remain unknown",
    }


def write_copyability_outputs(output_dir: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "wallet_copyability_research.csv"
    summary_path = output_dir / "wallet_copyability_summary.json"
    report_path = output_dir / "wallet_copyability_report.md"
    _write_csv_rows(csv_path, rows, COPYABILITY_FIELDS)
    first_hash = file_sha256(csv_path)
    _write_csv_rows(csv_path, rows, COPYABILITY_FIELDS)
    second_hash = file_sha256(csv_path)
    summary["validation"]["repeatable_export"] = first_hash == second_hash
    bools = [value for value in summary["validation"].values() if isinstance(value, bool)]
    summary["validation"]["all_validation_passed"] = all(bools)
    summary["reproducibility_hashes"] = {
        "wallet_copyability_research_csv_sha256": file_sha256(csv_path),
        "csv_repeat_export_hash_match": first_hash == second_hash,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    summary["reproducibility_hashes"]["wallet_copyability_summary_json_sha256"] = file_sha256(summary_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(_build_copyability_report(summary, rows), encoding="utf-8")
    summary["reproducibility_hashes"]["wallet_copyability_report_md_sha256"] = file_sha256(report_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def _copyability_row(score: dict[str, str], metric: dict[str, str], watch: dict[str, str] | None, ingestion_summary: dict[str, Any]) -> dict[str, str]:
    wallet_id = score["wallet_id"]
    score_value = _decimal(score.get("wallet_score"))
    positions = _int(score.get("total_lifecycle_positions"))
    fast_share = _decimal(score.get("fast_crypto_lifecycle_share"))
    still_open = _decimal(score.get("percentage_still_open_positions"))
    oversold = _int(score.get("oversold_bounded_history"))
    partial = _int(score.get("partial_exits"))
    priority = score.get("score_band") or ""
    inclusion = "included" if watch else "excluded_minimum_visibility"
    reason_codes = watch.get("reason_codes") if watch else "minimum_visibility_failed"
    strengths = watch.get("structural_strengths") if watch else _fallback_strengths(score)
    risks = watch.get("structural_risks") if watch else _fallback_risks(score)
    recommendation = _recommendation(score, watch)
    confidence = _confidence(positions, fast_share, still_open, oversold)
    observed = [
        f"visible_lifecycle_positions={positions}",
        f"fast_crypto_share={score.get('fast_crypto_lifecycle_share')}",
        f"partial_exits={partial}",
        f"priority_bucket={priority}",
    ]
    if wallet_id in ingestion_summary.get("rows_by_wallet", {}):
        observed.append(f"normalized_trade_rows={ingestion_summary['rows_by_wallet'][wallet_id]}")
    return {
        "wallet_id": wallet_id,
        "profile_url": score.get("profile_url") or "",
        "score": score.get("wallet_score") or "0",
        "priority_bucket": priority,
        "watchlist_inclusion": inclusion,
        "reason_codes": reason_codes or "none",
        "structural_strengths": strengths or "none",
        "structural_weaknesses": risks or "none",
        "confidence_level": confidence,
        "missing_evidence": "; ".join(_missing_evidence_for(score)),
        "recommendation": recommendation,
        "observed": "; ".join(observed),
        "unknown": "; ".join(_missing_evidence_layers()),
    }


def _recommendation(score: dict[str, str], watch: dict[str, str] | None) -> str:
    bucket = score.get("score_band") or ""
    positions = _int(score.get("total_lifecycle_positions"))
    fast_share = _decimal(score.get("fast_crypto_lifecycle_share"))
    still_open = _decimal(score.get("percentage_still_open_positions"))
    if watch and bucket in {"high_priority", "medium_priority"} and positions >= 15 and fast_share >= Decimal("0.5") and still_open < Decimal("0.9"):
        return "monitor_candidate"
    if watch and bucket in {"medium_priority", "low_priority"} and positions >= 5:
        return "needs_more_history"
    if positions >= 5:
        return "insufficient_signal"
    return "exclude_for_now"


def _confidence(positions: int, fast_share: Decimal, still_open: Decimal, oversold: int) -> str:
    if positions >= 25 and fast_share >= Decimal("0.5") and still_open < Decimal("0.75") and oversold == 0:
        return "medium_structural"
    if positions >= 10:
        return "low_to_medium_structural"
    if positions >= 5:
        return "low_structural"
    return "insufficient_visible_history"


def _missing_evidence_for(score: dict[str, str]) -> list[str]:
    missing = _missing_evidence_layers()
    if _decimal(score.get("percentage_still_open_positions")) >= Decimal("0.9"):
        missing.append("later exits beyond bounded window")
    if _int(score.get("oversold_bounded_history")) > 0:
        missing.append("prior buys before bounded window")
    if _decimal(score.get("fast_crypto_lifecycle_share")) == 0:
        missing.append("fast crypto relevance")
    return missing


def _missing_evidence_layers() -> list[str]:
    return [
        "realized outcome joins",
        "expiry joins",
        "complete unbounded wallet history",
        "entry-to-exit holding time",
        "observation delay model",
        "slippage model",
        "liquidity and fill uncertainty",
        "queue position",
        "maker/taker completeness",
        "external BTC/ETH/SOL reference alignment",
    ]


def _research_conclusion(rows: list[dict[str, str]], analysis: dict[str, Any]) -> str:
    monitor = analysis["A_monitor_candidate_count"]
    total = len(rows)
    return (
        f"Based on the current bounded public evidence, Wallet Intelligence is moving toward a useful copy-trading research system only as a structural triage layer: {monitor} of {total} wallets became monitor_candidate and the score separated wallets into multiple structural groups, but missing realized outcomes, expiry joins, complete history, timing-delay, slippage, and liquidity evidence remain too significant for any conclusion about copy outcomes, market advantage, returns, or trading use."
    )


def _score_separation_statement(bands: Counter[str]) -> str:
    non_zero = sum(1 for count in bands.values() if count)
    if non_zero >= 3:
        return f"non_degenerate: scores span {non_zero} priority buckets ({dict(sorted(bands.items()))})"
    if non_zero == 2:
        return f"limited: scores span 2 priority buckets ({dict(sorted(bands.items()))})"
    return f"weak: most wallets collapsed into one priority bucket ({dict(sorted(bands.items()))})"


def _range(values: list[Decimal]) -> dict[str, Any]:
    if not values:
        return {"minimum": "0", "maximum": "0", "range": 0.0}
    minimum = min(values)
    maximum = max(values)
    return {"minimum": str(minimum), "maximum": str(maximum), "range": float(maximum - minimum)}


def _fallback_strengths(score: dict[str, str]) -> str:
    values = []
    if _int(score.get("total_lifecycle_positions")) >= 5:
        values.append("minimum visible lifecycle coverage")
    if _decimal(score.get("fast_crypto_lifecycle_share")) >= Decimal("0.75"):
        values.append("high fast-crypto lifecycle share")
    return "; ".join(values) or "none"


def _fallback_risks(score: dict[str, str]) -> str:
    risks = ["bounded public history only"]
    if _decimal(score.get("percentage_still_open_positions")) >= Decimal("0.9"):
        risks.append("all or mostly open visible lifecycle state")
    if _decimal(score.get("fast_crypto_lifecycle_share")) == 0:
        risks.append("no visible fast-crypto lifecycle share")
    return "; ".join(risks)


def _build_ingestion_report(summary: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# Wallet Public Trade History Broader Evidence v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Scope",
        "",
        "Public read-only wallet activity rows were fetched within the approved broader-evidence limits. Cross-check `/trades` rows were stored separately and were not merged into lifecycle reconstruction.",
        "",
        "## Summary",
        "",
        f"- Wallets attempted: {summary['wallets_attempted']}",
        f"- Wallets with primary rows: {summary['wallets_with_primary_rows']}",
        f"- Primary pages fetched: {summary['primary_pages_fetched']}",
        f"- Primary rows fetched: {summary['primary_rows_fetched']}",
        f"- Primary rows normalized: {summary['primary_rows_normalized']}",
        f"- Cross-check pages fetched: {summary['cross_check_pages_fetched']}",
        f"- Cross-check rows fetched: {summary['cross_check_rows_fetched']}",
        f"- Validation gates passed: {str(summary['validation_gates_passed']).lower()}",
        "",
        "## Validation Gates",
        "",
    ]
    for name, result in summary["validation_gates"].items():
        if isinstance(result, dict):
            lines.append(f"- `{name}`: {'passed' if result.get('passed') else 'failed'}")
    lines.extend(["", "## Reproducibility Hashes", ""])
    for name, value in hashes.items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "No wallet/private-key use, order placement, automatic trade copying, live monitoring, capture campaign, production model training, sealed holdout inspection, or holdout evaluation was performed.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_copyability_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    analysis = summary["analysis"]
    lines = [
        "# Wallet Copyability Feasibility Sprint v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Scope And Non-Claims",
        "",
        "This is public, read-only Wallet Intelligence research. It is not a trading signal, not a copy-trading recommendation, does not provide financial advice, and is not a claim about performance, market advantage, returns, copy outcomes, or execution quality.",
        "",
        "## Evidence Size",
        "",
        f"- Wallet count: {summary['wallet_count']}",
        f"- Primary normalized trade rows: {summary['evidence_size']['primary_rows_normalized']}",
        f"- Cross-check rows fetched: {summary['evidence_size']['cross_check_rows_fetched']}",
        "",
        "## Classification Counts",
        "",
    ]
    for key, value in summary["classification_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Required Research Questions", ""])
    lines.append(f"- A. Monitor candidates: {analysis['A_monitor_candidate_count']}")
    lines.append(f"- B. Exclude for now: {analysis['B_exclude_for_now_count']}")
    lines.append(f"- C. Score separation: {analysis['C_score_separation']}")
    lines.append(f"- D. Most influential structural metrics: {', '.join(analysis['D_most_influential_metrics'])}")
    lines.append(f"- E. Almost useless metrics in this batch: {', '.join(analysis['E_almost_useless_metrics']) or 'none with zero range'}")
    lines.append(
        f"- F. Interesting despite weak raw evidence: {', '.join(analysis['F_interesting_despite_weak_raw_evidence']) or 'none under the sprint rule'}"
    )
    lines.append(f"- G. Largest blockers: {', '.join(analysis['G_largest_remaining_blockers'])}")
    lines.extend(["", "## Observed Versus Unknown", ""])
    lines.append("Observed:")
    for item in summary["observed_vs_unknown"]["observed"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Unknown:")
    for item in summary["observed_vs_unknown"]["unknown"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Wallet Classifications", ""])
    for row in rows:
        lines.append(
            f"- `{row['wallet_id']}`: recommendation={row['recommendation']}, score={row['score']}, bucket={row['priority_bucket']}, confidence={row['confidence_level']}"
        )
        lines.append(f"  - reasons: {row['reason_codes']}")
        lines.append(f"  - strengths: {row['structural_strengths']}")
        lines.append(f"  - weaknesses: {row['structural_weaknesses']}")
        lines.append(f"  - missing: {row['missing_evidence']}")
    lines.extend(["", "## Validation", ""])
    for name, value in summary["validation"].items():
        lines.append(f"- `{name}`: {str(value).lower()}")
    lines.extend(
        [
            "",
            "## Research Conclusion",
            "",
            summary["research_conclusion"],
            "",
            "## Recommended Next Sprint",
            "",
            f"`{summary['recommended_next_sprint']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _read_wallet_manifest(path: Path) -> list[WatchedWallet]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            WatchedWallet(
                wallet_id=(row.get("wallet_id") or "").strip(),
                profile_url=(row.get("profile_url") or "").strip(),
                label=(row.get("label") or "").strip(),
                source=(row.get("source") or "").strip(),
                notes=(row.get("notes") or "").strip(),
            )
            for row in csv.DictReader(handle)
            if (row.get("wallet_id") or "").strip()
        ]


def _write_wallet_manifest(path: Path, wallets: list[WatchedWallet]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WATCHED_WALLETS_FIELDS, lineterminator="\n")
        writer.writeheader()
        for wallet in wallets:
            writer.writerow(
                {
                    "wallet_id": wallet.wallet_id,
                    "profile_url": wallet.profile_url,
                    "label": wallet.label,
                    "source": wallet.source,
                    "notes": wallet.notes,
                }
            )


def _write_csv_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _profile_resolution_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    mapping: dict[str, str] = {}
    for row in _read_csv(path):
        profile_url = (row.get("profile_url") or "").strip()
        wallet_id = _normalize_wallet_id(row.get("wallet_id") or "", profile_url)
        if profile_url and wallet_id.startswith("0x") and len(wallet_id) == 42:
            mapping[profile_url] = wallet_id
    return mapping


def _broader_limit_violations(wallets: list[WatchedWallet], metadata: dict[str, Any], cross_pages: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    if len(wallets) > MAX_WALLETS:
        violations.append("wallet_count_exceeds_limit")
    if metadata["input_rows"] > MAX_PRIMARY_ROWS_TOTAL:
        violations.append("primary_rows_total_exceeds_limit")
    for wallet, rows in metadata["rows_by_wallet"].items():
        if rows > MAX_PRIMARY_ROWS_PER_WALLET:
            violations.append(f"primary_rows_exceed_wallet_limit:{wallet}")
    for wallet, pages in metadata["pages_by_wallet"].items():
        if pages > MAX_PRIMARY_PAGES_PER_WALLET:
            violations.append(f"primary_pages_exceed_wallet_limit:{wallet}")
    cross_by_wallet = Counter(page["wallet_id"] for page in cross_pages)
    for wallet, pages in cross_by_wallet.items():
        if pages > MAX_CROSS_CHECK_PAGES_PER_WALLET:
            violations.append(f"cross_check_pages_exceed_wallet_limit:{wallet}")
    if _cross_check_rows(cross_pages) > MAX_CROSS_CHECK_ROWS_TOTAL:
        violations.append("cross_check_rows_total_exceeds_limit")
    return violations


def _cross_check_rows(pages: list[dict[str, Any]]) -> int:
    return sum(len(page.get("rows") or []) for page in pages)


def _compact_ingestion_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "wallets_attempted": summary.get("wallets_attempted"),
        "wallets_with_primary_rows": summary.get("wallets_with_primary_rows"),
        "primary_rows_normalized": summary.get("primary_rows_normalized"),
        "cross_check_rows_fetched": summary.get("cross_check_rows_fetched"),
        "validation_gates_passed": summary.get("validation_gates_passed"),
        "row_summary": summary.get("row_summary"),
    }


def _normalize_wallet_id(wallet_id: str, profile_url: str = "") -> str:
    value = (wallet_id or "").strip()
    if value.startswith("@"):
        value = value[1:]
    if value.lower().startswith("0x") and len(value) == 42:
        return value.lower()
    tail = (profile_url or "").rstrip("/").split("/")[-1]
    if tail.startswith("@"):
        tail = tail[1:]
    if tail.lower().startswith("0x") and len(tail) == 42:
        return tail.lower()
    return value.lower()


def _recommendation_order(value: str) -> int:
    return {
        "monitor_candidate": 0,
        "needs_more_history": 1,
        "insufficient_signal": 2,
        "exclude_for_now": 3,
    }.get(value, 9)


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def _int(value: Any) -> int:
    try:
        return int(Decimal(str(value or "0")))
    except Exception:
        return 0
