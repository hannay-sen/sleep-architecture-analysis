# RBD vs Control — Sleep Architecture Analysis
 
This script downloads polysomnography annotation files from the **CAP Sleep
Database** (PhysioNet) and compares sleep architecture between patients with
REM Sleep Behavior Disorder (RBD) and healthy controls.
 
## What it does
 
1. **Downloads** the `.txt` scoring files for 22 RBD subjects (`rbd1`–`rbd22`)
   and 16 healthy control subjects (`n1`–`n16`) from:
   `https://physionet.org/files/capslpdb/1.0.0/`
2. **Parses** each file into a sequence of 30-second sleep-stage epochs
   (Wake, N1/S1, N2/S2, N3/S3+S4, REM).
3. **Computes** per-subject sleep metrics:
   - Total recording time and total sleep time (TST)
   - Sleep efficiency (%)
   - % time in REM, N1, N2, and N3 (deep sleep)
   - Number of awakenings after sleep onset
   - Number of stage transitions (a proxy for sleep fragmentation)
4. **Summarizes** results with a group-level comparison table (RBD vs Control
   means and the difference between them).
5. **Plots**:
   - A bar chart of sleep-stage distribution (REM/N1/N2/N3) by group
   - A boxplot of awakenings (fragmentation) by group
## Requirements
 
```bash
pip install pandas matplotlib
```
 
Internet access is required to download the annotation files from PhysioNet.
 
## Usage
 
Run the script directly (e.g. in a Jupyter/Colab notebook or from the command
line):
 
```bash
python rbd_analysis.py
```
 
Some subjects may be skipped automatically if their file fails to download or
can't be parsed — a message is printed for each skipped subject, and the
final counts reflect only successfully analyzed subjects.
 
## Output files
 
| File | Description |
|---|---|
| `rbd_results_raw.csv` | Per-subject metrics (one row per subject) |
| `rbd_group_comparison.csv` | Group-level mean comparison (RBD vs Control) |
| `fig1_sleep_stages.png` | Bar chart: sleep stage % by group |
| `fig2_fragmentation.png` | Boxplot: awakenings by group |
 
## Notes on the metrics
 
- **Sleep efficiency** = (total sleep time / total recording time) × 100
- **N3 (deep sleep)** combines legacy stages S3 and S4, per AASM convention
- **Awakenings** count only transitions *into* Wake after the first sleep
  epoch (i.e., they exclude the initial sleep-onset period)
- **Stage transitions** count every change in stage across the whole night,
  including into/out of Wake — a simple global fragmentation index
## Data source
 
Terzano MG, et al. *The CAP Sleep Database*. PhysioNet.
https://physionet.org/content/capslpdb/1.0.0/
 
