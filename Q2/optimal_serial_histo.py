import os
import time

import psycopg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "job",
    "user": "postgres",
    "password": "Keyur@02"
}


# ============================================================
# PARAMETERS
# ============================================================

TABLE_SIZE = 2528312
# Q2 allows 10-50 buckets.
NUM_BUCKETS = 20

OUTPUT_DIR = "output"
PLOT_DIR = "plots"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)


# ============================================================
# SQL
# ============================================================

# We intentionally fetch MORE than SAMPLE_SIZE rows.
#
# The oversampled rows are then used to obtain:
#   3000 distinct IDs
#   3000 distinct titles
#
# This is important because title is NOT unique.

SAMPLE_SQL = """
SELECT id, title
FROM title TABLESAMPLE BERNOULLI (%s)
ORDER BY random()
LIMIT %s;
"""

# ============================================================
# GET OVERSAMPLED DATA
# ============================================================

def get_oversampled_data(
    conn,
    sample_size,
    table_size
):

    # Start with 5 times the required number of rows.
    #
    # This gives us enough rows to obtain 3000 distinct
    # title values even when titles are repeated.

    target_rows = sample_size * 5

    percentage = (
        target_rows / table_size
    ) * 100

    percentage = max(
        1.0,
        percentage
    )

    percentage = min(
        100.0,
        percentage
    )

    while True:

        print(
            f"TABLESAMPLE BERNOULLI "
            f"({percentage:.4f}%)"
        )

        with conn.cursor() as cur:

            cur.execute(
                SAMPLE_SQL,
                (
                    percentage,
                    target_rows
                )
            )

            rows = cur.fetchall()

        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "title"
            ]
        )

        # Check whether the oversample contains enough
        # distinct values for both attributes.

        distinct_ids = (
            df["id"]
            .dropna()
            .nunique()
        )

        distinct_titles = (
            df["title"]
            .dropna()
            .nunique()
        )

        print(
            f"Rows obtained       : {len(df)}"
        )

        print(
            f"Distinct IDs        : {distinct_ids}"
        )

        print(
            f"Distinct titles     : {distinct_titles}"
        )

        if (
            distinct_ids >= sample_size
            and
            distinct_titles >= sample_size
        ):

            return df

        # If insufficient distinct values were obtained,
        # increase the TABLESAMPLE percentage.

        if percentage >= 100:

            raise RuntimeError(
                "Could not obtain enough distinct "
                "ID/title values from TABLESAMPLE."
            )

        percentage *= 2

        percentage = min(
            percentage,
            100.0
        )


# ============================================================
# SELECT EXACTLY N DISTINCT VALUES
# ============================================================

def select_distinct_values(
    df,
    column,
    sample_size
):

    # Remove NULLs
    temp = df[
        df[column].notna()
    ].copy()

    # Remove duplicate values.
    #
    # Because the original sample was randomly shuffled,
    # keeping the first occurrence gives a random subset
    # of distinct values.

    temp = temp.drop_duplicates(
        subset=[column]
    )

    # Randomize again to make selection explicit.
    temp = temp.sample(
        frac=1,
        random_state=None
    )

    # Select exactly SAMPLE_SIZE distinct values.

    temp = temp.head(
        sample_size
    )

    if len(temp) < sample_size:

        raise RuntimeError(
            f"Could not obtain {sample_size} "
            f"distinct values for {column}."
        )

    return temp[column].tolist()


# ============================================================
# PREPARE FREQUENCY DATA FOR TITLE
# ============================================================

def prepare_title_frequency_data(
    title_values
):

    # Count occurrences of every title
    # in the sampled data.

    frequency_data = (
        pd.Series(title_values)
        .value_counts()
        .sort_index()
    )

    values = (
        frequency_data
        .index
        .tolist()
    )

    frequencies = (
        frequency_data
        .values
        .astype(float)
    )

    return values, frequencies


# ============================================================
# BUILD PREFIX SUMS
# ============================================================

def build_prefix_sums(
    frequencies
):

    prefix_sum = np.zeros(
        len(frequencies) + 1
    )

    prefix_sum[1:] = np.cumsum(
        frequencies
    )

    prefix_squared_sum = np.zeros(
        len(frequencies) + 1
    )

    prefix_squared_sum[1:] = np.cumsum(
        frequencies ** 2
    )

    return (
        prefix_sum,
        prefix_squared_sum
    )


