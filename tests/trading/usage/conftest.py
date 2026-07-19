"""Keep standalone Trading usage scripts out of direct pytest collection."""

collect_ignore = [
    "01_contracts.py",
    "02_state.py",
    "03_validation.py",
    "04_routing.py",
    "05_reconciliation.py",
    "06_monitoring.py",
    "07_live.py",
    "08_actions.py",
    "09_reporting.py",
]
