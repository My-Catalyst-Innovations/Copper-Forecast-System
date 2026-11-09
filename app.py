import json
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
STATE_PATH = DATA_DIR / "copper_forecast_state.json"
OVERRIDES_PATH = DATA_DIR / "copper_forecast_overrides.json"
SETTINGS_PATH = DATA_DIR / "copper_forecast_settings.json"
FORECASTS_PATH = DATA_DIR / "copper_future_demand.json"
IMPORT_HISTORY_PATH = DATA_DIR / "copper_import_history.json"
ACTIONS_PATH = DATA_DIR / "copper_item_actions.json"
LARGE_JOBS_PATH = DATA_DIR / "copper_large_jobs.json"
REVIEW_HISTORY_PATH = DATA_DIR / "copper_review_history.json"
SCHEDULE_PATH = DATA_DIR / "copper_current_schedule.json"
ACTIVE_MILL = "Demo Mill A"
FUTURE_MILL = "Demo Mill B"
DIST_SOURCES = ("Demo Distributor A", "Demo Distributor B")
DEFAULT_SOURCE_LEAD_WEEKS = {
    "Demo Mill A": 11.0,
    "Demo Mill B": 9.0,
    "Demo Distributor A": 13.0,
    "Demo Distributor B": 13.0,
}
DEFAULT_SAFETY_WEEKS_BY_MOVER = {
    "Fast": 14.0,
    "Medium": 10.0,
    "Slow": 6.0,
}
SUPABASE_STATE_TABLE = "app_state"
WEEKLY_PROFILES = {
    "Front-loaded": [0.35, 0.25, 0.20, 0.20],
    "Even": [0.25, 0.25, 0.25, 0.25],
    "Mid-month spike": [0.20, 0.35, 0.30, 0.15],
    "Back-loaded": [0.20, 0.20, 0.25, 0.35],
}
CONFIDENCE_WEIGHTS = {
    "High": 1.0,
    "Medium": 0.6,
    "Low": 0.3,
}
OBSOLETE_SIZE_LABELS = {
    '.1875 X 4.00"',
    '.250 X 1.75"',
    '.375 X 1.75"',
    '.5 X 3.0"',
    '.625 X 4.0',
    'T-174-F',
}