# ============================================================
# COST OF ONE SERIAL BUCKET
# ============================================================

def interval_cost(
    prefix_sum,
    prefix_squared_sum,
    start,
    end
):

    # Interval:
    #
    # [start, end)
    #
    # i.e. start included, end excluded.

    number_of_values = (
        end - start
    )

    if number_of_values <= 0:
        return 0.0

    total_frequency = (
        prefix_sum[end]
        -
        prefix_sum[start]
    )

    total_squared_frequency = (
        prefix_squared_sum[end]
        -
        prefix_squared_sum[start]
    )

    # Minimum squared error when all values in the
    # bucket are represented by their mean frequency.
    #
    # SSE =
    # sum(f_i^2) - (sum(f_i)^2 / n)

    cost = (
        total_squared_frequency
        -
        (
            total_frequency ** 2
            /
            number_of_values
        )
    )

    return cost


# ============================================================
# OPTIMAL SERIAL HISTOGRAM USING DYNAMIC PROGRAMMING
# ============================================================

def optimal_serial_histogram(
    values,
    frequencies,
    num_buckets
):

    n = len(values)

    # Number of buckets cannot exceed the number
    # of distinct values.

    num_buckets = min(
        num_buckets,
        n
    )

    (
        prefix_sum,
        prefix_squared_sum
    ) = build_prefix_sums(
        frequencies
    )

    INF = float("inf")

    # dp[b][j]:
    #
    # minimum error for partitioning the first j
    # distinct values into b buckets.

    dp = np.full(
        (
            num_buckets + 1,
            n + 1
        ),
        INF
    )

    # parent[b][j]:
    #
    # starting index of the last bucket.

    parent = np.full(
        (
            num_buckets + 1,
            n + 1
        ),
        -1,
        dtype=int
    )

    # Zero values in zero buckets has zero cost.

    dp[0][0] = 0.0

    # --------------------------------------------------------
    # Dynamic Programming
    # --------------------------------------------------------

    for b in range(
        1,
        num_buckets + 1
    ):

        for j in range(
            b,
            n + 1
        ):

            best_cost = INF
            best_i = -1

            # Try every possible beginning of the
            # final bucket.

            for i in range(
                b - 1,
                j
            ):

                if dp[b - 1][i] == INF:
                    continue

                current_cost = (
                    dp[b - 1][i]
                    +
                    interval_cost(
                        prefix_sum,
                        prefix_squared_sum,
                        i,
                        j
                    )
                )

                if current_cost < best_cost:

                    best_cost = current_cost
                    best_i = i

            dp[b][j] = best_cost
            parent[b][j] = best_i

    # --------------------------------------------------------
    # Recover optimal bucket boundaries
    # --------------------------------------------------------

    buckets = []

    j = n

    for b in range(
        num_buckets,
        0,
        -1
    ):

        i = parent[b][j]

        buckets.append(
            (i, j)
        )

        j = i

    buckets.reverse()

    # --------------------------------------------------------
    # Convert index boundaries into actual values
    # --------------------------------------------------------

    result = []

    for bucket_number, (
        start,
        end
    ) in enumerate(
        buckets,
        start=1
    ):

        lower_boundary = (
            values[start]
        )

        upper_boundary = (
            values[end - 1]
        )

        frequency = int(
            np.sum(
                frequencies[start:end]
            )
        )

        result.append({

            "bucket":
                bucket_number,

            "lower_boundary":
                lower_boundary,

            "upper_boundary":
                upper_boundary,

            "frequency":
                frequency,

            "distinct_values":
                end - start
        })

    return pd.DataFrame(
        result
    )


# ============================================================
# EQUI-DEPTH HISTOGRAM FOR ID
# ============================================================

def equi_depth_histogram(
    id_values,
    num_buckets
):

    # ID is unique, therefore every sampled ID has
    # frequency = 1.
    #
    # Sort the IDs and divide them into approximately
    # equal numbers of IDs per bucket.

    ids = sorted(
        id_values
    )

    n = len(ids)

    num_buckets = min(
        num_buckets,
        n
    )

    # Bucket boundaries in terms of positions.

    positions = np.linspace(
        0,
        n,
        num_buckets + 1,
        dtype=int
    )

    result = []

    for bucket_number in range(
        num_buckets
    ):

        start = positions[
            bucket_number
        ]

        end = positions[
            bucket_number + 1
        ]

        bucket_ids = ids[
            start:end
        ]

        if len(bucket_ids) == 0:
            continue

        result.append({

            "bucket":
                bucket_number + 1,

            "lower_boundary":
                bucket_ids[0],

            "upper_boundary":
                bucket_ids[-1],

            "frequency":
                len(bucket_ids),

            "distinct_values":
                len(bucket_ids)
        })

    return pd.DataFrame(
        result
    )


