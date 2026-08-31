# ADBMS Assignment 0 & 1 — PostgreSQL Histograms on the JOB Benchmark

This repository contains the code, data, and generated plots for **Assignment 0** (environment/database setup) and **Assignment 1** (PostgreSQL histogram analysis) for the Advanced Database Management Systems (ADBMS) course, using the **Join Order Benchmark (JOB, 2013 snapshot)** dataset loaded into PostgreSQL.

The full write-up, methodology, and results are in [`adbms_ass1.pdf`](./adbms_ass1.pdf).

## Overview

- **Assignment 0** — records the machine/software setup used for the experiments (CPU, RAM, SSD, OS, PostgreSQL version) and the JOB database schema (21 tables with primary keys and cardinalities).
- **Assignment 1** — analyzes the `id` and `title` columns of the `title` table (`N = 2,528,312` rows):
  - **Q1**: Inspects PostgreSQL's native equi-depth histograms (via `pg_stats`), plots them, and evaluates their selectivity-estimation accuracy against actual query selectivity for both a numeric range predicate (`id < 350000`) and a text range predicate (`title < 'Race'`).
  - **Q2**: Builds a custom **optimal serial histogram** (20 buckets, minimizing `Σ nᵢVᵢ` — number of distinct values times frequency variance per bucket) from table samples of different sizes (1000 / 3000 / 5000 requested rows via `TABLESAMPLE`), measures construction time, computes maximum selectivity error, and extrapolates construction time to the full table.

## Repository Structure

```
ADBMS-Assignment-0-1-main/
├── adbms_ass1.pdf                        # Full assignment report (setup, methodology, results, figures)
├── q1/                                    # Assignment 1, Question 1: PostgreSQL native histograms
│   ├── q1_histograms.py                   # Parses pg_stats histogram_bounds and plots the histogram
│   ├── q1_histogram_boundaries.csv        # Exported pg_stats row for id/title (attname, n_distinct, histogram_bounds)
│   ├── id_histogram.png                   # Rendered histogram for title.id
│   └── title_histogram.png                # Rendered histogram for title.title
└── q2/                                     # Assignment 1, Question 2: Optimal serial histogram
    ├── code/
    │   ├── plot_serial_histograms.py      # Builds the DP-optimal serial histogram, computes cost/build time/max
    │   │                                   # selectivity error, and generates the per-sample-size bucket plots
    │   ├── Q2_7.py                        # Plots sample size vs. histogram construction time
    │   └── q2_8.py                        # Plots sample size vs. maximum selectivity error
    ├── data/                              # Sampled (value, frequency) pairs pulled via TABLESAMPLE
    │   ├── id_freq_{1000,3000,5000}.csv
    │   └── title_freq_{1000,3000,5000}.csv
    ├── histograms/                        # Generated 20-bucket serial histogram plots per column/sample size
    │   └── serial_histogram_{id,title}_{1000,3000,5000}.png
    └── plot/                              # Summary plots across all sample sizes
        ├── q2_7_sample_size_vs_time.png
        └── q2_8_sample_size_vs_max_selectivity_error.png
```

## Requirements

- PostgreSQL (18.x used in this study) with the JOB (2013) dataset loaded, at minimum the `title` table
- Python 3.x with:
  ```
  pandas
  numpy
  matplotlib
  ```

Install with:
```bash
pip install pandas numpy matplotlib
```

## Reproducing the Results

### Q1 — Native PostgreSQL Histogram

1. Generate statistics and export the histogram bounds from PostgreSQL:
   ```sql
   ANALYZE title;

   SELECT attname, n_distinct, most_common_vals, most_common_freqs, histogram_bounds
   FROM pg_stats
   WHERE tablename = 'title' AND attname IN ('id', 'title');
   ```
   Save the result as a CSV (matching the format of `q1/q1_histogram_boundaries.csv`).

2. Run the plotting script (edit the `attribute`/`numeric` flags at the top of the file to switch between `id` and `title`, and point `pd.read_csv(...)` at your exported CSV):
   ```bash
   cd q1
   python q1_histograms.py
   ```

### Q2 — Optimal Serial Histogram

1. Sample the table and compute per-value frequencies for each requested sample size, e.g.:
   ```sql
   SELECT id, COUNT(*) AS frequency
   FROM title TABLESAMPLE BERNOULLI(<pct>)
   GROUP BY id;
   ```
   Export each result as `id_freq_<size>.csv` / `title_freq_<size>.csv` (columns: value, `frequency`), matching the files under `q2/data/`.

2. Build the serial histograms, print bucket boundaries/cost/build time/max selectivity error, and generate per-sample-size plots:
   ```bash
   cd q2/code
   python plot_serial_histograms.py
   ```
   By default this runs the 1000- and 5000-row experiments (see the `experiments` list at the bottom of the script); adjust the file names/sizes there to reproduce the 3000-row run as well.

3. Generate the summary plots (update the hard-coded `sample_sizes`/timing/error arrays with your own measured values first):
   ```bash
   python Q2_7.py   # sample size vs. construction time
   python q2_8.py   # sample size vs. maximum selectivity error
   ```

## Key Findings (see the report for full details)

- PostgreSQL's histograms for `id` and `title` are **equi-depth**, each with 100 buckets; text values are ordered lexicographically and compared via a byte-based scalar interpolation scheme.
- Maximum selectivity error for the native histograms was ≈ **0.01** for both columns; measured selectivity error on the two test queries was **0.0074** (`title < 'Race'`) and **0.0021** (`id < 350000`).
- The custom 20-bucket optimal serial histogram achieves **zero error for `id`** (every value has frequency 1) and a small error for `title` (max ≈ **0.0047**, i.e., ~0.47%) at the 3000-row sample size.
- Serial-histogram construction time grows steeply with sample size (from tens of seconds at 1000 rows to ~1200 seconds at ~4800 rows), reflecting the O(B·n²) dynamic-programming construction; naive linear extrapolation to the full 2.5M-row table suggests **~150+ hours**, which is why sampling is used in practice.

## Notes

- File and variable names in the scripts (e.g., `histooo.csv`, hard-coded sample-size arrays) reflect the exact scripts used to produce the report's figures; update paths/values as needed if you rerun the pipeline with different exports.
- `q1/fghj` is an empty leftover file with no content and can be ignored/removed.
