"""Settings for the CMG data pipeline."""

# The SEC asks every automated client to identify itself with a name and a contact email.
# Requests without it are blocked.
# Do NOT type your email here (this file is public on GitHub). Instead create
# cmg_pipeline/config_local.py containing one line:
#     USER_AGENT = "Your Name your.email@example.com"
# config_local.py is listed in .gitignore, so it never gets uploaded.
USER_AGENT = "Your Name your.email@example.com"
try:
    from .config_local import USER_AGENT  # noqa: F401  (your private copy overrides the placeholder)
except ImportError:
    pass

# Target company first, then peers. CIKs are SEC company identifiers
# (looked up automatically if left as None).
COMPANIES = [
    {"ticker": "CMG",  "cik": 1058090, "name": "Chipotle (target)"},
    {"ticker": "MCD",  "cik": 63908,   "name": "McDonald's"},
    {"ticker": "YUM",  "cik": 1041061, "name": "Yum! Brands"},
    {"ticker": "DPZ",  "cik": 1286681, "name": "Domino's Pizza"},
    {"ticker": "WING", "cik": 1636222, "name": "Wingstop"},
    {"ticker": "SHAK", "cik": 1620533, "name": "Shake Shack"},
    {"ticker": "CAVA", "cik": None,    "name": "CAVA Group"},
    {"ticker": "SG",   "cik": None,    "name": "Sweetgreen"},
]

# XBRL tags tried in order (companies label the same item differently).
TAGS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
    "ebit": ["OperatingIncomeLoss"],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
           "DepreciationAmortizationAndAccretionNet", "Depreciation"],
    "eps_diluted": ["EarningsPerShareDiluted"],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "st_investments": ["MarketableSecuritiesCurrent", "ShortTermInvestments", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
    "lt_investments": ["LongTermInvestments", "MarketableSecuritiesNoncurrent"],
    "debt_total": ["LongTermDebt", "DebtLongtermAndShorttermCombinedAmount"],
    "debt_noncurrent": ["LongTermDebtNoncurrent"],
    "debt_current": ["LongTermDebtCurrent", "DebtCurrent"],
    "short_borrowings": ["ShortTermBorrowings"],
    "lease_total": ["OperatingLeaseLiability"],
    "lease_current": ["OperatingLeaseLiabilityCurrent"],
    "lease_noncurrent": ["OperatingLeaseLiabilityNoncurrent"],
    "finance_lease": ["FinanceLeaseLiability"],
    "food_cost": ["CostDirectMaterial"],
    "labor_cost": ["CostDirectLabor"],
}

# Excel model to update: the model at the root of this repo (one level above data-pipeline/).
import os as _os
_PIPELINE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
MODEL_PATH = _os.path.join(_os.path.dirname(_PIPELINE_DIR), "CMG_Historicals_Assumptions.xlsx")
OUTPUT_DIR = _os.path.join(_PIPELINE_DIR, "output")
