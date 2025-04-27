import json
import numpy as np
import pandas as pd
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
STATE_DIR            = Path("/data/state")
WEIGHTS_FILE         = STATE_DIR / "metric_weights.json"
CURVE_FILE           = STATE_DIR / "equity_curve.csv"
REWARD_STATE         = STATE_DIR / "reward_state.json"

# hyper-parameters
ETA_BASE             = 0.05    # base learning rate
ALPHA                = 0.9     # smoothing old vs new
MAX_WINDOW           = 20      # cap expanding window
CYCLES_PER_UPDATE    = 4       # run every 4 intraday cycles (~1 hr)
BETA_ENTROPY         = 0.01    # entropy regularization strength
ETA_TURNOVER         = 0.1     # turnover penalty strength
# ────────────────────────────────────────────────────────────────────────────────

def load_json(f, default):
    return json.loads(f.read_text()) if f.exists() else default

def save_json(f, obj):
    f.write_text(json.dumps(obj, indent=2))

def load_weights():
    return np.array(load_json(WEIGHTS_FILE, [1.0]))

def save_weights(w):
    WEIGHTS_FILE.write_text(json.dumps(w.tolist(), indent=2))

def compute_returns(window):
    df = pd.read_csv(CURVE_FILE)
    df["ret"] = df["equity"].pct_change().fillna(0)
    return df["ret"].tail(window).values

def compute_reward(returns):
    μ = returns.mean()
    σ = returns.std()
    return μ/σ if σ > 0 else 0.0

def entropy_gradient(w):
    # ∂/∂w [ -Σ w ln w ] = -(1 + ln w)
    return -(1 + np.log(np.clip(w, 1e-12, None)))

def update_weights_throttled():
    # 1. load state & weights
    w_old = load_weights()
    state = load_json(REWARD_STATE, {"intervals": 0})
    state["intervals"] += 1
    intervals = state["intervals"]
    save_json(REWARD_STATE, state)

    # 2. throttle: only run every N cycles
    if intervals % CYCLES_PER_UPDATE != 0:
        return {"skipped": True, "intervals": intervals}

    # 3. compute windowed returns
    window = min(intervals, MAX_WINDOW)
    rets   = compute_returns(window)
    r      = compute_reward(rets)

    # 4. entropy term
    grad_ent = BETA_ENTROPY * entropy_gradient(w_old)
    # 5. turnover penalty
    turn_pen = -ETA_TURNOVER * (w_old - w_old)  # placeholder; if you store prev_w, use it here

    # 6. policy-gradient step
    w_tent = w_old + ETA_BASE * r + grad_ent + turn_pen
    w_tent = np.clip(w_tent, 0, None)

    # 7. smooth and renormalize
    w_new = ALPHA * w_old + (1 - ALPHA) * w_tent
    w_new /= w_new.sum()

    # 8. persist
    save_weights(w_new)
    return {
        "skipped": False,
        "intervals": intervals,
        "window": window,
        "reward": r,
        "old_weights": w_old.tolist(),
        "new_weights": w_new.tolist()
    }

if __name__=="__main__":
    info = update_weights_throttled()
    print(json.dumps(info, indent=2))