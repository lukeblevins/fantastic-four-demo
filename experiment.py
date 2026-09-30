"""Deterministic simulated sampling experiment. No patient images or clinical model."""

import math
import random
import statistics
from functools import lru_cache

WIDTH, HEIGHT = 24, 16


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-35, min(35, x))))


def mean_features(patches):
    return [statistics.fmean(p[j] for p in patches) for j in range(3)]


def make_case(index, seed):
    rng = random.Random(seed * 10000 + index)
    label = rng.randrange(2)
    strength = rng.uniform(0.15, 1.4)
    offset = rng.gauss(0, 0.6)
    phase = rng.uniform(0, math.tau)
    variation = rng.uniform(0.2, 2.8)
    patches = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            signal = (2 * label - 1) * strength + offset
            signal += (
                variation
                * math.sin(x / WIDTH * math.tau + phase)
                * math.cos(y / HEIGHT * math.pi)
            )
            signal += rng.gauss(0, 0.9)
            # A fixed toy feature map stands in for cached encoder output.
            patches.append(
                [math.tanh(signal), math.tanh(signal / 2), rng.gauss(0, 0.7)]
            )
    return {"id": f"SIM-{index:03d}", "label": label, "patches": patches}


def fit(cases):
    rows = [(mean_features(c["patches"]), c["label"]) for c in cases]
    weights = [0.0, 0.0, 0.0]
    bias = 0.0
    for _ in range(500):
        grad = [0.0, 0.0, 0.0]
        db = 0.0
        for x, y in rows:
            error = sigmoid(sum(a * b for a, b in zip(weights, x)) + bias) - y
            db += error
            for j in range(3):
                grad[j] += error * x[j]
        for j in range(3):
            weights[j] -= 0.3 * (grad[j] / len(rows) + 0.015 * weights[j])
        bias -= 0.3 * db / len(rows)
    return weights, bias


def predict(features, model):
    return sigmoid(sum(a * b for a, b in zip(features, model[0])) + model[1])


def sample_indices(budget, method, rng):
    if method == "random":
        return rng.sample(range(WIDTH * HEIGHT), budget)
    # Equal-area strata: one randomly selected patch per spatial cell.
    columns = 4 if budget == 16 else 8
    rows = budget // columns
    return [
        rng.randrange(c * WIDTH // columns, (c + 1) * WIDTH // columns)
        + WIDTH * rng.randrange(r * HEIGHT // rows, (r + 1) * HEIGHT // rows)
        for r in range(rows)
        for c in range(columns)
    ]


@lru_cache(maxsize=8)
def cohort(seed):
    cases = [make_case(i, seed) for i in range(240)]
    order = list(range(240))
    random.Random(seed).shuffle(order)
    train, validation, test = (
        [cases[i] for i in order[a:b]] for a, b in [(0, 120), (120, 160), (160, 240)]
    )
    model = fit(train)
    # Select a classification threshold on validation patients only.
    vp = [(predict(mean_features(c["patches"]), model), c["label"]) for c in validation]
    candidates = [i / 100 for i in range(25, 76)]
    threshold = min(
        candidates, key=lambda t: (sum((p >= t) != y for p, y in vp), abs(t - 0.5))
    )
    return train, validation, test, model, threshold


def summarize(rows, threshold):
    errors = [int((r["mean"] >= threshold) != r["label"]) for r in rows]
    n = len(rows)
    accuracy = 1 - statistics.fmean(errors)
    z = 1.96
    denom = 1 + z * z / n
    center = (accuracy + z * z / (2 * n)) / denom
    radius = z * math.sqrt(accuracy * (1 - accuracy) / n + z * z / (4 * n * n)) / denom
    positive = [r["mean"] for r in rows if r["label"] == 1]
    negative = [r["mean"] for r in rows if r["label"] == 0]
    auc = (
        sum((p > q) + 0.5 * (p == q) for p in positive for q in negative)
        / (len(positive) * len(negative))
        if positive and negative
        else None
    )
    bins = []
    for i in range(5):
        group = [r for r in rows if min(4, int(r["mean"] * 5)) == i]
        if group:
            bins.append(
                {
                    "predicted": statistics.fmean(r["mean"] for r in group),
                    "observed": statistics.fmean(r["label"] for r in group),
                    "n": len(group),
                }
            )
    by_class = {
        str(k): {
            "n": sum(r["label"] == k for r in rows),
            "errors": sum(e for r, e in zip(rows, errors) if r["label"] == k),
        }
        for k in (0, 1)
    }
    return {
        "accuracy": accuracy,
        "accuracy_ci": [center - radius, center + radius],
        "auc": auc,
        "brier": statistics.fmean((r["mean"] - r["label"]) ** 2 for r in rows),
        "variance": statistics.fmean(r["variance"] for r in rows),
        "calibration": bins,
        "by_class": by_class,
    }


def review(rows, rate, kind, threshold):
    count = round(len(rows) * rate / 100)
    ranked = sorted(
        rows,
        key=lambda r: (
            (-r["variance"] if kind == "disagreement" else r["confidence"]),
            r["id"],
        ),
    )
    flagged = {r["id"] for r in ranked[:count]}
    retained = [r for r in rows if r["id"] not in flagged]
    errors = sum((r["mean"] >= threshold) != r["label"] for r in retained)
    return {
        "flagged": sorted(flagged),
        "retained": len(retained),
        "errors": errors,
        "error_rate": errors / len(retained),
    }


@lru_cache(maxsize=32)
def run(seed=42, budget=32, repeats=20):
    if (
        seed not in (7, 42, 101)
        or budget not in (16, 32, 64)
        or repeats not in (10, 20, 40)
    ):
        raise ValueError("Choose one of the displayed experiment settings.")
    train, val, test, model, threshold = cohort(seed)
    result = {
        "simulated": True,
        "seed": seed,
        "budget": budget,
        "repeats": repeats,
        "threshold": threshold,
        "splits": {"train": len(train), "validation": len(val), "test": len(test)},
        "methods": {},
        "cases": [],
    }
    for method in ("random", "spatial"):
        rows = []
        for c in test:
            probs = []
            samples = []
            for repeat in range(repeats):
                rng = random.Random(seed * 1000000 + int(c["id"][4:]) * 1000 + repeat)
                indices = sample_indices(budget, method, rng)
                probs.append(
                    predict(mean_features([c["patches"][i] for i in indices]), model)
                )
                samples.append(indices)
            avg = statistics.fmean(probs)
            rows.append(
                {
                    "id": c["id"],
                    "label": c["label"],
                    "mean": avg,
                    "variance": statistics.variance(probs),
                    "confidence": max(avg, 1 - avg),
                    "probabilities": probs,
                    "samples": samples,
                }
            )
        curves = {
            kind: [
                {"rate": rate, **review(rows, rate, kind, threshold)}
                for rate in (0, 10, 20, 30, 40)
            ]
            for kind in ("confidence", "disagreement")
        }
        result["methods"][method] = {
            "rows": rows,
            "metrics": summarize(rows, threshold),
            "curves": curves,
        }
    result["cases"] = [
        {
            "id": c["id"],
            "label": c["label"],
            "signal": [round(p[0], 4) for p in c["patches"]],
        }
        for c in test
    ]
    return result
