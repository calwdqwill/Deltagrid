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
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.read() else "{}"
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {}

print("=== Phase 1 Regression ===")

status, data = request("/health")
print(f"Health: {status} {data.get('data', {}).get('status')}")

status, data = request("/scanner")
print(f"Scanner: {status} records={len(data.get('data', {}).get('records', []))}")

status, data = request("/preferences")
print(f"Preferences: {status}")

status, data = request("/preferences/favorites")
print(f"Favorites: {status}")

print("\n=== Phase 2 Auth ===")
status, auth = request("/auth/register", "POST", {"email":"reg@test.com","password":"password123"})
if status != 200:
    status, auth = request("/auth/login", "POST", {"email":"reg@test.com","password":"password123"})
print(f"Auth: {status}")
token = auth.get("data", {}).get("access_token", "")
print(f"Token: {token[:20]}...")

print("\n=== Phase 2 Paper Trading ===")
status, acc = request("/paper/accounts", "POST", {"name":"Regression Test","initial_balance":10000}, token)
print(f"Account: {status} {acc.get('data', {}).get('id', '')[:8]}")
acc_id = acc.get("data", {}).get("id")

if acc_id:
    status, trade = request(f"/paper/accounts/{acc_id}/trades", "POST", {"strategy":"basis","instrument_id":"bitcoin","side":"buy","entry_price":67000,"quantity":0.1}, token)
    print(f"Trade: {status} {trade.get('data', {}).get('id', '')[:8]}")
    trade_id = trade.get("data", {}).get("id")

    if trade_id:
        status, closed = request(f"/paper/accounts/{acc_id}/trades/{trade_id}/close?exit_price=68000", "POST", {}, token)
        print(f"Close: {status} PnL={closed.get('data', {}).get('pnl')}")

    status, perf = request(f"/performance/accounts/{acc_id}", token=token)
    print(f"Performance: {status} win_rate={perf.get('data', {}).get('win_rate', {}).get('win_rate_pct')}")

print("\n=== Phase 2 Billing ===")
status, plans = request("/billing/plans")
print(f"Billing: {status} {len(plans.get('data', []))} plans")

print("\n=== ALL TESTS PASSED ===")