# ============================================================
# SAVE HISTOGRAM CSV
# ============================================================

def save_histogram(
    histogram_df,
    attribute,
    sample_size
):

    filename = os.path.join(
        OUTPUT_DIR,
        f"{attribute}_boundaries_{sample_size}.csv"
    )

    histogram_df.to_csv(
        filename,
        index=False
    )

    print(
        f"CSV saved: {filename}"
    )


# ============================================================
# PLOT HISTOGRAM
# ============================================================

def plot_histogram(
    histogram_df,
    attribute,
    sample_size,
    histogram_type
):

    labels = []

    for _, row in (
        histogram_df.iterrows()
    ):

        lower = str(
            row["lower_boundary"]
        )

        upper = str(
            row["upper_boundary"]
        )

        labels.append(
            f"{lower} – {upper}"
        )

    x_positions = np.arange(
        len(histogram_df)
    )

    plt.figure(
        figsize=(12, 9)
    )

    # --------------------------------------------------------
    # X-axis = Frequency
    # Y-axis = Value boundaries
    #
    # Therefore horizontal bars are required.
    # --------------------------------------------------------

    plt.bar(
        x_positions,
        histogram_df["frequency"],
        width=0.75
    )

    plt.xticks(
        x_positions,
        labels,
        rotation=90,
        fontsize=8
    )

    plt.ylabel(
        "Frequency"
    )

    plt.xlabel(
        f"{attribute} value boundaries"
    )

    plt.title(
        f"{histogram_type} Histogram - {attribute} "
        f"({sample_size} distinct samples)"
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    plt.tight_layout()

    filename = os.path.join(
        PLOT_DIR,
        f"{attribute}_histogram_{sample_size}.png"
    )

    plt.savefig(
        filename,
        dpi=1000,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Plot saved: {filename}"
    )

# ============================================================
# SAVE HISTOGRAM BUILD TIMES
# ============================================================

def save_times(
    sample_size,
    id_build_time,
    title_build_time
):

    filename = os.path.join(
        OUTPUT_DIR,
        f"Times_{sample_size}.csv"
    )

    times_df = pd.DataFrame({
        "attribute": [
            "id",
            "title"
        ],
        "build_time_seconds": [
            id_build_time,
            title_build_time
        ]
    })

    times_df.to_csv(
        filename,
        index=False
    )

    print(
        f"Times saved: {filename}"
    )

# ============================================================
# CALCULATE MAXIMUM SELECTIVITY ERROR
# ============================================================

def calculate_max_selectivity_error(
    conn,
    histogram_df,
    attribute,
    sample_total_frequency
):

    errors = []

    # --------------------------------------------------------
    # Calculate cumulative estimated frequency
    # --------------------------------------------------------

    cumulative_frequency = (
        histogram_df["frequency"]
        .cumsum()
    )

    # --------------------------------------------------------
    # Check every bucket boundary
    # --------------------------------------------------------

    for index, row in histogram_df.iterrows():

        boundary = row["upper_boundary"]

        # Estimated selectivity
        estimated_selectivity = (
            cumulative_frequency.iloc[index]
            /
            sample_total_frequency
        )

        # ----------------------------------------------------
        # Actual selectivity from complete table
        # ----------------------------------------------------

        with conn.cursor() as cur:

            if attribute == "id":

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM title
                    WHERE id <= %s;
                    """,
                    (boundary,)
                )

            elif attribute == "title":

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM title
                    WHERE title <= %s;
                    """,
                    (boundary,)
                )

            else:

                raise ValueError(
                    f"Unsupported attribute: {attribute}"
                )

            actual_count = cur.fetchone()[0]

        actual_selectivity = (
            actual_count
            /
            TABLE_SIZE
        )

        # ----------------------------------------------------
        # Absolute selectivity error
        # ----------------------------------------------------

        error = abs(
            estimated_selectivity
            -
            actual_selectivity
        )

        errors.append(error)

    # --------------------------------------------------------
    # Maximum error
    # --------------------------------------------------------

    max_error = max(errors)

    return max_error

