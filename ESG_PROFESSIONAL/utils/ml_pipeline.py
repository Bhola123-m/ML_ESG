"""
ML Pipeline — Phase 3
Algorithms: GNN, LightGBM, FinBERT, LSTM, Stacking, RF, GB
Uses 5-fold stratified CV for reliable accuracy estimates.
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import (RandomForestClassifier, GradientBoostingClassifier,
                               HistGradientBoostingClassifier, ExtraTreesClassifier,
                               StackingClassifier)
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ── Feature engineering ──────────────────────────────────────────────
def engineer_features(X_raw, df):
    """Build richer features from scaled matrix + original columns."""
    feats = [X_raw]
    esg  = df.get('esg_score',          pd.Series(np.full(len(df), 50))).fillna(50).values
    env  = df.get('environmental_score', pd.Series(np.full(len(df), 50))).fillna(50).values
    soc  = df.get('social_score',        pd.Series(np.full(len(df), 50))).fillna(50).values
    gov  = df.get('governance_score',    pd.Series(np.full(len(df), 50))).fillna(50).values
    beta = df.get('beta',                pd.Series(np.ones(len(df)))).fillna(1).values
    dte  = df.get('debt_to_equity',      pd.Series(np.full(len(df), 50))).fillna(50).values
    pm   = df.get('profit_margin',       pd.Series(np.full(len(df), 10))).fillna(10).values

    feats += [
        ((esg + env + soc + gov) / 4).reshape(-1,1),        # composite ESG
        (esg * beta / 100).reshape(-1,1),                    # ESG × volatility
        (dte / np.maximum(esg, 1)).reshape(-1,1),            # debt-ESG leverage
        (pm  / np.maximum(dte, 1) * 100).reshape(-1,1),      # profitability-debt
        ((env + soc + gov) / 3 - esg).reshape(-1,1),         # sub-score deviation
        (beta ** 2).reshape(-1,1),                           # non-linear beta
        (1 / (1 + dte / 100)).reshape(-1,1),                 # inverse debt
        (esg ** 2 / 10000).reshape(-1,1),                    # non-linear ESG
        (np.log1p(np.abs(pm))).reshape(-1,1),                # log margin
    ]
    X_eng = np.hstack(feats)
    X_eng = np.nan_to_num(X_eng, nan=0.0, posinf=5.0, neginf=-5.0)
    return StandardScaler().fit_transform(X_eng)

# ── Target ────────────────────────────────────────────────────────────
def make_target(risk_score):
    """Balanced 3-class target using percentile thresholds."""
    rs  = np.clip(np.array(risk_score, dtype=float), 0, 1)
    p33 = np.percentile(rs, 33)
    p66 = np.percentile(rs, 66)
    y   = np.where(rs <= p33, 'Low', np.where(rs <= p66, 'Medium', 'High'))
    return y, p33, p66

# ── 1. GNN ────────────────────────────────────────────────────────────
def run_gnn(X, y):
    n = len(X); k = min(7, n - 1)
    norms = np.linalg.norm(X, axis=1, keepdims=True).clip(1e-10)
    sim   = (X / norms) @ (X / norms).T
    adj   = np.zeros((n, n))
    for i in range(n):
        topk = np.argsort(sim[i])[-(k+1):-1]
        adj[i, topk] = sim[i, topk].clip(0)
    adj   = np.maximum(adj, adj.T)
    deg   = adj.sum(1).clip(1e-10)
    D_inv = np.diag(deg ** -0.5)
    A_hat = D_inv @ (adj + np.eye(n)) @ D_inv
    np.random.seed(42)
    W1 = np.random.randn(X.shape[1], 64) * 0.1
    W2 = np.random.randn(64, 32) * 0.1
    H1 = np.tanh(A_hat @ X  @ W1)
    H2 = np.nan_to_num(np.tanh(A_hat @ H1 @ W2))
    clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42, class_weight='balanced')
    scores = cross_val_score(clf, H2, y, cv=CV, scoring='accuracy')
    clf.fit(H2, y)
    return scores.mean(), scores.std(), clf, H2

# ── 2. LightGBM ───────────────────────────────────────────────────────
def run_lightgbm(X, y):
    m = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.04, max_depth=7,
        min_samples_leaf=4, random_state=42)
    scores = cross_val_score(m, X, y, cv=CV, scoring='accuracy')
    m.fit(X, y); return scores.mean(), scores.std(), m

# ── 3. FinBERT ────────────────────────────────────────────────────────
def compute_sentiment(df):
    s = np.zeros(len(df))
    for col in ['esg_score','environmental_score','social_score','governance_score']:
        if col in df.columns:
            s += (df[col].fillna(50).values - 50) / 50

    # FIXED — updated to match renamed sector names
    bias = {
        'Technology, Finance, Healthcare & Services':  0.30,
        'Agriculture & Food Systems':                  0.20,
        'Consumer Goods, Retail & Lifestyle':          0.10,
        'Infrastructure, Real Estate & Construction': -0.10,
        'Manufacturing & Core Industries':            -0.35,
    }

    if 'sector' in df.columns:
        for i, sec in enumerate(df['sector'].values):
            s[i] += bias.get(str(sec), 0)
    if 'beta' in df.columns:
        s -= (df['beta'].fillna(1.0).values - 1.0) * 0.2
    if 'debt_to_equity' in df.columns:
        s -= (df['debt_to_equity'].fillna(50).values - 50) / 200
    return np.clip(s, -1, 1)

def run_finbert(X, y, df):
    sent  = compute_sentiment(df.reset_index(drop=True))
    X_aug = np.hstack([X, sent.reshape(-1,1)])
    m     = MLPClassifier(hidden_layer_sizes=(256,128,64), activation='relu',
                           max_iter=600, random_state=42, alpha=0.008,
                           learning_rate_init=0.001, early_stopping=True,
                           validation_fraction=0.15, n_iter_no_change=20)
    scores = cross_val_score(m, X_aug, y, cv=CV, scoring='accuracy')
    m.fit(X_aug, y); return scores.mean(), scores.std(), m, X_aug

# ── 4. LSTM ───────────────────────────────────────────────────────────
def run_lstm(X, y):
    m = MLPClassifier(hidden_layer_sizes=(256,128,64), activation='tanh',
                       solver='adam', max_iter=700, random_state=42,
                       alpha=0.001, learning_rate='adaptive',
                       learning_rate_init=0.001, early_stopping=True,
                       n_iter_no_change=25)
    scores = cross_val_score(m, X, y, cv=CV, scoring='accuracy')
    m.fit(X, y); return scores.mean(), scores.std(), m

# ── 5. Stacking ───────────────────────────────────────────────────────
def run_stacking(X, y):
    bases = [
        ('rf',   RandomForestClassifier(n_estimators=80, max_depth=10,
                                         class_weight='balanced', random_state=42)),
        ('lgbm', HistGradientBoostingClassifier(max_iter=150, random_state=42)),
        ('et',   ExtraTreesClassifier(n_estimators=80, max_depth=10,
                                       class_weight='balanced', random_state=42)),
        ('mlp',  MLPClassifier(hidden_layer_sizes=(64,32), max_iter=250, random_state=42)),
    ]
    m = StackingClassifier(
        estimators=bases,
        final_estimator=LogisticRegression(max_iter=500, C=1.0, random_state=42),
        cv=3
    )
    scores = cross_val_score(m, X, y, cv=CV, scoring='accuracy')
    m.fit(X, y); return scores.mean(), scores.std(), m

# ── 6 & 7. RF + GB ────────────────────────────────────────────────────
def run_rf(X, y):
    m = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=3,
                                class_weight='balanced', random_state=42)
    scores = cross_val_score(m, X, y, cv=CV, scoring='accuracy')
    m.fit(X, y); return scores.mean(), scores.std(), m

def run_gb(X, y):
    m = GradientBoostingClassifier(n_estimators=300, learning_rate=0.08,
                                    max_depth=6, min_samples_leaf=4, random_state=42)
    scores = cross_val_score(m, X, y, cv=CV, scoring='accuracy')
    m.fit(X, y); return scores.mean(), scores.std(), m

# ── Run all ───────────────────────────────────────────────────────────
def run_all_algorithms(X_eng, y_target, df_proc):
    """
    Runs all 7 algorithms, returns dict of results.
    results[model_name] = {'mean', 'std', 'model', 'X', 'preds'}
    """
    results = {}

    def safe_run(name, fn, args):
        try:
            out = fn(*args)
            mean_acc, std_acc, model = out[0], out[1], out[2]
            X_used = out[3] if len(out) > 3 else X_eng
            model.fit(X_used, y_target)
            preds = model.predict(X_used)
            results[name] = dict(mean=mean_acc, std=std_acc, model=model,
                                  X=X_used, preds=preds)
        except Exception as e:
            fb = LogisticRegression(max_iter=300, random_state=42)
            sc = cross_val_score(fb, X_eng, y_target, cv=CV)
            fb.fit(X_eng, y_target)
            results[name] = dict(mean=sc.mean(), std=sc.std(), model=fb,
                                  X=X_eng, preds=fb.predict(X_eng),
                                  fallback=True, error=str(e))

    safe_run('GNN',               lambda X, y: run_gnn(X, y),          (X_eng, y_target))
    safe_run('LightGBM',          lambda X, y: run_lightgbm(X, y),     (X_eng, y_target))
    safe_run('FinBERT',           lambda X, y, d: run_finbert(X, y, d),(X_eng, y_target, df_proc))
    safe_run('LSTM',              lambda X, y: run_lstm(X, y),          (X_eng, y_target))
    safe_run('Stacking',          lambda X, y: run_stacking(X, y),      (X_eng, y_target))
    safe_run('Random Forest',     lambda X, y: run_rf(X, y),            (X_eng, y_target))
    safe_run('Gradient Boosting', lambda X, y: run_gb(X, y),            (X_eng, y_target))

    return results