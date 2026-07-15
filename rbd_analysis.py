import urllib.request
import pandas as pd
import matplotlib.pyplot as plt

BASE = "https://physionet.org/files/capslpdb/1.0.0/"

# Subject IDs in the CAP database:
#   RBD patients:      rbd1 ... rbd22
#   Healthy controls:  n1  ... n16   ('n' = normal)
RBD_IDS      = [f"rbd{i}" for i in range(1, 23)]
CONTROL_IDS  = [f"n{i}"   for i in range(1, 17)]

# 1. DOWNLOAD the small annotation (.txt) files

def download_txt(subject_id):
    """Download one subject's .txt file. Returns text, or None if it fails."""
    url = BASE + subject_id + ".txt"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [skip] {subject_id}: {e}")
        return None

# 2. PARSE a .txt file into its sequence of 30-second epochs

def parse_epochs(text):
    """Return a list of sleep-stage labels (one per 30-second epoch)."""
    lines = text.splitlines()
    header_idx, cols = None, None
    for i, line in enumerate(lines):
        if line.startswith("Sleep Stage") and "Event" in line:
            header_idx = i
            cols = [c.strip() for c in line.split("\t")]
            break
    if header_idx is None:
        return []

    idx = {name: j for j, name in enumerate(cols)}
    stage_i = idx.get("Sleep Stage", 0)
    event_i = idx.get("Event", 3)

    stages = []
    for line in lines[header_idx + 1:]:
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) <= max(stage_i, event_i):
            continue
        event = parts[event_i]
        # keep only the 30-second sleep-stage epoch rows (ignore CAP micro-events)
        if event.startswith("SLEEP-"):
            stages.append(parts[stage_i])
    return stages


# 3. COMPUTE sleep-architecture metrics for one subject

def compute_metrics(stages):
    """Turn a list of epoch stages into summary sleep metrics."""
    if not stages:
        return None
    n = len(stages)
    count = lambda s: stages.count(s)

    wake        = count("W")
    tst_epochs  = n - wake                 # total sleep time (epochs)
    deep        = count("S3") + count("S4")  # N3 = S3 + S4

    pct = lambda x: round(100 * x / tst_epochs, 1) if tst_epochs else 0.0

    # awakenings = number of times the subject enters Wake after first falling asleep
    first_sleep = next((i for i, s in enumerate(stages) if s != "W"), 0)
    awakenings = sum(
        1 for i in range(first_sleep + 1, n)
        if stages[i] == "W" and stages[i - 1] != "W"
    )
    # fragmentation = how many times the stage changes across the night
    transitions = sum(1 for i in range(1, n) if stages[i] != stages[i - 1])

    return {
        "recording_min":      round(n * 30 / 60, 1),
        "TST_min":            round(tst_epochs * 30 / 60, 1),
        "sleep_efficiency_%": round(100 * tst_epochs / n, 1),
        "REM_%":              pct(count("R")),
        "N1_%":               pct(count("S1")),
        "N2_%":               pct(count("S2")),
        "N3_deep_%":          pct(deep),
        "wake_epochs":        wake,
        "awakenings":         awakenings,
        "stage_transitions":  transitions,
    }


# 4. RUN the pipeline over all subjects

def build_dataset():
    records = []
    for group, ids in [("RBD", RBD_IDS), ("Control", CONTROL_IDS)]:
        print(f"Downloading & analyzing {group} subjects...")
        for sid in ids:
            text = download_txt(sid)
            if text is None:
                continue
            metrics = compute_metrics(parse_epochs(text))
            if metrics is None:
                print(f"  [skip] {sid}: could not parse")
                continue
            metrics["subject"] = sid
            metrics["group"]   = group
            records.append(metrics)
    df = pd.DataFrame(records)
    # put id/group columns first
    front = ["subject", "group"]
    df = df[front + [c for c in df.columns if c not in front]]
    return df



# 5. EXECUTE + summarize + plot

print("=" * 55)
print(" RBD vs Control — Sleep Architecture Analysis")
print("=" * 55)

data = build_dataset()
data.to_csv("rbd_results_raw.csv", index=False)
print(f"\nAnalyzed {len(data)} subjects "
      f"({(data.group=='RBD').sum()} RBD, {(data.group=='Control').sum()} Control)")
print("Saved per-subject results -> rbd_results_raw.csv\n")

# --- Group comparison table (mean of each metric per group) ---
metric_cols = ["TST_min", "sleep_efficiency_%", "REM_%", "N1_%", "N2_%",
               "N3_deep_%", "awakenings", "stage_transitions"]
summary = data.groupby("group")[metric_cols].mean().round(1).T
summary["difference"] = (summary.get("RBD", 0) - summary.get("Control", 0)).round(1)
print("GROUP COMPARISON (means):")
print(summary.to_string())
summary.to_csv("rbd_group_comparison.csv")
print("\nSaved comparison -> rbd_group_comparison.csv")

# --- Chart 1: bar chart comparing key stage percentages ---
stage_metrics = ["REM_%", "N1_%", "N2_%", "N3_deep_%"]
means = data.groupby("group")[stage_metrics].mean()
ax = means.T.plot(kind="bar", figsize=(8, 5))
ax.set_ylabel("% of Total Sleep Time")
ax.set_title("Sleep Stage Distribution: RBD vs Control")
ax.set_xticklabels(stage_metrics, rotation=0)
plt.tight_layout()
plt.savefig("fig1_sleep_stages.png", dpi=150)
plt.show()

# --- Chart 2: boxplot of sleep fragmentation (awakenings) ---
fig, ax = plt.subplots(figsize=(7, 5))
groups = data["group"].unique()
ax.boxplot([data[data.group == g]["awakenings"] for g in groups], labels=groups)
ax.set_ylabel("Number of Awakenings")
ax.set_title("Sleep Fragmentation: RBD vs Control")
plt.tight_layout()
plt.savefig("fig2_fragmentation.png", dpi=150)
plt.show()

print("\nDONE. Charts saved: fig1_sleep_stages.png, fig2_fragmentation.png")
print("Download these + the CSVs for your report (Files panel on the left in Colab).")
