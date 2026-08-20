"""Project paths, constants, and synthetic dataset labels.

All definitions in this file are for a synthetic, illustrative, non-production
portfolio project. They do not represent a real healthcare organisation.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
PROCESSED_DIR = DATA_DIR / "processed"
RULES_DIR = ROOT / "rules"
REPORTS_DIR = ROOT / "reports"
DASHBOARD_DIR = ROOT / "dashboard"
DOCS_DIR = ROOT / "docs"

SEED = 42
AS_OF_DATE = "2026-08-20"

DATASET_CLASSIFICATION = "Synthetic / Illustrative / Non-production"
DATASET_NOTICE = (
    "SYNTHETIC DATASET. Illustrative and non-production. "
    "Contains no real patient, provider, or facility information."
)

GENDER_VALUE_SET = ("Female", "Male", "Unknown")
ENCOUNTER_TYPE_VALUE_SET = ("Emergency", "Inpatient", "Outpatient", "Virtual")

PATIENT_ID_PATTERN = r"^PAT-\d{6}$"
PROVIDER_ID_PATTERN = r"^PRV-\d{3}$"
FACILITY_ID_PATTERN = r"^FAC-\d{3}$"
ENCOUNTER_ID_PATTERN = r"^ENC-\d{7}$"

UNKNOWN_FACILITY_ID = "FAC-UNK"
UNKNOWN_PROVIDER_ID = "PRV-UNK"
UNKNOWN_PATIENT_ID = "PAT-UNK"

RAW_TABLES = ("facilities", "providers", "patients", "encounters")

RULE_CATALOG_PATH = RULES_DIR / "dq_rules.yaml"
CDE_CATALOG_PATH = RULES_DIR / "cde_catalog.yaml"
