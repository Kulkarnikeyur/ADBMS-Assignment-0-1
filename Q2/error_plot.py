import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_SIZES = [1000, 3000, 5000]

# Error files are stored here
OUTPUT_DIR = "../Q2/output"

# Plot will be saved here
PLOT_DIR = "../Q2/plots"

os.makedirs(PLOT_DIR, exist_ok=True)


# ============================================================
# READ MAX SELECTIVITY ERRORS
# ============================================================

def read_errors():

    id_errors = []
    title_errors = []

    for sample_size in SAMPLE_SIZES:

        filename = os.path.join(
            OUTPUT_DIR,
            f"Errors_{sample_size}.csv"
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

        id_row = df[
            df["attribute"] == "id"
        ]

        if id_row.empty:
            raise ValueError(
                f"'id' entry not found in {filename}"
            )

        id_error = float(
            id_row.iloc[0]["max_selectivity_error"]
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_row = df[
            df["attribute"] == "title"
        ]

        if title_row.empty:
            raise ValueError(
                f"'title' entry not found in {filename}"
            )

        title_error = float(
            title_row.iloc[0]["max_selectivity_error"]
        )

        id_errors.append(id_error)
        title_errors.append(title_error)

    return id_errors, title_errors


# ============================================================
# PLOT SAMPLE SIZE VS MAX SELECTIVITY ERROR
# ============================================================

def plot_selectivity_error(id_errors, title_errors):

    plt.figure(
        figsize=(10, 6)
    )

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    plt.plot(
        SAMPLE_SIZES,
        id_errors,
        marker="o",
        linewidth=2,
        markersize=8,
        label="ID"
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    plt.plot(
        SAMPLE_SIZES,
        title_errors,
        marker="o",
        linewidth=2,
        markersize=8,
        label="Title"
    )

    # --------------------------------------------------------
    # Label ID points
    # --------------------------------------------------------

    for x, y in zip(
        SAMPLE_SIZES,
        id_errors
    ):

        plt.annotate(
            f"{y:.6f}",
            (x, y),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

    # --------------------------------------------------------
    # Label Title points
    # --------------------------------------------------------

    for x, y in zip(
        SAMPLE_SIZES,
        title_errors
    ):

        plt.annotate(
            f"{y:.6f}",
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
        "Maximum selectivity error"
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    plt.title(
        "Sample Size vs Maximum Selectivity Error"
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
    # Save
    # --------------------------------------------------------

    filename = os.path.join(
        PLOT_DIR,
        "sample_size_vs_max_selectivity_error.png"
    )

    plt.tight_layout()

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
    print("SAMPLE SIZE VS MAXIMUM SELECTIVITY ERROR")
    print("=" * 70)

    # --------------------------------------------------------
    # Read data
    # --------------------------------------------------------

    id_errors, title_errors = read_errors()

    # --------------------------------------------------------
    # Display values
    # --------------------------------------------------------

    print("\nMaximum selectivity errors:")
    print("-" * 70)

    print(
        f"{'Sample Size':>15}"
        f"{'ID Error':>20}"
        f"{'Title Error':>20}"
    )

    print("-" * 70)

    for i in range(
        len(SAMPLE_SIZES)
    ):

        print(
            f"{SAMPLE_SIZES[i]:>15}"
            f"{id_errors[i]:>20.10f}"
            f"{title_errors[i]:>20.10f}"
        )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    plot_selectivity_error(
        id_errors,
        title_errors
    )

    print("\nDone.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()