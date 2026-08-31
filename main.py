"""
MAIN PROGRAM
------------
Run the complete histogram assignment with ONE command:

    python main.py

Keep this file in the same folder as:
    q1_histograms.py
    plot_serial_histograms(5).py
    Q2_7.py
    q2_8.py

and all required CSV files.
"""

import runpy
from pathlib import Path

BASE = Path(__file__).resolve().parent


def run_script(filename):
    path = BASE / filename
    if not path.exists():
        print(f"[SKIPPED] {filename} not found.")
        return

    print("\n" + "=" * 80)
    print(f"RUNNING: {filename}")
    print("=" * 80)

    runpy.run_path(str(path), run_name="__main__")


print("=" * 80)
print("HISTOGRAM ASSIGNMENT - MAIN EXECUTION")
print("=" * 80)

# Q1
run_script("q1_histograms.py")

# Q2.5 - optimal serial histograms
run_script("plot_serial_histograms(5).py")

# Q2.7 - sample size vs construction time
run_script("Q2_7.py")

# Q2.8 - sample size vs maximum selectivity error
run_script("q2_8.py")

print("\n" + "=" * 80)
print("ALL AVAILABLE ASSIGNMENT CODE HAS BEEN EXECUTED.")
print("=" * 80)
