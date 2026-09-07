import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

TABLE_SIZE = 2528312

SAMPLE_SIZES = [1000, 3000, 5000]

# Times_1000.csv, Times_3000.csv, Times_5000.csv
OUTPUT_DIR = "../Q2/output"

PLOT_DIR = "../Q2/plots"

os.makedirs(PLOT_DIR, exist_ok=True)


# ============================================================
# READ TIMES FROM CSV FILES
# ============================================================

def read_times():

    id_times = []
    title_times = []

    for sample_size in SAMPLE_SIZES:

        filename = os.path.join(
            OUTPUT_DIR,
            f"Times_{sample_size}.csv"
        )

        if not os.path.exists(filename):
            raise FileNotFoundError(
                f"File not found: {filename}"
            )

        df = pd.read_csv(filename)

        # Normalize attribute names
        df["attribute"] = (
            df["attribute"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        id_row = df[df["attribute"] == "id"]

        if id_row.empty:
            raise ValueError(
                f"'id' entry not found in {filename}"
            )

        id_time = float(
            id_row.iloc[0]["build_time_seconds"]
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_row = df[df["attribute"] == "title"]

        if title_row.empty:
            raise ValueError(
                f"'title' entry not found in {filename}"
            )

        title_time = float(
            title_row.iloc[0]["build_time_seconds"]
        )

        # Store actual values
        id_times.append(id_time)
        title_times.append(title_time)

    return id_times, title_times


# ============================================================
# LINEAR EXTRAPOLATION
# ============================================================
#
# Used ONLY to estimate the build time for the complete table.
#
# The regression line is NOT plotted.
#
# ============================================================

def extrapolate_time(times):

    x = np.array(
        SAMPLE_SIZES,
        dtype=float
    )

    y = np.array(
        times,
        dtype=float
    )

    # Fit:
    #
    # T = aS + b
    #

    slope, intercept = np.polyfit(
        x,
        y,
        1
    )

    estimated_time = (
        slope * TABLE_SIZE
        + intercept
    )

    return estimated_time


# ============================================================
# PLOT BOTH ID AND TITLE IN THE SAME GRAPH
# ============================================================

def plot_both_times(id_times, title_times):

    plt.figure(
        figsize=(10, 6)
    )

    # --------------------------------------------------------
    # ID actual data
    # --------------------------------------------------------

    plt.plot(
        SAMPLE_SIZES,
        id_times,
        marker="o",
        linewidth=2,
        markersize=8,
        label="ID"
    )

    # --------------------------------------------------------
    # Title actual data
    # --------------------------------------------------------

    plt.plot(
        SAMPLE_SIZES,
        title_times,
        marker="o",
        linewidth=2,
        markersize=8,
        label="Title"
    )

    # --------------------------------------------------------
    # Display values above ID points
    # --------------------------------------------------------

    for x, y in zip(
        SAMPLE_SIZES,
        id_times
    ):

        plt.annotate(
            f"{y:.6f}s",
            (x, y),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

    # --------------------------------------------------------
    # Display values above Title points
    # --------------------------------------------------------

    for x, y in zip(
        SAMPLE_SIZES,
        title_times
    ):

        plt.annotate(
            f"{y:.6f}s",
            (x, y),
            xytext=(0, -18),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    plt.xlabel(
        "Sample size"
    )

    plt.ylabel(
        "Build time (seconds)"
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    plt.title(
        "Histogram Build Time vs Sample Size"
    )

    # --------------------------------------------------------
    # X-axis
    # --------------------------------------------------------

    plt.xticks(
        SAMPLE_SIZES
    )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    plt.grid(
        True,
        linestyle="--",
        alpha=0.4
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    plt.legend()

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    plt.tight_layout()

    # --------------------------------------------------------
    # Save plot
    # --------------------------------------------------------

    filename = os.path.join(
        PLOT_DIR,
        "sample_size_vs_time.png"
    )

    plt.savefig(
        filename,
        dpi=300
    )

    plt.show()

    print(
        f"\nPlot saved: {filename}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("Q2.6 — BUILD TIME")
    print("=" * 70)

    print(
        f"\nFull table size: {TABLE_SIZE:,}"
    )

    # ========================================================
    # READ CSV DATA
    # ========================================================

    id_times, title_times = read_times()

    # ========================================================
    # DISPLAY ACTUAL VALUES
    # ========================================================

    print("\nActual build times read from CSV:")
    print("-" * 70)

    print(
        f"{'Sample Size':>15}"
        f"{'ID Time (s)':>20}"
        f"{'Title Time (s)':>20}"
    )

    print("-" * 70)

    for i in range(
        len(SAMPLE_SIZES)
    ):

        print(
            f"{SAMPLE_SIZES[i]:>15}"
            f"{id_times[i]:>20.10f}"
            f"{title_times[i]:>20.10f}"
        )

    # ========================================================
    # PLOT BOTH SERIES
    # ========================================================

    plot_both_times(
        id_times,
        title_times
    )

    # ========================================================
    # EXTRAPOLATE FULL TABLE TIME
    # ========================================================

    id_full_time = extrapolate_time(
        id_times
    )

    title_full_time = extrapolate_time(
        title_times
    )

    # ========================================================
    # DISPLAY EXTRAPOLATED RESULTS
    # ========================================================

    print("\n")
    print("=" * 70)
    print("EXTRAPOLATED FULL-TABLE BUILD TIME")
    print("=" * 70)

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    print("\nID histogram:")

    print(
        f"  {id_full_time:.6f} seconds"
    )

    print(
        f"  {id_full_time / 60:.6f} minutes"
    )

    print(
        f"  {id_full_time / 3600:.6f} hours"
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    print("\nTitle histogram:")

    print(
        f"  {title_full_time:.6f} seconds"
    )

    print(
        f"  {title_full_time / 60:.6f} minutes"
    )

    print(
        f"  {title_full_time / 3600:.6f} hours"
    )

    print("\nDone.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()