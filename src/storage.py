import json
from datetime import datetime

def load_approved(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_approved(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def approve_ticker(approved: dict, ticker: str, note: str="") -> dict:
    approved = dict(approved)
    approved[ticker] = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "note": note or ""
    }
    return approved

def unapprove_ticker(approved: dict, ticker: str) -> dict:
    approved = dict(approved)
    approved.pop(ticker, None)
    return approved