st.set_page_config(
    page_title="Copper Forecast System",
    page_icon="CF",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.1rem;
                padding-bottom: 2rem;
                max-width: 1450px;
            }
            .main {
                background:
                    radial-gradient(circle at top right, rgba(201, 166, 91, 0.16), transparent 28%),
                    linear-gradient(180deg, #f5f8fc 0%, #eef3f8 100%);
            }
            .brand-shell {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 0.8rem;
                padding: 0.6rem 0.8rem;
                background: rgba(255,255,255,0.82);
                border: 1px solid #d7e0e7;
                border-radius: 18px;
                box-shadow: 0 10px 22px rgba(18, 54, 75, 0.06);
            }
            .brand-mark {
                min-width: 92px;
                min-height: 68px;
                border-radius: 16px;
                background:
                    radial-gradient(circle at 18% 50%, rgba(201,166,91,0.42) 0%, rgba(201,166,91,0.10) 36%, transparent 37%),
                    linear-gradient(135deg, #005b9a 0%, #0f2743 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: inset 0 0 0 1px rgba(201,166,91,0.22);
            }
            .brand-mark span {
                color: #ffffff;
                font-size: 2rem;
                font-weight: 900;
                letter-spacing: 0.04em;
                line-height: 1;
            }
            .brand-copy h2 {
                margin: 0;
                color: #005b9a;
                font-size: 1.15rem;
            }
            .brand-copy p {
                margin: 0.2rem 0 0 0;
                color: #506777;
                font-size: 0.92rem;
            }
            .hero-card {
                background: linear-gradient(135deg, #005b9a 0%, #0f2743 100%);
                border: 1px solid rgba(201, 166, 91, 0.38);
                border-radius: 24px;
                padding: 1.35rem 1.45rem;
                margin-bottom: 1rem;
                box-shadow: 0 18px 40px rgba(8, 26, 44, 0.18);
            }
            .hero-card h1 {
                margin: 0 0 0.35rem 0;
                color: #fff7e2;
                font-size: 2rem;
            }
            .hero-card p {
                margin: 0;
                color: #d9e4ef;
                max-width: 820px;
                font-size: 1rem;
            }
            .mini-card {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid #d7e0e7;
                border-top: 4px solid #c9a65b;
                border-radius: 18px;
                padding: 0.9rem 1rem;
                box-shadow: 0 10px 24px rgba(18, 54, 75, 0.08);
            }
            .mini-card strong {
                color: #005b9a;
                font-size: 1.4rem;
            }
            .section-card {
                background: rgba(255, 255, 255, 0.96);
                border: 1px solid #d7e0e7;
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 10px 24px rgba(18, 54, 75, 0.08);
                margin-bottom: 1rem;
            }
            .kpi-card {
                background: linear-gradient(180deg, rgba(0, 91, 154, 0.98) 0%, rgba(15, 39, 67, 0.98) 100%);
                border: 1px solid rgba(201, 166, 91, 0.38);
                border-radius: 18px;
                padding: 1rem;
                box-shadow: 0 10px 24px rgba(8, 26, 44, 0.14);
                margin-bottom: 0.85rem;
            }
            .kpi-value {
                color: #f3cd73;
                font-size: 1.65rem;
                font-weight: 800;
                line-height: 1.1;
            }
            .kpi-label {
                color: #dbe6f0;
                font-size: 0.9rem;
                margin-top: 0.25rem;
            }
            .item-hero {
                background: linear-gradient(135deg, #005b9a 0%, #0f2743 100%);
                border: 1px solid rgba(201, 166, 91, 0.35);
                border-radius: 18px;
                padding: 1rem 1.15rem;
                margin: 0 0 1rem 0;
                box-shadow: 0 12px 28px rgba(8, 26, 44, 0.18);
            }
            .item-hero h3 {
                margin: 0 0 0.25rem 0;
                color: #f5efe1;
            }
            .item-hero p {
                margin: 0;
                color: #d9e4ef;
            }
            .stButton > button,
            .stDownloadButton > button {
                border-radius: 12px;
                border: 1px solid #d2dbe4;
                box-shadow: 0 8px 20px rgba(18, 54, 75, 0.08);
            }
            div[data-baseweb="tab"] {
                border-radius: 12px 12px 0 0;
                background: rgba(255,255,255,0.75);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_json(path: Path) -> dict:
    # All demo changes are isolated to this browser session.
    import copy
    return copy.deepcopy(st.session_state.get("demo:" + path.name, {}))


def save_json(path: Path, payload: dict) -> None:
    import copy
    st.session_state["demo:" + path.name] = copy.deepcopy(payload)


def append_import_history(snapshot: dict) -> None:
    if not snapshot:
        return
    history_payload = load_json(IMPORT_HISTORY_PATH)
    entries = history_payload.get("entries", []) if isinstance(history_payload, dict) else []
    items = snapshot.get("items", [])
    total_recommended = sum(number(item.get("tecnofil_on_order_lbs", 0.0)) for item in items)
    entries.append(
        {
            "imported_at": snapshot.get("imported_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "source_name": snapshot.get("source_name", ""),
            "item_count": len(items),
            "current_inventory_lbs": round(sum(number(item.get("icc_inventory_current_lbs", 0.0)) for item in items), 0),
            "plant_available_lbs": round(
                sum(max(0.0, number(item.get("icc_inventory_current_lbs", 0.0)) - number(item.get("jobs_pending_lbs", 0.0))) for item in items),
                0,
            ),
            "mill_on_order_lbs": round(total_recommended, 0),
        }
    )
    save_json(IMPORT_HISTORY_PATH, {"entries": entries[-24:]})


def month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1)


def start_of_week(value: datetime) -> datetime:
    normalized = value.replace(hour=0, minute=0, second=0, microsecond=0)
    return normalized.replace(day=normalized.day) - timedelta(days=normalized.weekday())


def build_default_settings() -> dict:
    return {
        "source_lead_weeks": dict(DEFAULT_SOURCE_LEAD_WEEKS),
        "safety_weeks_by_mover": dict(DEFAULT_SAFETY_WEEKS_BY_MOVER),
        "preferred_mill": ACTIVE_MILL,
        "future_mill": FUTURE_MILL,
        "active_scenario": "Base",
        "planning_horizon_weeks": 26,
        "weekly_demand_profile": "Front-loaded",
        "monthly_review_day": 1,
        "source_moq_lbs": {
            "direct_mill": 40000.0,
            "distribution": 10000.0,
        },
        "confidence_weights": dict(CONFIDENCE_WEIGHTS),
        "dc_release_date": "2026-07-31",
        "dc_target_lbs_by_mover": {
            "Fast": 3000.0,
            "Medium": 3000.0,
            "Slow": 1000.0,
        },
    }


def load_settings() -> dict:
    saved = load_json(SETTINGS_PATH)
    defaults = build_default_settings()
    defaults["source_lead_weeks"].update(saved.get("source_lead_weeks", {}))
    defaults["safety_weeks_by_mover"].update(saved.get("safety_weeks_by_mover", {}))
    defaults["preferred_mill"] = saved.get("preferred_mill", ACTIVE_MILL) or ACTIVE_MILL
    defaults["future_mill"] = saved.get("future_mill", FUTURE_MILL) or FUTURE_MILL
    defaults["active_scenario"] = saved.get("active_scenario", "Base") or "Base"
    defaults["planning_horizon_weeks"] = int(saved.get("planning_horizon_weeks", 26) or 26)
    defaults["weekly_demand_profile"] = saved.get("weekly_demand_profile", "Front-loaded") or "Front-loaded"
    defaults["monthly_review_day"] = int(saved.get("monthly_review_day", 1) or 1)
    defaults["source_moq_lbs"].update(saved.get("source_moq_lbs", {}))
    defaults["confidence_weights"].update(saved.get("confidence_weights", {}))
    defaults["dc_release_date"] = saved.get("dc_release_date", "2026-07-31") or "2026-07-31"
    defaults["dc_target_lbs_by_mover"].update(saved.get("dc_target_lbs_by_mover", {}))
    return defaults


def resolve_logo_path() -> Path | None:
    return None


def ensure_local_snapshot_exists() -> None:
    if load_json(STATE_PATH):
        return
    items = []
    # These values are invented for demonstration and are not ICC records.
    for size, stock, demand, distribution, inbound in [
        ("0.25 x 1.00", 4800, 1600, 900, 3000),
        ("0.50 x 2.00", 900, 2100, 2400, 0),
        ("0.75 x 3.00", 12500, 700, 800, 0),
        ("1.00 x 2.00", 3400, 1200, 600, 1800),
    ]:
        item = build_placeholder_item(size)
        item.update({"icc_inventory_current_lbs": stock, "avg_monthly_lbs": demand,
                     "adjusted_usage_7mo_lbs": demand * 7, "usage_prev_7mo_lbs": demand * 7,
                     "williams_on_hand_lbs": distribution, "tecnofil_on_order_lbs": inbound,
                     "total_on_order_lbs": inbound, "data_status": "Synthetic demo"})
        items.append(item)
    save_json(STATE_PATH, {"source_name": "Fictional demonstration data", "imported_at": "Demo", "items": items})


def normalize_snapshot(snapshot: dict) -> dict:
    if not isinstance(snapshot, dict):
        return {"source_name": "", "imported_at": "", "items": []}
    items = snapshot.get("items", [])
    cleaned_items = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        size = clean_size(item.get("size"))
        if not size:
            continue
        size_key = canonical_size(size)
        if size_key in OBSOLETE_SIZES or size_key in seen:
            continue
        normalized = dict(item)
        normalized["size"] = size
        seen.add(size_key)
        cleaned_items.append(normalized)
    cleaned_items = sorted(cleaned_items, key=lambda entry: size_sort_key(entry["size"]))
    return {
        "source_name": snapshot.get("source_name", ""),
        "imported_at": snapshot.get("imported_at", ""),
        "items": cleaned_items,
    }


def clean_size(value: object) -> str:
    return str(value or "").strip()


def canonical_size(value: object) -> str:
    text = clean_size(value).upper()
    for token in ['"', " "]:
        text = text.replace(token, "")
    text = text.replace("X", "X")
    text = text.replace(".50", ".5")
    text = text.replace(".0", "")
    return text


OBSOLETE_SIZES = {canonical_size(size) for size in OBSOLETE_SIZE_LABELS}


def size_sort_key(size: str) -> tuple:
    text = clean_size(size)
    if "X" in text.upper():
        normalized = text.upper().replace('"', "")
        parts = normalized.split("X", 1)
        try:
            thickness = float(parts[0].strip())
        except ValueError:
            thickness = 999.0
        try:
            width = float(parts[1].strip())
        except ValueError:
            width = 999.0
        return (0, thickness, width, text.upper())
    return (1, 999.0, 999.0, text.upper())


def build_placeholder_item(size: str) -> dict:
    return {
        "size": size,
        "inventory_7mo_ago_lbs": 0.0,
        "received_prev_7mo_lbs": 0.0,
        "usage_prev_7mo_lbs": 0.0,
        "alt_for_other_lbs": 0.0,
        "alt_used_for_size_lbs": 0.0,
        "adjusted_usage_7mo_lbs": 0.0,
        "usage_share": 0.0,
        "avg_monthly_lbs": 0.0,
        "williams_on_hand_lbs": 0.0,
        "williams_on_order_lbs": 0.0,
        "maverick_on_hand_lbs": 0.0,
        "maverick_on_order_lbs": 0.0,
        "sam_dong_on_order_lbs": 0.0,
        "tecnofil_on_order_lbs": 0.0,
        "total_on_order_lbs": 0.0,
        "williams_general_inventory_lbs": 0.0,
        "icc_inventory_current_lbs": 0.0,
        "jobs_pending_lbs": 0.0,
        "total_available_reported_lbs": 0.0,
        "avg_monthly_supply_lbs": 0.0,
        "large_jobs_prev_7mo_lbs": 0.0,
        "avg_monthly_supply_ex_large_lbs": 0.0,
        "data_status": "Placeholder",
    }


def number(value: object) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def classify_movers(items: list[dict]) -> dict:
    ranked = sorted(
        [(item["size"], item.get("avg_monthly_lbs", 0.0) or 0.0) for item in items],
        key=lambda pair: pair[1],
    )
    count = len(ranked)
    mover_map = {}
    if not count:
        return mover_map
    for index, (size, _) in enumerate(ranked, start=1):
        position = index / count
        if position > 0.67:
            mover_map[size] = "Fast"
        elif position > 0.34:
            mover_map[size] = "Medium"
        else:
            mover_map[size] = "Slow"
    return mover_map


def choose_action(
    *,
    weekly_usage: float,
    plant_available_lbs: float,
    net_supply_lbs: float,
    dc_on_hand_lbs: float,
    reorder_point_lbs: float,
    target_stock_lbs: float,
    recommended_order_lbs: float,
) -> tuple[str, str]:
    if weekly_usage <= 0:
        if net_supply_lbs > 0:
            return "Excess Risk", "No current demand signal is showing, so this size should be reviewed for slow movement."
        return "Healthy", "No recent demand signal and no active supply issue."
    if plant_available_lbs < weekly_usage * 4 and dc_on_hand_lbs > 0:
        return "Pull From DC", "Plant coverage is short-term only, so distribution inventory should protect the schedule."
    if net_supply_lbs < reorder_point_lbs:
        return "Order Now", "Net supply will not cover mill lead time plus safety stock."
    if net_supply_lbs > target_stock_lbs * 1.6:
        return "Excess Risk", "Net supply is well above the current target range for this size."
    if recommended_order_lbs > 0:
        return "Monitor", "The item is above reorder point now, but it should stay on the buyer watch list."
    return "Healthy", "Supply position is currently inside the target range."


def planning_sort_key(row: dict) -> tuple:
    priority = {
        "Order Now": 0,
        "Pull From DC": 1,
        "Excess Risk": 2,
        "Monitor": 3,
        "Healthy": 4,
    }
    size_key = size_sort_key(row["size"])
    return (priority.get(row["action_bucket"], 9), -row["recommended_order_lbs"], size_key)


def largest_dc_source(item: dict) -> str:
    if item.get("williams_on_hand_lbs", 0.0) >= item.get("maverick_on_hand_lbs", 0.0):
        return "Demo Distributor A"
    return "Demo Distributor B"


def choose_source(source_override: str, recommendation_qty: float, preferred_mill: str) -> str:
    if source_override and source_override != "Auto":
        return source_override
    if recommendation_qty <= 0:
        return "None"
    return preferred_mill


def apply_moq_to_recommendation(
    recommendation_qty: float,
    recommended_source: str,
    settings: dict,
) -> tuple[float, str]:
    if recommendation_qty <= 0 or recommended_source == "None":
        return 0.0, ""
    return recommendation_qty, ""


def summarize_order_baskets(plan_rows: list[dict], settings: dict) -> list[dict]:
    moq_settings = settings.get("source_moq_lbs", {})
    source_groups: dict[str, list[dict]] = {}
    for row in plan_rows:
        source = row.get("recommended_source", "None")
        if source == "None" or number(row.get("recommended_order_lbs", 0.0)) <= 0:
            continue
        group_key = "Distribution" if source in DIST_SOURCES else source
        source_groups.setdefault(group_key, []).append(row)

    summaries = []
    for source, rows in source_groups.items():
        total_lbs = sum(number(row.get("recommended_order_lbs", 0.0)) for row in rows)
        moq = number(moq_settings.get("distribution", 10000.0)) if source == "Distribution" else number(moq_settings.get("direct_mill", 40000.0))
        gap = max(0.0, moq - total_lbs)
        summaries.append(
            {
                "Source Basket": source,
                "SKUs in Basket": len(rows),
                "Recommended Total (lbs)": round(total_lbs, 0),
                "MOQ (lbs)": round(moq, 0),
                "MOQ Gap (lbs)": round(gap, 0),
                "Meets MOQ": "Yes" if gap <= 0 else "No",
            }
        )
    return summaries


def build_monthly_po_rows(plan_rows: list[dict], settings: dict) -> list[dict]:
    next_review = next_monthly_review_date(settings).strftime("%Y-%m-%d")
    rows = []
    for row in plan_rows:
        order_by = row.get("order_by_date", "Now")
        include = order_by == "Now" or order_by <= next_review
        if not include or number(row.get("recommended_order_lbs", 0.0)) <= 0:
            continue
        rows.append(
            {
                "Source": row.get("recommended_source", "None"),
                "Copper Size": row["size"],
                "Suggested Qty (lbs)": round(number(row.get("recommended_order_lbs", 0.0)), 0),
                "Action": row.get("action_bucket", ""),
                "Order By": order_by,
                "Expected Receipt": row.get("expected_receipt_date", "N/A"),
                "Reason": row.get("recommendation_reason", ""),
            }
        )
    return rows


def normalize_forecast_entries(raw_payload: dict | list) -> list[dict]:
    if isinstance(raw_payload, dict):
        entries = raw_payload.get("entries", [])
    elif isinstance(raw_payload, list):
        entries = raw_payload
    else:
        entries = []
    cleaned = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        size = clean_size(entry.get("size"))
        month = clean_size(entry.get("month"))
        scenario = clean_size(entry.get("scenario")) or "Base"
        lbs = number(entry.get("monthly_lbs"))
        confidence = clean_size(entry.get("confidence")) or "High"
        if size and month:
            cleaned.append(
                {
                    "size": size,
                    "month": month,
                    "scenario": scenario,
                    "monthly_lbs": lbs,
                    "note": clean_size(entry.get("note")),
                    "confidence": confidence,
                    "customer": clean_size(entry.get("customer")),
                }
            )
    return cleaned


def normalize_large_job_entries(raw_payload: dict | list) -> list[dict]:
    if isinstance(raw_payload, dict):
        entries = raw_payload.get("entries", [])
    elif isinstance(raw_payload, list):
        entries = raw_payload
    else:
        entries = []
    cleaned = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        size = clean_size(entry.get("size"))
        month = clean_size(entry.get("month"))
        lbs = number(entry.get("lbs"))
        if size and month and lbs:
            cleaned.append(
                {
                    "size": size,
                    "month": month,
                    "lbs": lbs,
                    "job_name": clean_size(entry.get("job_name")),
                    "note": clean_size(entry.get("note")),
                }
            )
    return cleaned


def normalize_schedule_entries(raw_payload: dict | list) -> list[dict]:
    if isinstance(raw_payload, dict):
        entries = raw_payload.get("entries", [])
    elif isinstance(raw_payload, list):
        entries = raw_payload
    else:
        entries = []
    cleaned = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        size = clean_size(entry.get("size"))
        want_date = clean_size(entry.get("want_date"))
        lbs = number(entry.get("lbs"))
        if size and want_date and lbs:
            want_dt = parse_date_string(want_date)
            ship_date = clean_size(entry.get("ship_date")) or (want_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            cleaned.append(
                {
                    "size": size,
                    "want_date": want_dt.strftime("%Y-%m-%d"),
                    "ship_date": ship_date,
                    "lbs": lbs,
                    "job_name": clean_size(entry.get("job_name")),
                    "customer": clean_size(entry.get("customer")),
                    "note": clean_size(entry.get("note")),
                }
            )
    return cleaned


def build_future_demand_map(forecast_entries: list[dict], active_scenario: str, settings: dict) -> dict[str, dict]:
    selected = [entry for entry in forecast_entries if entry.get("scenario") == active_scenario]
    grouped: dict[str, list[dict]] = {}
    for entry in selected:
        grouped.setdefault(entry["size"], []).append(entry)
    result: dict[str, dict] = {}
    for size, entries in grouped.items():
        sorted_entries = sorted(entries, key=lambda item: item["month"])
        monthly_values = [
            number(item.get("monthly_lbs")) * number(settings.get("confidence_weights", {}).get(item.get("confidence", "High"), 1.0))
            for item in sorted_entries
        ]
        result[size] = {
            "future_monthly_lbs": sum(monthly_values) / len(monthly_values) if monthly_values else 0.0,
            "future_total_lbs": sum(monthly_values),
            "future_month_count": len(monthly_values),
            "future_months": ", ".join(item["month"] for item in sorted_entries[:6]),
            "future_confidence_mix": ", ".join(sorted({item.get("confidence", "High") for item in sorted_entries})),
        }
    return result


def format_date_from_weeks(weeks_from_now: float) -> str:
    target = datetime.today() + timedelta(weeks=max(0.0, weeks_from_now))
    return target.strftime("%Y-%m-%d")


def parse_date_string(value: str, fallback: datetime | None = None) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return fallback or datetime.today()


def target_dc_lbs_for_mover(mover_class: str, settings: dict) -> float:
    return number(settings.get("dc_target_lbs_by_mover", {}).get(mover_class, 1000.0))


def schedule_lbs_in_window(
    schedule_entries: list[dict],
    size: str,
    start_date: datetime | None = None,
    days_forward: int = 35,
) -> float:
    window_start = (start_date or datetime.today()).replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(days=days_forward)
    total = 0.0
    for entry in schedule_entries:
        if entry.get("size") != size:
            continue
        want_dt = parse_date_string(entry.get("want_date", ""), fallback=window_start)
        if window_start <= want_dt <= window_end:
            total += number(entry.get("lbs", 0.0))
    return total


def next_monthly_review_date(settings: dict, base_date: datetime | None = None) -> datetime:
    anchor = base_date or datetime.today()
    review_day = max(1, min(28, int(settings.get("monthly_review_day", 1) or 1)))
    if anchor.day <= review_day:
        return anchor.replace(day=review_day, hour=0, minute=0, second=0, microsecond=0)
    next_month = add_months(anchor.replace(day=1), 1)
    return next_month.replace(day=review_day, hour=0, minute=0, second=0, microsecond=0)


def recommendation_timing(row: dict, settings: dict) -> tuple[str, str]:
    source_name = row.get("recommended_source", settings.get("preferred_mill", ACTIVE_MILL))
    if source_name in DIST_SOURCES:
        lead_weeks = number(settings.get("source_lead_weeks", {}).get(source_name, 13.0))
    elif source_name == "None":
        lead_weeks = 0.0
    else:
        lead_weeks = number(settings.get("source_lead_weeks", {}).get(settings.get("preferred_mill", ACTIVE_MILL), 11.0))
    weeks_to_stockout = number(row.get("net_coverage_weeks", 0.0))
    order_by_weeks = max(0.0, weeks_to_stockout - lead_weeks)
    next_review = next_monthly_review_date(settings)
    next_review_str = next_review.strftime("%Y-%m-%d")
    order_by = "Now" if row.get("action_bucket") in {"Order Now", "Pull From DC"} or order_by_weeks <= 0 else format_date_from_weeks(order_by_weeks)
    if order_by != "Now" and order_by <= next_review_str:
        order_by = next_review_str
    receipt_date = format_date_from_weeks(lead_weeks) if lead_weeks > 0 else "N/A"
    return order_by, receipt_date


def build_plan(
    snapshot: dict,
    overrides: dict,
    settings: dict,
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
) -> list[dict]:
    items = snapshot.get("items", [])
    lead_weeks = settings.get("source_lead_weeks", {})
    safety_by_mover = settings.get("safety_weeks_by_mover", {})
    preferred_mill = settings.get("preferred_mill", ACTIVE_MILL)
    future_mill = settings.get("future_mill", FUTURE_MILL)
    active_scenario = settings.get("active_scenario", "Base")
    review_cycle_weeks = 4.345
    future_demand_map = build_future_demand_map(forecast_entries, active_scenario, settings)
    mover_map = classify_movers(items)
    planning_rows = []
    for item in items:
        override = overrides.get(item["size"], {})
        base_monthly_lbs = item.get("avg_monthly_lbs") or round(item.get("adjusted_usage_7mo_lbs", 0.0) / 7.0, 2)
        manual_adjustment_lbs = float(override.get("manual_adjustment_lbs", 0.0) or 0.0)
        future_sales_lbs = future_demand_map.get(item["size"], {}).get("future_monthly_lbs", 0.0)
        large_job_monthly_lbs = (
            sum(number(entry.get("lbs", 0.0)) for entry in large_job_entries if entry.get("size") == item["size"])
            / max(1, round(number(settings.get("planning_horizon_weeks", 26)) / 4))
        )
        schedule_monthly_lbs = schedule_lbs_in_window(schedule_entries, item["size"])
        forecast_monthly_lbs = max(
            0.0, base_monthly_lbs + manual_adjustment_lbs + future_sales_lbs + large_job_monthly_lbs + schedule_monthly_lbs
        )
        weekly_usage = forecast_monthly_lbs / 4.345 if forecast_monthly_lbs else 0.0
        mover_class = mover_map.get(item["size"], "Slow")
        safety_weeks = float(safety_by_mover.get(mover_class, DEFAULT_SAFETY_WEEKS_BY_MOVER[mover_class]))
        dc_target_lbs = target_dc_lbs_for_mover(mover_class, settings)

        plant_available_lbs = max(0.0, item.get("icc_inventory_current_lbs", 0.0) - item.get("jobs_pending_lbs", 0.0))
        dc_on_hand_lbs = item.get("williams_on_hand_lbs", 0.0) + item.get("maverick_on_hand_lbs", 0.0)
        dc_on_order_lbs = item.get("williams_on_order_lbs", 0.0) + item.get("maverick_on_order_lbs", 0.0)
        mill_on_order_lbs = item.get("tecnofil_on_order_lbs", 0.0)
        inbound_total_lbs = dc_on_order_lbs + mill_on_order_lbs
        dc_over_target_lbs = max(0.0, dc_on_hand_lbs - dc_target_lbs)
        current_supply_lbs = plant_available_lbs + dc_over_target_lbs
        net_supply_lbs = current_supply_lbs + inbound_total_lbs

        safety_stock_lbs = weekly_usage * safety_weeks
        reorder_point_lbs = weekly_usage * float(lead_weeks.get(preferred_mill, 11.0)) + safety_stock_lbs
        target_stock_lbs = weekly_usage * (float(lead_weeks.get(preferred_mill, 11.0)) + safety_weeks + review_cycle_weeks)
        current_coverage_weeks = (current_supply_lbs / weekly_usage) if weekly_usage else 999.0
        net_coverage_weeks = (net_supply_lbs / weekly_usage) if weekly_usage else 999.0
        recommendation_qty = max(0.0, target_stock_lbs - net_supply_lbs)
        action_bucket, recommendation_reason = choose_action(
            weekly_usage=weekly_usage,
            plant_available_lbs=plant_available_lbs,
            net_supply_lbs=net_supply_lbs,
            dc_on_hand_lbs=dc_on_hand_lbs,
            reorder_point_lbs=reorder_point_lbs,
            target_stock_lbs=target_stock_lbs,
            recommended_order_lbs=recommendation_qty,
        )
        source_override = override.get("source_override", "Auto")
        recommended_source = choose_source(source_override, recommendation_qty, preferred_mill)
        moq_note = ""
        if action_bucket == "Pull From DC":
            recommendation_qty = min(dc_on_hand_lbs, max(0.0, (weekly_usage * 6.0) - plant_available_lbs))
            recommended_source = source_override if source_override not in {"", "Auto"} else largest_dc_source(item)
            recommendation_qty, moq_note = apply_moq_to_recommendation(recommendation_qty, recommended_source, settings)
        elif action_bucket in {"Healthy", "Monitor", "Excess Risk"}:
            recommendation_qty = 0.0 if action_bucket != "Monitor" else recommendation_qty
            if action_bucket == "Excess Risk":
                recommended_source = "None"
        else:
            recommendation_qty, moq_note = apply_moq_to_recommendation(recommendation_qty, recommended_source, settings)

        planning_rows.append(
            {
                "size": item["size"],
                "mover_class": mover_class,
                "base_monthly_lbs": base_monthly_lbs,
                "manual_adjustment_lbs": manual_adjustment_lbs,
                "future_sales_monthly_lbs": future_sales_lbs,
                "large_job_monthly_lbs": large_job_monthly_lbs,
                "schedule_monthly_lbs": schedule_monthly_lbs,
                "forecast_monthly_lbs": forecast_monthly_lbs,
                "plant_available_lbs": plant_available_lbs,
                "dc_on_hand_lbs": dc_on_hand_lbs,
                "dc_target_lbs": dc_target_lbs,
                "dc_over_target_lbs": dc_over_target_lbs,
                "dc_on_order_lbs": dc_on_order_lbs,
                "mill_on_order_lbs": mill_on_order_lbs,
                "inbound_total_lbs": inbound_total_lbs,
                "net_supply_lbs": net_supply_lbs,
                "current_coverage_weeks": current_coverage_weeks,
                "net_coverage_weeks": net_coverage_weeks,
                "safety_stock_lbs": safety_stock_lbs,
                "reorder_point_lbs": reorder_point_lbs,
                "target_stock_lbs": target_stock_lbs,
                "recommended_order_lbs": recommendation_qty,
                "recommended_source": recommended_source,
                "action_bucket": action_bucket,
                "recommendation_reason": (recommendation_reason + (" " + moq_note if moq_note else "")).strip(),
                "jobs_pending_lbs": item.get("jobs_pending_lbs", 0.0),
                "override_note": override.get("note", "").strip(),
                "preferred_mill": preferred_mill,
                "future_mill": future_mill,
                "active_scenario": active_scenario,
                "future_sales_months": future_demand_map.get(item["size"], {}).get("future_months", ""),
                "future_confidence_mix": future_demand_map.get(item["size"], {}).get("future_confidence_mix", ""),
                "moq_note": moq_note,
            }
        )
    for row in planning_rows:
        row["order_by_date"], row["expected_receipt_date"] = recommendation_timing(row, settings)
    return sorted(planning_rows, key=planning_sort_key)


def get_monthly_demand_map(
    plan_row: dict,
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
    settings: dict,
) -> dict[str, float]:
    active_scenario = settings.get("active_scenario", "Base")
    base_monthly = number(plan_row.get("base_monthly_lbs", 0.0)) + number(plan_row.get("manual_adjustment_lbs", 0.0))
    month_map: dict[str, float] = {}
    matching_entries = [
        entry
        for entry in forecast_entries
        if entry.get("size") == plan_row["size"] and entry.get("scenario") == active_scenario
    ]
    for entry in matching_entries:
        month_key = entry["month"]
        weight = number(settings.get("confidence_weights", {}).get(entry.get("confidence", "High"), 1.0))
        month_map[month_key] = base_monthly + number(entry.get("monthly_lbs", 0.0)) * weight
    for job in large_job_entries:
        if job.get("size") == plan_row["size"]:
            month_key = job["month"]
            month_map[month_key] = month_map.get(month_key, base_monthly) + number(job.get("lbs", 0.0))
    start_month = month_start(datetime.today())
    for offset in range(9):
        month_key = add_months(start_month, offset).strftime("%Y-%m")
        month_map.setdefault(month_key, base_monthly)
    return month_map


def get_weekly_profile(settings: dict) -> list[float]:
    profile_name = settings.get("weekly_demand_profile", "Front-loaded")
    return WEEKLY_PROFILES.get(profile_name, WEEKLY_PROFILES["Front-loaded"])


def monthly_profile_for_week_count(week_count: int, settings: dict) -> list[float]:
    profile = get_weekly_profile(settings)
    if week_count <= 4:
        raw = profile[:week_count]
    else:
        raw = profile[:3] + [profile[3] / (week_count - 3)] * (week_count - 3)
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def build_weekly_projection(
    plan_row: dict,
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
    settings: dict,
) -> list[dict]:
    horizon_weeks = int(settings.get("planning_horizon_weeks", 26) or 26)
    today_week = start_of_week(datetime.today())
    monthly_demand_map = get_monthly_demand_map(plan_row, forecast_entries, large_job_entries, schedule_entries, settings)
    total_supply = number(plan_row.get("plant_available_lbs", 0.0))
    dc_on_hand_lbs = number(plan_row.get("dc_on_hand_lbs", 0.0))
    dc_target_lbs = number(plan_row.get("dc_target_lbs", 0.0))
    inbound_events = {
        int(round(number(settings["source_lead_weeks"].get(settings.get("preferred_mill", ACTIVE_MILL), 11.0)))): number(
            plan_row.get("mill_on_order_lbs", 0.0)
        ),
        int(round(number(settings["source_lead_weeks"].get("Demo Distributor A", 13.0)))): number(plan_row.get("dc_on_order_lbs", 0.0)),
    }
    dc_release_date = parse_date_string(settings.get("dc_release_date", "2026-07-31"))
    dc_release_week = start_of_week(dc_release_date)
    dc_release_lbs = max(0.0, dc_on_hand_lbs - dc_target_lbs)
    week_starts = [today_week + timedelta(weeks=week_index) for week_index in range(horizon_weeks)]
    month_groups: dict[str, list[datetime]] = {}
    for week_start in week_starts:
        month_groups.setdefault(week_start.strftime("%Y-%m"), []).append(week_start)
    month_profiles = {
        month_key: monthly_profile_for_week_count(len(week_list), settings)
        for month_key, week_list in month_groups.items()
    }
    schedule_events: dict[str, float] = {}
    for schedule in schedule_entries:
        if schedule.get("size") == plan_row["size"]:
            week_key = start_of_week(parse_date_string(schedule["want_date"])).strftime("%Y-%m-%d")
            schedule_events[week_key] = schedule_events.get(week_key, 0.0) + number(schedule.get("lbs", 0.0))
    weeks = []
    running_supply = total_supply
    stockout_week = None
    for week_index, week_start in enumerate(week_starts):
        week_end = week_start + timedelta(days=6)
        month_key = week_start.strftime("%Y-%m")
        week_index_in_month = month_groups[month_key].index(week_start)
        monthly_lbs = number(monthly_demand_map.get(month_key, plan_row.get("forecast_monthly_lbs", 0.0)))
        weekly_demand = monthly_lbs * month_profiles[month_key][week_index_in_month]
        weekly_demand += number(schedule_events.get(week_start.strftime("%Y-%m-%d"), 0.0))
        inbound_lbs = number(inbound_events.get(week_index, 0.0))
        if week_start >= dc_release_week and dc_release_lbs > 0:
            inbound_lbs += dc_release_lbs
            dc_release_lbs = 0.0
        opening_supply = running_supply
        closing_supply = opening_supply + inbound_lbs - weekly_demand
        if stockout_week is None and closing_supply < 0:
            stockout_week = week_index + 1
        weeks.append(
            {
                "week_number": week_index + 1,
                "week_label": f"W{week_index + 1} ({week_start.strftime('%Y-%m-%d')})",
                "month": month_key,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "opening_supply_lbs": round(opening_supply, 1),
                "inbound_lbs": round(inbound_lbs, 1),
                "demand_lbs": round(weekly_demand, 1),
                "closing_supply_lbs": round(closing_supply, 1),
            }
        )
        running_supply = closing_supply
    return weeks


def summarize_projection(weeks: list[dict]) -> dict:
    stockout = next((week for week in weeks if number(week.get("closing_supply_lbs", 0.0)) < 0), None)
    return {
        "stockout_week_label": stockout.get("week_label") if stockout else "None in horizon",
        "weeks_to_stockout": stockout.get("week_number") if stockout else None,
        "min_closing_supply_lbs": min((number(week.get("closing_supply_lbs", 0.0)) for week in weeks), default=0.0),
    }


def build_exception_rows(
    plan_rows: list[dict],
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
    settings: dict,
) -> list[dict]:
    rows = []
    for row in plan_rows:
        weeks = build_weekly_projection(row, forecast_entries, large_job_entries, schedule_entries, settings)
        projection_summary = summarize_projection(weeks)
        weeks_to_stockout = projection_summary["weeks_to_stockout"]
        horizon_bucket = "No stockout in horizon"
        if weeks_to_stockout is not None:
            if weeks_to_stockout <= 4:
                horizon_bucket = "Stockout <= 4 weeks"
            elif weeks_to_stockout <= 8:
                horizon_bucket = "Stockout <= 8 weeks"
            elif weeks_to_stockout <= 12:
                horizon_bucket = "Stockout <= 12 weeks"
            else:
                horizon_bucket = "Stockout > 12 weeks"
        rows.append(
            {
                "Copper Size": row["size"],
                "Action": row["action_bucket"],
                "Exception": horizon_bucket,
                "Stockout Week": projection_summary["stockout_week_label"],
                "Net Coverage (weeks)": round(number(row.get("net_coverage_weeks", 0.0)), 1),
                "Recommended Source": row["recommended_source"],
                "Recommended Qty (lbs)": round(number(row.get("recommended_order_lbs", 0.0)), 0),
                "Min Projected Supply (lbs)": round(number(projection_summary["min_closing_supply_lbs"]), 0),
            }
        )
    priority = {
        "Stockout <= 4 weeks": 0,
        "Stockout <= 8 weeks": 1,
        "Stockout <= 12 weeks": 2,
        "Stockout > 12 weeks": 3,
        "No stockout in horizon": 4,
    }
    return sorted(rows, key=lambda item: (priority.get(item["Exception"], 9), -item["Recommended Qty (lbs)"], item["Copper Size"]))


def render_hero(snapshot: dict, plan_rows: list[dict]) -> None:
    logo_path = resolve_logo_path()
    if logo_path:
        brand_col1, brand_col2 = st.columns([0.16, 0.84])
        with brand_col1:
            st.image(str(logo_path), width=120)
        with brand_col2:
            st.markdown(
                """
                <div class="brand-shell">
                    <div class="brand-copy">
                        <h2>Copper Planning Demo</h2>
                        <p>Copper planning prototype designed for leadership visibility, buyer action, and future ERP/API readiness.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="brand-shell">
                <div class="brand-mark"><span>DEMO</span></div>
                <div class="brand-copy">
                    <h2>Copper Planning Demo</h2>
                    <p>Copper planning prototype designed for leadership visibility, buyer action, and future ERP/API readiness.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="hero-card">
            <h1>Copper Forecast System</h1>
            <p>Track plant inventory, distribution stock, inbound copper, and reorder timing in pounds with direct-mill-first logic and planner overrides.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    shortage_count = len([row for row in plan_rows if row["action_bucket"] in {"Order Now", "Pull From DC"}])
    excess_count = len([row for row in plan_rows if row["action_bucket"] == "Excess Risk"])
    total_buy = sum(row["recommended_order_lbs"] for row in plan_rows)
    cards = [
        (len(snapshot.get("items", [])), "Active sizes"),
        (shortage_count, "Shortage actions"),
        (excess_count, "Excess risks"),
        (f"{total_buy:,.0f}", "Recommended lbs"),
    ]
    cols = st.columns(4)
    for col, (value, label) in zip(cols, cards):
        col.markdown(f'<div class="mini-card"><strong>{value}</strong><br>{label}</div>', unsafe_allow_html=True)


def render_dashboard(plan_rows: list[dict], snapshot: dict, settings: dict) -> None:
    if not plan_rows:
        st.info("Load your copper workbook in `Data Import / Refresh` to populate the planning dashboard.")
        return
    kpi_cols = st.columns(4)
    kpis = [
        ("Items in plan", len(plan_rows)),
        ("Order now", len([row for row in plan_rows if row["action_bucket"] == "Order Now"])),
        ("Pull from DC", len([row for row in plan_rows if row["action_bucket"] == "Pull From DC"])),
        ("Monitor", len([row for row in plan_rows if row["action_bucket"] == "Monitor"])),
    ]
    for col, (label, value) in zip(kpi_cols, kpis):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    left, right = st.columns([1.3, 1.0])
    with left:
        st.markdown("#### Action Queue")
        rows = [
            {
                "Copper Size": row["size"],
                "Action": row["action_bucket"],
                "Source": row["recommended_source"],
                "Qty (lbs)": round(row["recommended_order_lbs"], 0),
                "Net Coverage (weeks)": round(row["net_coverage_weeks"], 1),
            }
            for row in plan_rows
            if row["action_bucket"] != "Healthy"
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### Planning Rules")
        st.write(f"Preferred direct mill: {settings.get('preferred_mill', ACTIVE_MILL)}")
        st.write(f"Future mill: {settings.get('future_mill', FUTURE_MILL)}")
        st.write(f"Active scenario: {settings.get('active_scenario', 'Base')}")
        st.write("Distribution centers are used as safety coverage when plant supply gets too tight.")
        st.write(f"Active workbook: {snapshot.get('source_name', 'Not loaded')}")
        st.write(f"Latest import: {snapshot.get('imported_at', 'Not loaded')}")
        items = snapshot.get("items", [])
        if items:
            st.write(f"Active current inventory: {round(sum(number(item.get('icc_inventory_current_lbs', 0.0)) for item in items), 0):,.0f} lbs")
            st.write(f"Active on-order total: {round(sum(number(item.get('total_on_order_lbs', 0.0)) for item in items), 0):,.0f} lbs")
    chart_data = {row["size"]: row["recommended_order_lbs"] for row in plan_rows if row["recommended_order_lbs"] > 0}
    if chart_data:
        st.markdown("#### Top Recommended Buys")
        st.bar_chart(chart_data)


def render_executive_summary(plan_rows: list[dict], snapshot: dict, settings: dict) -> None:
    st.markdown("#### Executive Summary")
    if not plan_rows:
        st.info("Load the workbook first so the executive summary can show live planning metrics.")
        return
    shortage_rows = [row for row in plan_rows if row["action_bucket"] in {"Order Now", "Pull From DC"}]
    excess_rows = [row for row in plan_rows if row["action_bucket"] == "Excess Risk"]
    direct_rows = [row for row in shortage_rows if row["recommended_source"] not in DIST_SOURCES]
    dc_rows = [row for row in shortage_rows if row["recommended_source"] in DIST_SOURCES]
    st.markdown(
        """
        <div class="section-card">
            <strong>What this system does</strong><br>
            Combines current inventory, DC inventory, inbound supply, lead times, MOQ rules, future demand, and non-linear weekly usage to recommend when to buy copper and where to source it.
        </div>
        """,
        unsafe_allow_html=True,
    )
    summary_cols = st.columns(4)
    summary_cols[0].metric("Urgent actions", len(shortage_rows))
    summary_cols[1].metric("Direct mill actions", len(direct_rows))
    summary_cols[2].metric("DC actions", len(dc_rows))
    summary_cols[3].metric("Excess reviews", len(excess_rows))

    st.markdown("##### Key talking points")
    st.write("1. Forecasting is performed by copper size, not just total pounds, because stockout risk happens at the item level.")
    st.write("2. The model uses source-specific lead times and MOQ rules, so recommendations align with real purchasing constraints.")
    st.write("3. DC inventory is no longer treated as permanent supply; it follows a release-date and target-buffer logic.")
    st.write("4. Future sales demand and large jobs can be added before they show up in historical usage.")
    st.write("5. The structure is designed to evolve from workbook imports today to ERP/API inputs later.")

    compare_col1, compare_col2 = st.columns(2)
    with compare_col1:
        st.markdown("##### Current State")
        st.write("- Trailing-history-driven material review")
        st.write("- Spreadsheet-based refreshes")
        st.write("- Limited visibility to future risk by copper size")
        st.write("- Outside inventory can overstate real long-term coverage")
    with compare_col2:
        st.markdown("##### Future State")
        st.write("- Item-level copper planning by thickness and width")
        st.write("- Time-phased weekly projection with inbound supply timing")
        st.write("- Future demand, large jobs, and planner actions in one system")
        st.write("- Ready for ERP/API automation when live feeds are available")

    st.markdown("##### Inventory Philosophy")
    st.write("1. Carry enough inventory in house to protect production, but avoid excess slow-mover inventory.")
    st.write("2. Use DC as a controlled buffer, not as false permanent long-term coverage.")
    st.write("3. Buy to protect lead time risk and production continuity, not just to react to past usage.")

    st.markdown("##### Current planning assumptions")
    st.write(f"- Preferred direct mill: {settings.get('preferred_mill', ACTIVE_MILL)}")
    st.write(f"- Active scenario: {settings.get('active_scenario', 'Base')}")
    st.write(f"- DC release date: {settings.get('dc_release_date', '2026-07-31')}")
    st.write(f"- Last imported workbook snapshot: {snapshot.get('imported_at', 'Not loaded')}")


def render_items(plan_rows: list[dict]) -> None:
    if not plan_rows:
        st.info("No item details are available yet.")
        return
    row_map = {row["size"]: row for row in plan_rows}
    selected = st.selectbox("Copper size", sorted(row_map, key=size_sort_key))
    row = row_map[selected]
    st.markdown(
        f"""
        <div class="item-hero">
            <h3>{row['size']}</h3>
            <p>{row['mover_class']} mover | {row['action_bucket']} | Preferred source: {row['recommended_source']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    top = st.columns(4)
    top[0].metric("Forecast / month", f"{row['forecast_monthly_lbs']:,.0f} lbs")
    top[1].metric("Plant available", f"{row['plant_available_lbs']:,.0f} lbs")
    top[2].metric("DC on hand", f"{row['dc_on_hand_lbs']:,.0f} lbs")
    top[3].metric("Net coverage", f"{row['net_coverage_weeks']:.1f} wks")
    bottom = st.columns(4)
    bottom[0].metric("Safety stock", f"{row['safety_stock_lbs']:,.0f} lbs")
    bottom[1].metric("Reorder point", f"{row['reorder_point_lbs']:,.0f} lbs")
    bottom[2].metric("Target stock", f"{row['target_stock_lbs']:,.0f} lbs")
    bottom[3].metric("Recommended qty", f"{row['recommended_order_lbs']:,.0f} lbs")
    if row["override_note"]:
        st.info(f"Planner note: {row['override_note']}")
    st.write(f"Data status: {row.get('data_status', 'Imported')}")
    st.write(f"Future sales demand added: {row['future_sales_monthly_lbs']:,.0f} lbs / month")
    if row["future_sales_months"]:
        st.write(f"Sales months in scenario: {row['future_sales_months']}")
    if row.get("future_confidence_mix"):
        st.write(f"Sales confidence mix: {row['future_confidence_mix']}")
    st.write(f"Large-job demand added: {row.get('large_job_monthly_lbs', 0.0):,.0f} lbs / month")
    st.write(f"Schedule demand added: {row.get('schedule_monthly_lbs', 0.0):,.0f} lbs / month")
    st.write(f"DC target buffer: {row.get('dc_target_lbs', 0.0):,.0f} lbs")
    st.write(f"DC release to ICC on release date: {row.get('dc_over_target_lbs', 0.0):,.0f} lbs")
    if row.get("moq_note"):
        st.write(f"MOQ rule: {row['moq_note']}")
    st.write(f"Order by: {row.get('order_by_date', 'Now')}")
    st.write(f"Expected receipt: {row.get('expected_receipt_date', 'N/A')}")


def render_supply_plan(plan_rows: list[dict]) -> None:
    if not plan_rows:
        st.info("No supply plan yet.")
        return
    rows = [
        {
            "Copper Size": row["size"],
            "Mover": row["mover_class"],
            "Plant Available": round(row["plant_available_lbs"], 0),
            "DC On Hand": round(row["dc_on_hand_lbs"], 0),
            "DC Target": round(row["dc_target_lbs"], 0),
            "DC Release Qty": round(row["dc_over_target_lbs"], 0),
            "Inbound Total": round(row["inbound_total_lbs"], 0),
            "Forecast / Month": round(row["forecast_monthly_lbs"], 0),
            "Current Coverage": round(row["current_coverage_weeks"], 1),
            "Net Coverage": round(row["net_coverage_weeks"], 1),
            "Action": row["action_bucket"],
        }
        for row in plan_rows
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_recommendations(plan_rows: list[dict]) -> None:
    if not plan_rows:
        st.info("No recommendations yet.")
        return
    basket_summary = summarize_order_baskets(plan_rows, load_settings())
    if basket_summary:
        st.markdown("#### Source Order Basket Summary")
        st.caption("MOQ is evaluated at the source order total level, not per individual copper size.")
        st.dataframe(basket_summary, use_container_width=True, hide_index=True)
    filter_value = st.selectbox(
        "Recommendation filter",
        ["All", "Order Now", "Pull From DC", "Excess Risk", "Monitor", "Healthy"],
    )
    rows = [
        {
            "Copper Size": row["size"],
            "Action": row["action_bucket"],
            "Source": row["recommended_source"],
            "Qty (lbs)": round(row["recommended_order_lbs"], 0),
            "Reorder Point": round(row["reorder_point_lbs"], 0),
            "Target Stock": round(row["target_stock_lbs"], 0),
            "Scenario": row["active_scenario"],
            "Order By": row.get("order_by_date", "Now"),
            "Expected Receipt": row.get("expected_receipt_date", "N/A"),
            "Reason": row["recommendation_reason"],
        }
        for row in plan_rows
        if filter_value == "All" or row["action_bucket"] == filter_value
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    if rows:
        st.download_button(
            "Download recommendations as CSV",
            data=rows_to_csv(rows),
            file_name="copper_recommendations.csv",
            mime="text/csv",
        )
        selected_size = st.selectbox(
            "Recommendation detail",
            sorted([row["size"] for row in plan_rows], key=size_sort_key),
            key="recommendation_detail_size",
        )
        selected_row = next(row for row in plan_rows if row["size"] == selected_size)
        st.markdown(
            """
            <div class="section-card">
                <strong>Why this recommendation exists</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(f"- Copper size: {selected_row['size']}")
        st.write(f"- Action: {selected_row['action_bucket']}")
        st.write(f"- Recommended source: {selected_row['recommended_source']}")
        st.write(f"- Recommended quantity: {selected_row['recommended_order_lbs']:,.0f} lbs")
        st.write(f"- Forecast demand: {selected_row['forecast_monthly_lbs']:,.0f} lbs/month")
        st.write(f"- Current coverage: {selected_row['current_coverage_weeks']:.1f} weeks")
        st.write(f"- Net coverage: {selected_row['net_coverage_weeks']:.1f} weeks")
        st.write(f"- Reorder point: {selected_row['reorder_point_lbs']:,.0f} lbs")
        st.write(f"- Target stock: {selected_row['target_stock_lbs']:,.0f} lbs")
        st.write(f"- Order by: {selected_row.get('order_by_date', 'Now')}")
        st.write(f"- Expected receipt: {selected_row.get('expected_receipt_date', 'N/A')}")
        st.write(f"- System reason: {selected_row['recommendation_reason']}")


def render_monthly_po_tab(plan_rows: list[dict], settings: dict) -> None:
    st.markdown("#### Monthly PO Draft")
    if not plan_rows:
        st.info("Load the workbook first to build a monthly PO draft.")
        return
    review_date = next_monthly_review_date(settings)
    st.write(f"Monthly review date: {review_date.strftime('%Y-%m-%d')}")
    st.write("This draft includes items that should be covered in the next monthly order cycle.")
    po_rows = build_monthly_po_rows(plan_rows, settings)
    if not po_rows:
        st.info("No items currently need to be included in the next monthly PO draft.")
        return
    basket_summary = summarize_order_baskets(
        [
            row for row in plan_rows
            if row["size"] in {po_row["Copper Size"] for po_row in po_rows}
        ],
        settings,
    )
    st.markdown("##### Basket Summary")
    st.dataframe(basket_summary, use_container_width=True, hide_index=True)
    st.markdown("##### Draft PO Lines")
    st.dataframe(po_rows, use_container_width=True, hide_index=True)


def render_logic_tab(
    settings: dict,
    plan_rows: list[dict],
    forecast_entries: list[dict],
    schedule_entries: list[dict],
) -> None:
    st.markdown("#### Forecast Logic")
    st.caption("This tab explains how the current planning engine is producing its recommendations.")

    st.markdown("##### Current Planning Flow")
    st.write("1. Import the copper workbook and identify active copper sizes.")
    st.write("2. Use workbook average monthly usage as the base demand signal.")
    st.write("3. Add manual overrides by copper size when planners know demand is changing.")
    st.write("4. Add future demand entries from sales or commercial expectations by scenario.")
    st.write("5. Convert monthly demand into weekly usage.")
    st.write("6. Calculate plant available, DC inventory, and inbound supply.")
    st.write("7. Treat DC stock above the target buffer as temporary release stock that moves to ICC on the release date.")
    st.write("8. Calculate safety stock, reorder point, target stock, and recommended source.")
    st.write("9. Classify each item into `Order Now`, `Pull From DC`, `Monitor`, `Healthy`, or `Excess Risk`.")

    st.markdown("##### Current Formulas")
    st.code(
        "\n".join(
            [
                "forecast_monthly_lbs = base_monthly_lbs + manual_adjustment_lbs + future_sales_monthly_lbs",
                "future_sales_monthly_lbs uses confidence-weighted sales entries by scenario",
                "large_job_monthly_lbs adds large-job demand into the planning horizon",
                "weekly_usage = forecast_monthly_lbs / 4.345",
                "plant_available_lbs = icc_inventory_current_lbs - jobs_pending_lbs",
                "dc_on_hand_lbs = williams_on_hand_lbs + maverick_on_hand_lbs",
                "dc_over_target_lbs = max(0, dc_on_hand_lbs - dc_target_lbs)",
                "inbound_total_lbs = dc_on_order_lbs + mill_on_order_lbs",
                "net_supply_lbs = plant_available_lbs + dc_over_target_lbs + inbound_total_lbs",
                "safety_stock_lbs = weekly_usage * safety_weeks",
                "reorder_point_lbs = weekly_usage * preferred_mill_lead_weeks + safety_stock_lbs",
                "target_stock_lbs = weekly_usage * (preferred_mill_lead_weeks + safety_weeks + monthly_review_cycle)",
                "recommended_order_lbs = max(0, target_stock_lbs - net_supply_lbs)",
                "MOQ is checked at the total source order basket level, not per SKU line",
                "Monthly ordering cadence is assumed; next review cycle is used in PO timing",
            ]
        ),
        language="text",
    )

    st.markdown("##### Current Action Rules")
    st.write("`Pull From DC`: plant available is below about 4 weeks of usage and distribution has stock.")
    st.write("`Order Now`: net supply is below reorder point.")
    st.write("`Excess Risk`: net supply is well above target stock.")
    st.write("`Monitor`: item is above reorder point now but still has a positive suggested buy gap.")
    st.write("`Healthy`: item is inside the current target range.")

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown("##### Live Assumptions")
        st.write(f"Preferred mill: {settings.get('preferred_mill', ACTIVE_MILL)}")
        st.write(f"Future mill: {settings.get('future_mill', FUTURE_MILL)}")
        st.write(f"Active scenario: {settings.get('active_scenario', 'Base')}")
        st.write(f"DC release date: {settings.get('dc_release_date', '2026-07-31')}")
        st.write(f"Monthly review day: {settings.get('monthly_review_day', 1)}")
        st.write("Lead times (weeks):")
        for source_name, weeks in settings.get("source_lead_weeks", {}).items():
            st.write(f"- {source_name}: {weeks}")
    with right_col:
        st.markdown("##### Current State")
        st.write("Safety stock by mover (weeks):")
        for mover_name, weeks in settings.get("safety_weeks_by_mover", {}).items():
            st.write(f"- {mover_name}: {weeks}")
        moq_settings = settings.get("source_moq_lbs", {})
        st.write("MOQ rules:")
        st.write(f"- Direct mill: {number(moq_settings.get('direct_mill', 40000.0)):,.0f} lbs")
        st.write(f"- Distribution: {number(moq_settings.get('distribution', 10000.0)):,.0f} lbs")
        st.write("- MOQ applies to the combined order basket by source, not each individual SKU.")
        st.write("DC target buffers:")
        for mover_name, lbs in settings.get("dc_target_lbs_by_mover", {}).items():
            st.write(f"- {mover_name}: {number(lbs):,.0f} lbs")
        st.write("Sales confidence weights:")
        for confidence, weight in settings.get("confidence_weights", {}).items():
            st.write(f"- {confidence}: {weight}")
        st.write(f"Future demand entries loaded: {len(forecast_entries)}")
        st.write(f"Current schedule lines loaded: {len(schedule_entries)}")
        st.write(f"Items currently in plan: {len(plan_rows)}")

    st.markdown("##### What This Version Does Not Do Yet")
    st.write("`Production schedule demand` is entered manually today, not yet pulled directly from ERP.")
    st.write("`Weighted sales pipeline logic` is not built yet.")
    st.write("`Supplier MOQ, lot size, and price break logic` are not built yet.")
    st.write("`ERP API automation` is not built yet.")


def render_projection_tab(
    plan_rows: list[dict],
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
    settings: dict,
) -> None:
    st.markdown("#### Weekly Projection")
    if not plan_rows:
        st.info("Load your workbook first to build weekly projections.")
        return
    selected_size = st.selectbox("Projection item", sorted([row["size"] for row in plan_rows], key=size_sort_key), key="projection_size")
    selected_row = next(row for row in plan_rows if row["size"] == selected_size)
    weeks = build_weekly_projection(selected_row, forecast_entries, large_job_entries, schedule_entries, settings)
    summary = summarize_projection(weeks)
    summary_cols = st.columns(4)
    summary_cols[0].metric("Active scenario", selected_row["active_scenario"])
    summary_cols[1].metric("Forecast / month", f"{selected_row['forecast_monthly_lbs']:,.0f} lbs")
    summary_cols[2].metric("Stockout timing", summary["stockout_week_label"])
    summary_cols[3].metric("Min projected supply", f"{summary['min_closing_supply_lbs']:,.0f} lbs")
    st.dataframe(
        [
            {
                "Week": week["week_label"],
                "Month": week["month"],
                "Opening Supply": week["opening_supply_lbs"],
                "Inbound": week["inbound_lbs"],
                "Demand": week["demand_lbs"],
                "Closing Supply": week["closing_supply_lbs"],
            }
            for week in weeks
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_exceptions_tab(
    plan_rows: list[dict],
    forecast_entries: list[dict],
    large_job_entries: list[dict],
    schedule_entries: list[dict],
    settings: dict,
) -> None:
    st.markdown("#### Exception Dashboard")
    if not plan_rows:
        st.info("No exceptions to show until the workbook is loaded.")
        return
    exception_rows = build_exception_rows(plan_rows, forecast_entries, large_job_entries, schedule_entries, settings)
    filter_value = st.selectbox(
        "Exception filter",
        ["All", "Stockout <= 4 weeks", "Stockout <= 8 weeks", "Stockout <= 12 weeks", "No stockout in horizon"],
    )
    filtered = [
        row for row in exception_rows if filter_value == "All" or row["Exception"] == filter_value
    ]
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def render_history_tab() -> None:
    st.markdown("#### Import History")
    history_payload = load_json(IMPORT_HISTORY_PATH)
    entries = history_payload.get("entries", []) if isinstance(history_payload, dict) else []
    if not entries:
        st.info("No import history yet.")
        return
    st.dataframe(list(reversed(entries)), use_container_width=True, hide_index=True)


def render_active_snapshot_tab(snapshot: dict) -> None:
    st.markdown("#### Active Snapshot")
    if not snapshot or not snapshot.get("items"):
        st.info("No active workbook snapshot is currently loaded.")
        return
    items = snapshot.get("items", [])
    summary_rows = [
        {"Metric": "Active workbook", "Value": snapshot.get("source_name", "Unknown")},
        {"Metric": "Imported at", "Value": snapshot.get("imported_at", "Unknown")},
        {"Metric": "Copper sizes", "Value": len(items)},
        {"Metric": "Current ICC inventory (lbs)", "Value": round(sum(number(item.get("icc_inventory_current_lbs", 0.0)) for item in items), 0)},
        {"Metric": "Plant available (lbs)", "Value": round(sum(max(0.0, number(item.get("icc_inventory_current_lbs", 0.0)) - number(item.get("jobs_pending_lbs", 0.0))) for item in items), 0)},
        {"Metric": "Total on order (lbs)", "Value": round(sum(number(item.get("total_on_order_lbs", 0.0)) for item in items), 0)},
        {"Metric": "DC on hand (lbs)", "Value": round(sum(number(item.get("williams_on_hand_lbs", 0.0)) + number(item.get("maverick_on_hand_lbs", 0.0)) for item in items), 0)},
        {"Metric": "Adjusted 7-month usage (lbs)", "Value": round(sum(number(item.get("adjusted_usage_7mo_lbs", 0.0)) for item in items), 0)},
        {"Metric": "Placeholder sizes added", "Value": sum(1 for item in items if item.get("data_status") == "Placeholder")},
    ]
    st.dataframe(summary_rows, use_container_width=True, hide_index=True)
    st.caption("This is the single workbook snapshot currently driving the planning recommendations.")


def render_snapshot_compare_tab(snapshot: dict) -> None:
    st.markdown("#### Snapshot Comparison")
    history_payload = load_json(IMPORT_HISTORY_PATH)
    entries = history_payload.get("entries", []) if isinstance(history_payload, dict) else []
    if len(entries) < 2:
        st.info("Import at least two snapshots to compare changes.")
        return
    latest = entries[-1]
    previous = entries[-2]
    compare_rows = [
        {
            "Metric": "Item count",
            "Previous": previous.get("item_count", 0),
            "Latest": latest.get("item_count", 0),
            "Delta": latest.get("item_count", 0) - previous.get("item_count", 0),
        },
        {
            "Metric": "Current inventory lbs",
            "Previous": previous.get("current_inventory_lbs", 0),
            "Latest": latest.get("current_inventory_lbs", 0),
            "Delta": latest.get("current_inventory_lbs", 0) - previous.get("current_inventory_lbs", 0),
        },
        {
            "Metric": "Plant available lbs",
            "Previous": previous.get("plant_available_lbs", 0),
            "Latest": latest.get("plant_available_lbs", 0),
            "Delta": latest.get("plant_available_lbs", 0) - previous.get("plant_available_lbs", 0),
        },
        {
            "Metric": "Mill on order lbs",
            "Previous": previous.get("mill_on_order_lbs", 0),
            "Latest": latest.get("mill_on_order_lbs", 0),
            "Delta": latest.get("mill_on_order_lbs", 0) - previous.get("mill_on_order_lbs", 0),
        },
    ]
    st.write(f"Comparing `{previous.get('imported_at', '')}` to `{latest.get('imported_at', '')}`")
    st.dataframe(compare_rows, use_container_width=True, hide_index=True)


def render_actions_tab(plan_rows: list[dict]) -> None:
    st.markdown("#### Item Ownership and Notes")
    if not plan_rows:
        st.info("Load your workbook before assigning ownership notes.")
        return
    actions_payload = load_json(ACTIONS_PATH)
    actions = actions_payload if isinstance(actions_payload, dict) else {}
    selected_size = st.selectbox("Copper size", sorted([row["size"] for row in plan_rows], key=size_sort_key), key="action_item_size")
    existing = actions.get(selected_size, {})
    with st.form("item_actions_form"):
        owner = st.text_input("Owner", value=existing.get("owner", ""))
        status = st.selectbox(
            "Status",
            ["Open", "Watching", "Ordering", "Covered", "Excess Review"],
            index=["Open", "Watching", "Ordering", "Covered", "Excess Review"].index(existing.get("status", "Open")),
        )
        note = st.text_area("Action note", value=existing.get("note", ""), height=110)
        submitted = st.form_submit_button("Save item action")
    if submitted:
        actions[selected_size] = {
            "owner": owner.strip(),
            "status": status,
            "note": note.strip(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_json(ACTIONS_PATH, actions)
        review_payload = load_json(REVIEW_HISTORY_PATH)
        review_entries = review_payload.get("entries", []) if isinstance(review_payload, dict) else []
        review_entries.append(
            {
                "size": selected_size,
                "owner": owner.strip(),
                "status": status,
                "note": note.strip(),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        save_json(REVIEW_HISTORY_PATH, {"entries": review_entries[-200:]})
        st.success(f"Saved action details for {selected_size}.")
        st.rerun()
    if actions:
        st.dataframe(
            [
                {
                    "Copper Size": size,
                    "Owner": detail.get("owner", ""),
                    "Status": detail.get("status", ""),
                    "Note": detail.get("note", ""),
                    "Updated": detail.get("updated_at", ""),
                }
                for size, detail in actions.items()
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_review_history_tab() -> None:
    st.markdown("#### Review History")
    review_payload = load_json(REVIEW_HISTORY_PATH)
    entries = review_payload.get("entries", []) if isinstance(review_payload, dict) else []
    if not entries:
        st.info("No review history yet.")
        return
    st.dataframe(list(reversed(entries)), use_container_width=True, hide_index=True)


def render_overrides(plan_rows: list[dict], overrides: dict) -> None:
    if not plan_rows:
        st.info("Load data before editing overrides.")
        return
    selected_size = st.selectbox("Copper size to adjust", sorted([row["size"] for row in plan_rows], key=size_sort_key), key="override_size")
    existing = overrides.get(selected_size, {})
    with st.form("override_form"):
        adjustment = st.number_input(
            "Monthly demand adjustment (lbs)",
            value=float(existing.get("manual_adjustment_lbs", 0.0)),
            step=100.0,
        )
        source_override = st.selectbox(
            "Source override",
            ["Auto", ACTIVE_MILL, "Demo Distributor A", "Demo Distributor B", FUTURE_MILL],
            index=["Auto", ACTIVE_MILL, "Demo Distributor A", "Demo Distributor B", FUTURE_MILL].index(
                existing.get("source_override", "Auto")
            ),
        )
        note = st.text_area("Planner note", value=existing.get("note", ""), height=120)
        submitted = st.form_submit_button("Save override")
    if submitted:
        overrides[selected_size] = {
            "manual_adjustment_lbs": adjustment,
            "source_override": source_override,
            "note": note.strip(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_json(OVERRIDES_PATH, overrides)
        st.success(f"Saved override for {selected_size}.")
        st.rerun()
    if overrides:
        st.dataframe(
            [
                {
                    "Copper Size": size,
                    "Monthly Adjustment": row.get("manual_adjustment_lbs", 0),
                    "Source Override": row.get("source_override", "Auto"),
                    "Note": row.get("note", ""),
                    "Updated": row.get("updated_at", ""),
                }
                for size, row in overrides.items()
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_settings(settings: dict) -> None:
    st.markdown("#### Planning Assumptions")
    with st.form("settings_form"):
        preferred_mill = st.selectbox(
            "Preferred direct mill",
            [ACTIVE_MILL, FUTURE_MILL],
            index=[ACTIVE_MILL, FUTURE_MILL].index(settings.get("preferred_mill", ACTIVE_MILL)),
        )
        future_mill = st.selectbox(
            "Future / alternate mill",
            [FUTURE_MILL, ACTIVE_MILL],
            index=[FUTURE_MILL, ACTIVE_MILL].index(settings.get("future_mill", FUTURE_MILL)),
        )
        active_scenario = st.selectbox(
            "Active demand scenario",
            ["Base", "Upside", "Downside"],
            index=["Base", "Upside", "Downside"].index(settings.get("active_scenario", "Base")),
        )
        planning_horizon_weeks = st.number_input(
            "Planning horizon (weeks)",
            min_value=8,
            max_value=52,
            value=int(settings.get("planning_horizon_weeks", 26)),
            step=2,
        )
        monthly_review_day = st.number_input(
            "Monthly review day",
            min_value=1,
            max_value=28,
            value=int(settings.get("monthly_review_day", 1)),
            step=1,
            help="Day of month when copper orders are reviewed and placed.",
        )
        weekly_demand_profile = st.selectbox(
            "Weekly demand profile",
            list(WEEKLY_PROFILES),
            index=list(WEEKLY_PROFILES).index(settings.get("weekly_demand_profile", "Front-loaded")),
            help="Use this to shape how monthly demand is distributed within each month.",
        )
        dc_release_date = st.text_input(
            "DC release date",
            value=settings.get("dc_release_date", "2026-07-31"),
            help="Inventory above the DC target buffer will be treated as releasing into ICC on this date.",
        )
        st.markdown("#### DC Target Buffers (lbs)")
        dc_col1, dc_col2, dc_col3 = st.columns(3)
        fast_dc_target = dc_col1.number_input(
            "Fast movers DC target",
            min_value=0.0,
            value=float(settings.get("dc_target_lbs_by_mover", {}).get("Fast", 3000.0)),
            step=500.0,
        )
        medium_dc_target = dc_col2.number_input(
            "Medium movers DC target",
            min_value=0.0,
            value=float(settings.get("dc_target_lbs_by_mover", {}).get("Medium", 3000.0)),
            step=500.0,
        )
        slow_dc_target = dc_col3.number_input(
            "Slow movers DC target",
            min_value=0.0,
            value=float(settings.get("dc_target_lbs_by_mover", {}).get("Slow", 1000.0)),
            step=500.0,
        )
        st.markdown("#### MOQ Rules (lbs)")
        moq_col1, moq_col2 = st.columns(2)
        direct_mill_moq = moq_col1.number_input(
            "Direct mill MOQ",
            min_value=0.0,
            value=float(settings.get("source_moq_lbs", {}).get("direct_mill", 40000.0)),
            step=1000.0,
        )
        distribution_moq = moq_col2.number_input(
            "Distribution MOQ",
            min_value=0.0,
            value=float(settings.get("source_moq_lbs", {}).get("distribution", 10000.0)),
            step=1000.0,
        )
        st.markdown("#### Sales Confidence Weights")
        conf_col1, conf_col2, conf_col3 = st.columns(3)
        high_weight = conf_col1.number_input(
            "High confidence",
            min_value=0.0,
            max_value=1.5,
            value=float(settings.get("confidence_weights", {}).get("High", 1.0)),
            step=0.1,
        )
        medium_weight = conf_col2.number_input(
            "Medium confidence",
            min_value=0.0,
            max_value=1.5,
            value=float(settings.get("confidence_weights", {}).get("Medium", 0.6)),
            step=0.1,
        )
        low_weight = conf_col3.number_input(
            "Low confidence",
            min_value=0.0,
            max_value=1.5,
            value=float(settings.get("confidence_weights", {}).get("Low", 0.3)),
            step=0.1,
        )
        st.markdown("#### Lead Times (weeks)")
        lead_col1, lead_col2, lead_col3, lead_col4 = st.columns(4)
        tecnofil_weeks = lead_col1.number_input(
            "Demo Mill A",
            value=float(settings["source_lead_weeks"].get("Demo Mill A", 11.0)),
            step=0.5,
        )
        coppr_rod_weeks = lead_col2.number_input(
            "Demo Mill B",
            value=float(settings["source_lead_weeks"].get("Demo Mill B", 9.0)),
            step=0.5,
        )
        williams_weeks = lead_col3.number_input(
            "Demo Distributor A",
            value=float(settings["source_lead_weeks"].get("Demo Distributor A", 13.0)),
            step=0.5,
        )
        maverick_weeks = lead_col4.number_input(
            "Demo Distributor B",
            value=float(settings["source_lead_weeks"].get("Demo Distributor B", 13.0)),
            step=0.5,
        )
        st.markdown("#### Safety Stock by Mover (weeks)")
        safety_col1, safety_col2, safety_col3 = st.columns(3)
        fast_weeks = safety_col1.number_input(
            "Fast movers",
            value=float(settings["safety_weeks_by_mover"].get("Fast", 14.0)),
            step=1.0,
        )
        medium_weeks = safety_col2.number_input(
            "Medium movers",
            value=float(settings["safety_weeks_by_mover"].get("Medium", 10.0)),
            step=1.0,
        )
        slow_weeks = safety_col3.number_input(
            "Slow movers",
            value=float(settings["safety_weeks_by_mover"].get("Slow", 6.0)),
            step=1.0,
        )
        submitted = st.form_submit_button("Save planning settings")
    if submitted:
        save_json(
            SETTINGS_PATH,
            {
                "preferred_mill": preferred_mill,
                "future_mill": future_mill,
                "active_scenario": active_scenario,
                "planning_horizon_weeks": int(planning_horizon_weeks),
                "monthly_review_day": int(monthly_review_day),
                "weekly_demand_profile": weekly_demand_profile,
                "dc_release_date": dc_release_date.strip(),
                "dc_target_lbs_by_mover": {
                    "Fast": fast_dc_target,
                    "Medium": medium_dc_target,
                    "Slow": slow_dc_target,
                },
                "source_moq_lbs": {
                    "direct_mill": direct_mill_moq,
                    "distribution": distribution_moq,
                },
                "confidence_weights": {
                    "High": high_weight,
                    "Medium": medium_weight,
                    "Low": low_weight,
                },
                "source_lead_weeks": {
                    "Demo Mill A": tecnofil_weeks,
                    "Demo Mill B": coppr_rod_weeks,
                    "Demo Distributor A": williams_weeks,
                    "Demo Distributor B": maverick_weeks,
                },
                "safety_weeks_by_mover": {
                    "Fast": fast_weeks,
                    "Medium": medium_weeks,
                    "Slow": slow_weeks,
                },
            },
        )
        st.success("Planning settings saved.")
        st.rerun()


def rows_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        values = []
        for header in headers:
            value = str(row.get(header, ""))
            if "," in value or '"' in value or "\n" in value:
                value = '"' + value.replace('"', '""') + '"'
            values.append(value)
        lines.append(",".join(values))
    return "\n".join(lines)


def render_future_demand(plan_rows: list[dict], forecast_entries: list[dict]) -> None:
    st.markdown("#### Future Demand Plan")
    if not plan_rows:
        st.info("Load your workbook first so the app knows which copper sizes are active.")
        return

    size_options = sorted([row["size"] for row in plan_rows], key=size_sort_key)
    with st.form("future_demand_form"):
        entry_cols = st.columns(5)
        selected_size = entry_cols[0].selectbox("Copper size", size_options)
        scenario = entry_cols[1].selectbox("Scenario", ["Base", "Upside", "Downside"])
        month_date = entry_cols[2].date_input("Month", value=datetime.today().date().replace(day=1))
        monthly_lbs = entry_cols[3].number_input("Monthly lbs", min_value=0.0, step=100.0)
        confidence = entry_cols[4].selectbox("Confidence", ["High", "Medium", "Low"])
        customer = st.text_input("Customer / Program")
        note = st.text_area("Sales note", height=90)
        submitted = st.form_submit_button("Add demand entry")

    entries_payload = {"entries": list(forecast_entries)}
    if submitted:
        month_value = month_date.strftime("%Y-%m")
        replaced = False
        for entry in entries_payload["entries"]:
            if entry["size"] == selected_size and entry["scenario"] == scenario and entry["month"] == month_value:
                entry["monthly_lbs"] = monthly_lbs
                entry["note"] = note.strip()
                entry["confidence"] = confidence
                entry["customer"] = customer.strip()
                replaced = True
                break
        if not replaced:
            entries_payload["entries"].append(
                {
                    "size": selected_size,
                    "scenario": scenario,
                    "month": month_value,
                    "monthly_lbs": monthly_lbs,
                    "note": note.strip(),
                    "confidence": confidence,
                    "customer": customer.strip(),
                }
            )
        save_json(FORECASTS_PATH, entries_payload)
        st.success(f"Saved {scenario} demand for {selected_size} in {month_value}.")
        st.rerun()

    st.caption("These entries represent future sales or commercial demand not visible in history yet.")
    if forecast_entries:
        rows = [
            {
                "Copper Size": entry["size"],
                "Scenario": entry["scenario"],
                "Month": entry["month"],
                "Monthly lbs": entry["monthly_lbs"],
                "Confidence": entry.get("confidence", "High"),
                "Customer / Program": entry.get("customer", ""),
                "Note": entry.get("note", ""),
            }
            for entry in sorted(forecast_entries, key=lambda item: (item["scenario"], item["month"], item["size"]))
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No future sales demand entries have been added yet.")


def render_large_jobs_tab(plan_rows: list[dict], large_job_entries: list[dict]) -> None:
    st.markdown("#### Large Job Plan")
    if not plan_rows:
        st.info("Load your workbook first so active copper sizes are available.")
        return
    size_options = sorted([row["size"] for row in plan_rows], key=size_sort_key)
    with st.form("large_job_form"):
        cols = st.columns(4)
        selected_size = cols[0].selectbox("Copper size", size_options, key="large_job_size")
        month_date = cols[1].date_input("Due month", value=datetime.today().date().replace(day=1), key="large_job_month")
        lbs = cols[2].number_input("Job lbs", min_value=0.0, step=100.0, key="large_job_lbs")
        job_name = cols[3].text_input("Job / Program", key="large_job_name")
        note = st.text_area("Large job note", height=90, key="large_job_note")
        submitted = st.form_submit_button("Add large job")
    payload = {"entries": list(large_job_entries)}
    if submitted:
        payload["entries"].append(
            {
                "size": selected_size,
                "month": month_date.strftime("%Y-%m"),
                "lbs": lbs,
                "job_name": job_name.strip(),
                "note": note.strip(),
            }
        )
        save_json(LARGE_JOBS_PATH, payload)
        st.success(f"Saved large job for {selected_size}.")
        st.rerun()
    if large_job_entries:
        st.dataframe(
            [
                {
                    "Copper Size": entry["size"],
                    "Due Month": entry["month"],
                    "Job lbs": entry["lbs"],
                    "Job / Program": entry.get("job_name", ""),
                    "Note": entry.get("note", ""),
                }
                for entry in large_job_entries
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No large jobs entered yet.")


def render_schedule_tab(plan_rows: list[dict], schedule_entries: list[dict]) -> None:
    st.markdown("#### Current Schedule")
    st.caption("Use this to capture current scheduled demand by copper size. Ship date is set to one day after the want date.")
    if not plan_rows:
        st.info("Load your workbook first so active copper sizes are available.")
        return
    size_options = sorted([row["size"] for row in plan_rows], key=size_sort_key)
    with st.form("schedule_form"):
        cols = st.columns(5)
        job_name = cols[0].text_input("Job / Program")
        customer = cols[1].text_input("Customer")
        selected_size = cols[2].selectbox("Copper size", size_options, key="schedule_size")
        want_date = cols[3].date_input("Want date", value=datetime.today().date(), key="schedule_want_date")
        lbs = cols[4].number_input("Copper lbs", min_value=0.0, step=100.0, key="schedule_lbs")
        auto_ship_date = want_date + timedelta(days=1)
        st.write(f"Calculated ship date: {auto_ship_date.strftime('%Y-%m-%d')}")
        note = st.text_area("Schedule note", height=90, key="schedule_note")
        submitted = st.form_submit_button("Add schedule line")
    payload = {"entries": list(schedule_entries)}
    if submitted:
        payload["entries"].append(
            {
                "job_name": job_name.strip(),
                "customer": customer.strip(),
                "size": selected_size,
                "want_date": want_date.strftime("%Y-%m-%d"),
                "ship_date": auto_ship_date.strftime("%Y-%m-%d"),
                "lbs": lbs,
                "note": note.strip(),
            }
        )
        save_json(SCHEDULE_PATH, payload)
        st.success(f"Saved schedule line for {selected_size}.")
        st.rerun()
    if schedule_entries:
        total_lbs = sum(number(entry.get("lbs", 0.0)) for entry in schedule_entries)
        upcoming_ship = min((entry.get("ship_date", "") for entry in schedule_entries if entry.get("ship_date")), default="N/A")
        summary_cols = st.columns(3)
        summary_cols[0].metric("Schedule lines", len(schedule_entries))
        summary_cols[1].metric("Scheduled copper", f"{total_lbs:,.0f} lbs")
        summary_cols[2].metric("Earliest ship date", upcoming_ship)
        st.dataframe(
            [
                {
                    "Job / Program": entry.get("job_name", ""),
                    "Customer": entry.get("customer", ""),
                    "Copper Size": entry["size"],
                    "Want Date": entry["want_date"],
                    "Ship Date": entry.get("ship_date", ""),
                    "Copper lbs": entry["lbs"],
                    "Note": entry.get("note", ""),
                }
                for entry in sorted(schedule_entries, key=lambda item: (item["want_date"], item["size"]))
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No current schedule demand has been entered yet.")


def main() -> None:
    inject_styles()
    st.warning("DEMONSTRATION ONLY — fictional data. Changes stay in this browser session. No real orders, emails, imports, or external synchronization.")
    ensure_local_snapshot_exists()
    snapshot = normalize_snapshot(load_json(STATE_PATH))
    save_json(STATE_PATH, snapshot)
    overrides = load_json(OVERRIDES_PATH)
    settings = load_settings()
    forecast_entries = normalize_forecast_entries(load_json(FORECASTS_PATH))
    large_job_entries = normalize_large_job_entries(load_json(LARGE_JOBS_PATH))
    schedule_entries = normalize_schedule_entries(load_json(SCHEDULE_PATH))
    plan_rows = build_plan(snapshot, overrides, settings, forecast_entries, large_job_entries, schedule_entries)
    render_hero(snapshot, plan_rows)
    summary_tab, active_snapshot_tab, dashboard_tab, monthly_po_tab, items_tab, projection_tab, exceptions_tab, compare_tab, supply_tab, reorder_tab, logic_tab, future_tab, large_jobs_tab, schedule_tab, actions_tab, review_tab, overrides_tab, settings_tab, history_tab = st.tabs(
        [
            "Executive Summary",
            "Active Snapshot",
            "Dashboard",
            "Monthly PO Draft",
            "Copper Items",
            "Weekly Projection",
            "Exceptions",
            "Snapshot Compare",
            "Supply Plan",
            "Reorder Recommendations",
            "Logic",
            "Future Demand Plan",
            "Large Jobs",
            "Current Schedule",
            "Item Actions",
            "Review History",
            "Manual Forecast Overrides",
            "Planning Settings",
            "Import History",
        ]
    )
    with summary_tab:
        render_executive_summary(plan_rows, snapshot, settings)
    with active_snapshot_tab:
        render_active_snapshot_tab(snapshot)
    with dashboard_tab:
        render_dashboard(plan_rows, snapshot, settings)
    with monthly_po_tab:
        render_monthly_po_tab(plan_rows, settings)
    with items_tab:
        render_items(plan_rows)
    with projection_tab:
        render_projection_tab(plan_rows, forecast_entries, large_job_entries, schedule_entries, settings)
    with exceptions_tab:
        render_exceptions_tab(plan_rows, forecast_entries, large_job_entries, schedule_entries, settings)
    with compare_tab:
        render_snapshot_compare_tab(snapshot)
    with supply_tab:
        render_supply_plan(plan_rows)
    with reorder_tab:
        render_recommendations(plan_rows)
    with logic_tab:
        render_logic_tab(settings, plan_rows, forecast_entries, schedule_entries)
    with future_tab:
        render_future_demand(plan_rows, forecast_entries)
    with large_jobs_tab:
        render_large_jobs_tab(plan_rows, large_job_entries)
    with schedule_tab:
        render_schedule_tab(plan_rows, schedule_entries)
    with actions_tab:
        render_actions_tab(plan_rows)
    with review_tab:
        render_review_history_tab()
    with overrides_tab:
        render_overrides(plan_rows, overrides)
    with settings_tab:
        render_settings(settings)
    with history_tab:
        render_history_tab()


if __name__ == "__main__":
    main()
