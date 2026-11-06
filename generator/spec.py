"""Fixed format of cases.xlsx (Iteration 1, Section 3) and the size ranges per tier.

Everything in this file is copied from the Iteration 1 document, so the rest of the
generator never hard-codes a sheet name, a header or a range.
"""

# The 20 sheets, in the required order, with their exact headers.
SHEETS = [
    ("cases", ["case_id", "group_seed", "case_no", "tier", "scenario", "capacity",
               "target_0", "target_1", "target_2", "edit_bound", "tour_length",
               "sensor_nodes", "sensor_k", "safety_vars", "rations_target"]),
    ("crates", ["case_id", "crate_id", "cat", "weight", "value", "expiry", "serial"]),
    ("locations", ["case_id", "loc_id", "type", "penalty"]),
    ("roads", ["case_id", "road_no", "u", "v", "minutes", "cable"]),
    ("waves", ["case_id", "wave_no", "road_no"]),
    ("radio_log", ["case_id", "part", "text"]),
    ("radio_patterns", ["case_id", "pattern_no", "pattern", "count"]),
    ("radio_reports", ["case_id", "report_a", "report_b"]),
    ("windows", ["case_id", "window_id", "start", "finish", "value"]),
    ("incidents", ["case_id", "alarm_id", "tick", "priority"]),
    ("sites", ["case_id", "site_no", "x", "y"]),
    ("tour", ["case_id", "step", "site_no"]),
    ("pipeline_dims", ["case_id", "idx", "dim"]),
    ("drum_prices", ["case_id", "length", "price"]),
    ("sensor_edges", ["case_id", "u", "v"]),
    ("sensor_cover", ["case_id", "node"]),
    ("safety_rules", ["case_id", "rule_no", "lit_1", "lit_2", "lit_3"]),
    ("safety_planted", ["case_id", "switch", "value"]),
    ("rations", ["case_id", "item", "value", "planted"]),
    ("claims", ["case_id", "cargo_opt", "window_count_opt", "window_value_opt",
                "drum_opt", "tour_opt", "cover_min"]),
]
SHEET_NAMES = [name for name, _ in SHEETS]
HEADERS = dict(SHEETS)

# Ranges by tier (inclusive). Tier X uses tier L unless a trap overrides it.
RANGES = {
    "S": dict(crates=(8, 20), locations=(6, 12), waves=(2, 5), log=(200, 500),
              report=(10, 30), windows=(8, 20), alarms=(10, 40), sites=(5, 9),
              stages=(4, 8), drum=(5, 14), sensors=(6, 14), safety_vars=(6, 15),
              rations=(8, 20)),
    "M": dict(crates=(40, 200), locations=(30, 150), waves=(2, 5), log=(2000, 10000),
              report=(30, 150), windows=(50, 300), alarms=(200, 1000), sites=(10, 16),
              stages=(15, 60), drum=(40, 200), sensors=(20, 40), safety_vars=(20, 50),
              rations=(24, 40)),
    "L": dict(crates=(500, 1500), locations=(500, 2000), waves=(2, 5), log=(20000, 100000),
              report=(200, 1000), windows=(1000, 3000), alarms=(2000, 5000), sites=(200, 500),
              stages=(100, 300), drum=(500, 2000), sensors=(100, 400), safety_vars=(20, 50),
              rations=(50, 100)),
}

# Size overrides fixed by the trap rules (Section 2).
TRAP_OVERRIDES = {
    46: {"crates": (1500, 3000)},
    47: {"crates": (12, 60)},
    48: {"locations": (1500, 3000)},
    49: {"log": (50000, 100000)},
}

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"   # 38 symbols
PATTERN_LENGTHS = (2, 4, 8, 12, 20, 40)
PENALTIES = (0, 1, 2, 4, 6)
CELL_LIMIT = 10000          # max symbols in one radio_log cell
DAY_MINUTES = 1440

CAT_FOOD, CAT_WATER, CAT_MEDICINE, CAT_TOOL, CAT_RARE = range(5)


def ranges_for(case_no, tier):
    """Size ranges for one case: tier ranges plus any trap override."""
    base = dict(RANGES["L" if tier == "X" else tier])
    base.update(TRAP_OVERRIDES.get(case_no, {}))
    return base
