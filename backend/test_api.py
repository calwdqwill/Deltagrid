import urllib.request
import json

BASE = "http://127.0.0.1:8000/api/v1"

def request(path, method="GET", data=None, token=None):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method=method)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, json.loads(body) if body else {}

# Register
status, auth = request("/auth/register", "POST", {"email":"paper@test.com","password":"password123"})
if status != 200:
    status, auth = request("/auth/login", "POST", {"email":"paper@test.com","password":"password123"})

token = auth.get("data", {}).get("access_token")
print("Auth OK, token:", token[:20] + "..." if token else "NONE")

# Create account
status, account = request("/paper/accounts", "POST", {"name":"Test Account","initial_balance":5000}, token)
print("Account:", status, account.get("data", {}).get("id"), "balance:", account.get("data", {}).get("current_balance"))

acc_id = account.get("data", {}).get("id")

# Create trade
status, trade = request(f"/paper/accounts/{acc_id}/trades", "POST", {
    "strategy": "basis",
    "instrument_id": "bitcoin",
    "side": "buy",
    "entry_price": 67000,
    "quantity": 0.05
}, token)
print("Trade:", status, trade.get("data", {}).get("id"), "status:", trade.get("data", {}).get("status"))

trade_id = trade.get("data", {}).get("id")

# Close trade
status, closed = request(f"/paper/accounts/{acc_id}/trades/{trade_id}/close?exit_price=68000", "POST", {}, token)
print("Closed:", status, "PnL:", closed.get("data", {}).get("pnl"))

# Portfolio
status, port = request(f"/paper/accounts/{acc_id}/portfolio", token=token)
print("Portfolio:", status, "balance:", port.get("data", {}).get("current_balance"), "pnl:", port.get("data", {}).get("total_pnl"))

# Performance
status, perf = request(f"/performance/accounts/{acc_id}", token=token)
print("Performance:", status, "win_rate:", perf.get("data", {}).get("win_rate", {}).get("win_rate_pct"))