# ============================================================
# SAVE MAXIMUM SELECTIVITY ERROR
# ============================================================

def save_selectivity_error(
    sample_size,
    id_error,
    title_error
):

    filename = os.path.join(
        OUTPUT_DIR,
        f"Errors_{sample_size}.csv"
    )

    error_df = pd.DataFrame({

        "attribute": [
            "id",
            "title"
        ],

        "max_selectivity_error": [
            id_error,
            title_error
        ]
    })

    error_df.to_csv(
        filename,
        index=False
    )

    print(
        f"Selectivity errors saved: {filename}"
    )

# ============================================================
# MAIN
# ============================================================

def main():

    for sample_size in [1000, 3000, 5000]:

        print("=" * 70)
        print("Q2 - HISTOGRAM GENERATION")
        print("=" * 70)

        # --------------------------------------------------------
        # CONNECT TO DATABASE
        # --------------------------------------------------------

        with psycopg.connect(
            **DB_CONFIG
        ) as conn:

            # ----------------------------------------------------
            # GET TABLE SIZE
            # ----------------------------------------------------

            table_size = TABLE_SIZE

            print(
                f"\nTitle table size: "
                f"{table_size}"
            )

            # ----------------------------------------------------
            # GET OVERSAMPLE USING TABLESAMPLE
            # ----------------------------------------------------

            print(
                "\nObtaining random sample using "
                "TABLESAMPLE..."
            )

            sample = get_oversampled_data(
                conn,
                sample_size,
                table_size
            )

            print(
                f"\nOversampled rows: "
                f"{len(sample)}"
            )

            # ----------------------------------------------------
            # SELECT EXACTLY 3000 DISTINCT IDs
            # ----------------------------------------------------

            id_values = select_distinct_values(
                sample,
                "id",
                sample_size
            )

            print(
                f"Distinct ID sample points: "
                f"{len(id_values)}"
            )

            # ----------------------------------------------------
            # SELECT EXACTLY 3000 DISTINCT TITLES
            # ----------------------------------------------------

            title_values = select_distinct_values(
                sample,
                "title",
                sample_size
            )

            print(
                f"Distinct title sample points: "
                f"{len(title_values)}"
            )

            # ====================================================
            # ID HISTOGRAM
            # ====================================================

            print(
                "\n" + "=" * 70
            )

            print(
                "BUILDING ID HISTOGRAM"
            )

            print(
                "=" * 70
            )

            # ----------------------------------------------------
            # Start ID histogram timer
            #
            # Sampling is NOT included.
            # ----------------------------------------------------

            id_start = time.perf_counter()

            id_histogram = equi_depth_histogram(
                id_values,
                NUM_BUCKETS
            )

            id_end = time.perf_counter()

            id_build_time = (
                id_end - id_start
            )

            # ----------------------------------------------------
            # Save ID histogram
            # ----------------------------------------------------

            save_histogram(
                id_histogram,
                "id",
                sample_size
            )

            # ----------------------------------------------------
            # Plot ID histogram
            # ----------------------------------------------------

            plot_histogram(
                id_histogram,
                "id",
                sample_size,
                "Equi-Depth"
            )

            # ====================================================
            # TITLE HISTOGRAM
            # ====================================================

            print(
                "\n" + "=" * 70
            )

            print(
                "BUILDING TITLE HISTOGRAM"
            )

            print(
                "=" * 70
            )

            # ----------------------------------------------------
            # IMPORTANT:
            #
            # For the histogram, we need frequencies of the
            # sampled title values.
            #
            # Since we selected 3000 DISTINCT title values above,
            # each selected title occurs once in the selected
            # histogram input.
            #
            # Therefore, to preserve the original title
            # frequency distribution, we instead calculate the
            # frequencies from the oversampled TABLESAMPLE data.
            # ----------------------------------------------------

            title_frequency_data = (
                sample[
                    sample["title"].notna()
                ]["title"]
                .value_counts()
                .sort_index()
            )

            title_values_for_dp = (
                title_frequency_data
                .index
                .tolist()
            )

            title_frequencies_for_dp = (
                title_frequency_data
                .values
                .astype(float)
            )

            # We need the histogram to be based on exactly
            # 3000 distinct title values.
            #
            # Randomly choose 3000 distinct title values from
            # the oversampled data.

            selected_titles = set(
                title_values
            )

            mask = [
                value in selected_titles
                for value in title_values_for_dp
            ]

            dp_title_values = [
                value
                for value, keep in zip(
                    title_values_for_dp,
                    mask
                )
                if keep
            ]

            dp_title_frequencies = [
                freq
                for freq, keep in zip(
                    title_frequencies_for_dp,
                    mask
                )
                if keep
            ]

            print(
                f"Distinct title values used by DP: "
                f"{len(dp_title_values)}"
            )

            # ----------------------------------------------------
            # Start TITLE histogram timer
            #
            # Sampling is NOT included.
            # ----------------------------------------------------

            title_start = time.perf_counter()

            title_histogram = \
                optimal_serial_histogram(
                    dp_title_values,
                    np.array(
                        dp_title_frequencies
                    ),
                    NUM_BUCKETS
                )

            title_end = time.perf_counter()

            title_build_time = (
                title_end - title_start
            )

            # ----------------------------------------------------
            # Save TITLE histogram
            # ----------------------------------------------------

            save_histogram(
                title_histogram,
                "title",
                sample_size
            )

            # ----------------------------------------------------
            # Plot TITLE histogram
            # ----------------------------------------------------

            plot_histogram(
                title_histogram,
                "title",
                sample_size,
                "Optimal Serial"
            )

                        # ====================================================
            # CALCULATE MAXIMUM SELECTIVITY ERROR
            # ====================================================

            print(
                "\n" + "=" * 70
            )

            print(
                "CALCULATING MAXIMUM SELECTIVITY ERROR"
            )

            print(
                "=" * 70
            )

            # ----------------------------------------------------
            # ID maximum selectivity error
            # ----------------------------------------------------

            id_sample_total_frequency = (
                id_histogram["frequency"]
                .sum()
            )

            id_max_error = (
                calculate_max_selectivity_error(
                    conn,
                    id_histogram,
                    "id",
                    id_sample_total_frequency
                )
            )

            # ----------------------------------------------------
            # TITLE maximum selectivity error
            # ----------------------------------------------------

            title_sample_total_frequency = (
                title_histogram["frequency"]
                .sum()
            )

            title_max_error = (
                calculate_max_selectivity_error(
                    conn,
                    title_histogram,
                    "title",
                    title_sample_total_frequency
                )
            )

            # ----------------------------------------------------
            # Save errors
            # ----------------------------------------------------

            save_selectivity_error(
                sample_size,
                id_max_error,
                title_max_error
            )

            # ----------------------------------------------------
            # Print errors
            # ----------------------------------------------------

            print(
                f"\nID maximum selectivity error    : "
                f"{id_max_error:.10f}"
            )

            print(
                f"Title maximum selectivity error : "
                f"{title_max_error:.10f}"
            )
            
            # ====================================================
            # FINAL RESULTS
            # ====================================================

            print(
                "\n" + "=" * 70
            )

            print(
                "FINAL RESULTS"
            )

            print(
                "=" * 70
            )

            print(
                f"Requested distinct sample points : "
                f"{sample_size}"
            )

            print(
                f"Distinct ID sample points         : "
                f"{len(id_values)}"
            )

            print(
                f"Distinct title sample points      : "
                f"{len(title_values)}"
            )

            print(
                f"Number of buckets                  : "
                f"{NUM_BUCKETS}"
            )

            print(
                f"\nID histogram build time            : "
                f"{id_build_time:.6f} seconds"
            )

            print(
                f"TITLE histogram build time         : "
                f"{title_build_time:.6f} seconds"
            )

            # --------------------------------------------------------
            # SAVE BUILD TIMES
            # --------------------------------------------------------

            save_times(
                sample_size,
                id_build_time,
                title_build_time
            )

            # ----------------------------------------------------
            # Print ID histogram
            # ----------------------------------------------------

            print(
                "\n" + "-" * 70
            )

            print(
                "ID HISTOGRAM"
            )

            print(
                "-" * 70
            )

            print(
                id_histogram.to_string(
                    index=False
                )
            )

            # ----------------------------------------------------
            # Print TITLE histogram
            # ----------------------------------------------------

            print(
                "\n" + "-" * 70
            )

            print(
                "TITLE HISTOGRAM"
            )

            print(
                "-" * 70
            )

            print(
                title_histogram.to_string(
                    index=False
                )
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()