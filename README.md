# ADBMS Assignment

This project implements the required ADBMS assignment tasks for **Q1 and Q2**.

The project is automated so that the **entire project can be executed by running a single file: `main.py`**.

---

## Project Structure

```text
ADBMS-Assignment-0-1-main/
│
├── main.py
│
├── Q1/
│   ├── q1_histograms.py
│   ├── q1_histogram_boundaries.csv
│   ├── id_histogram.png
│   └── title_histogram.png
│
├── Q2/
│   ├── optimal_serial_histo.py
│   ├── error_plot.py
│   ├── extrapolate.py
│   │
│   ├── output/
│   │   ├── Errors_1000.csv
│   │   ├── Errors_3000.csv
│   │   ├── Errors_5000.csv
│   │   ├── Times_1000.csv
│   │   ├── Times_3000.csv
│   │   ├── Times_5000.csv
│   │   ├── id_boundaries_1000.csv
│   │   ├── id_boundaries_3000.csv
│   │   ├── id_boundaries_5000.csv
│   │   ├── title_boundaries_1000.csv
│   │   ├── title_boundaries_3000.csv
│   │   └── title_boundaries_5000.csv
│   │
│   └── plots/
│       ├── id_histogram_1000.png
│       ├── id_histogram_3000.png
│       ├── id_histogram_5000.png
│       ├── id_sample_size_vs_time.png
│       ├── title_histogram_1000.png
│       ├── title_histogram_3000.png
│       ├── title_histogram_5000.png
│       ├── title_sample_size_vs_time.png
│       ├── sample_size_vs_time.png
│       └── sample_size_vs_max_selectivity_error.png
│
└── BT2024025_Report.pdf
```

---

# Requirements

## Python

Python 3 is required.

The following Python packages are required:

```bash
pip install pandas numpy matplotlib "psycopg[binary]"
```

The packages used by the project are:

* `pandas`
* `numpy`
* `matplotlib`
* `psycopg`

---

# Database Configuration

Q2 connects to a PostgreSQL database.

The database configuration is defined in:

```text
Q2/optimal_serial_histo.py
```

Current configuration:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "job",
    "user": "postgres",
    "password": "Keyur@02"
}
```

The PostgreSQL server must therefore be running and the required database/table must be available before executing Q2.

The project expects the table:

```text
title
```

with the attributes:

```text
id
title
```

---

# Execution

## Single-command execution

The complete project is executed through:

```bash
python main.py
```

**Run this command from the project root directory**, i.e. the directory containing `main.py`.

Do not run the individual Q1/Q2 scripts manually.

---

# Execution Order

`main.py` executes all scripts sequentially in the following order:

```text
1. Q1/q1_histograms.py
        ↓
2. Q2/optimal_serial_histo.py
        ↓
3. Q2/error_plot.py
        ↓
4. Q2/extrapolate.py
```

If any script fails, execution stops and the corresponding error is displayed.

If all scripts complete successfully, the following message is displayed:

```text
ALL PROJECT TASKS COMPLETED SUCCESSFULLY
```

---

# Q1

Q1 is executed by:

```text
Q1/q1_histograms.py
```

The script reads:

```text
Q1/q1_histogram_boundaries.csv
```

The total number of rows used for the histogram frequency calculation is:

```python
N = 2528312
```

The current configuration in the script is:

```python
attribute = "title"
numeric = False
```

Therefore, the current execution generates the histogram for the `title` attribute.

To generate the histogram for `id`, change the parameters in `q1_histograms.py` to:

```python
attribute = "id"
numeric = True
```

The generated histogram is displayed using Matplotlib.

---

# Q2

Q2 consists of three processing stages.

## Q2.1/Q2.2/Q2.3 — Optimal Serial Histogram

The main Q2 processing is performed by:

```text
Q2/optimal_serial_histo.py
```

### Parameters

The table size is:

```python
TABLE_SIZE = 2528312
```

The number of histogram buckets is:

```python
NUM_BUCKETS = 20
```

The allowed bucket range is:

```text
10–50 buckets
```

The output directories are:

```python
OUTPUT_DIR = "output"
PLOT_DIR = "plots"
```

The script uses the following sample sizes:

```text
1000
3000
5000
```

For each requested sample size, the script obtains an oversampled dataset and selects the required number of distinct values.

The histogram is constructed for:

```text
id
title
```

The script also measures histogram construction time and calculates maximum selectivity error.

---

# Q2 Error Plot

The second Q2 stage is:

```text
Q2/error_plot.py
```

It reads the generated error files:

```text
Q2/output/Errors_1000.csv
Q2/output/Errors_3000.csv
Q2/output/Errors_5000.csv
```

The sample sizes used are:

```python
SAMPLE_SIZES = [1000, 3000, 5000]
```

The script extracts the maximum selectivity errors for:

```text
id
title
```

and generates:

```text
Q2/plots/sample_size_vs_max_selectivity_error.png
```

---

# Q2 Extrapolation

The final Q2 stage is:

```text
Q2/extrapolate.py
```

It reads the histogram construction times from:

```text
Q2/output/Times_1000.csv
Q2/output/Times_3000.csv
Q2/output/Times_5000.csv
```

The sample sizes are:

```python
SAMPLE_SIZES = [1000, 3000, 5000]
```

The complete table size is:

```python
TABLE_SIZE = 2528312
```

Linear regression is used to estimate the histogram construction time for the complete table.

The fitted model is:

```text
T = aS + b
```

where:

* `T` = histogram construction time
* `S` = sample size
* `a` = regression slope
* `b` = regression intercept

The extrapolated time is calculated for both:

```text
id
title
```

The script also generates:

```text
Q2/plots/sample_size_vs_time.png
```

---

# Parameters Summary

| Parameter         |         Value |
| ----------------- | ------------: |
| Full table size   |   `2,528,312` |
| Histogram buckets |          `20` |
| Minimum buckets   |          `10` |
| Maximum buckets   |          `50` |
| Sample size 1     |        `1000` |
| Sample size 2     |        `3000` |
| Sample size 3     |        `5000` |
| Q2 attributes     | `id`, `title` |
| Database          |    PostgreSQL |
| Database name     |         `job` |
| Database host     |   `localhost` |
| Database port     |        `5432` |
| Database user     |    `postgres` |

---

# Output

After successful execution, Q2 produces:

### CSV files

```text
Q2/output/
```

containing:

* Histogram boundaries for `id` and `title`
* Histogram construction times
* Maximum selectivity errors

### Plots

```text
Q2/plots/
```

containing:

* Histograms for all sample sizes
* Sample size vs. construction time plots
* Sample size vs. maximum selectivity error plot

---

# Complete Execution

From the project root:

```bash
cd ADBMS-Assignment-0-1-main
python main.py
```

This single command performs:

```text
Q1
 ↓
Q2 Optimal Serial Histogram
 ↓
Q2 Error Analysis
 ↓
Q2 Linear Extrapolation
```

No individual script execution is required.

---
