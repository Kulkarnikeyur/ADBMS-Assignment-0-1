import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time


# ============================================================
# CONFIGURATION
# ============================================================

NUM_BUCKETS = 20


# ============================================================
# OPTIMAL SERIAL HISTOGRAM
# ============================================================

def optimal_serial_histogram(
    freq_df,
    value_column,
    num_buckets=20
):
    """
    Construct an optimal serial histogram.

    A serial histogram groups values according to their frequencies,
    with no interleaving of frequency ranges between buckets.

    The optimal histogram minimizes:

        SUM(n_i * V_i)

    where:

        n_i = number of attribute values in bucket i
        V_i = variance of their frequencies
    """

    data = freq_df.copy()

    # String representation is used only for deterministic
    # tie-breaking when values have the same frequency.
    data["_sort_value"] = (
        data[value_column].astype(str)
    )

    # --------------------------------------------------------
    # Sort by frequency first.
    # This is what gives the serial ordering.
    # --------------------------------------------------------

    data = data.sort_values(
        by=["frequency", "_sort_value"],
        kind="mergesort"
    ).reset_index(drop=True)

    data.drop(
        columns=["_sort_value"],
        inplace=True
    )

    frequencies = (
        data["frequency"]
        .to_numpy(dtype=float)
    )

    n = len(frequencies)

    if n == 0:
        raise ValueError(
            "Frequency distribution is empty."
        )

    B = min(num_buckets, n)

    # --------------------------------------------------------
    # Prefix sums
    # --------------------------------------------------------

    prefix_sum = np.zeros(n + 1)
    prefix_sq_sum = np.zeros(n + 1)

    prefix_sum[1:] = np.cumsum(frequencies)
    prefix_sq_sum[1:] = np.cumsum(
        frequencies ** 2
    )

    # --------------------------------------------------------
    # Bucket statistics
    # --------------------------------------------------------

    def bucket_statistics(left, right):

        count = right - left

        total = (
            prefix_sum[right]
            - prefix_sum[left]
        )

        total_sq = (
            prefix_sq_sum[right]
            - prefix_sq_sum[left]
        )

        mean = total / count

        variance = (
            total_sq / count
            - mean ** 2
        )

        # Protect against tiny floating-point negatives.
        variance = max(0.0, variance)

        cost = count * variance

        return count, mean, variance, cost

    # --------------------------------------------------------
    # Dynamic programming
    # --------------------------------------------------------

    dp = np.full(
        (B + 1, n + 1),
        np.inf
    )

    prev = np.full(
        (B + 1, n + 1),
        -1,
        dtype=int
    )

    # Secondary criterion only breaks ties.
    # It does NOT replace the histogram objective.
    balance = np.full(
        (B + 1, n + 1),
        np.inf
    )

    dp[0, 0] = 0.0
    balance[0, 0] = 0.0

    EPS = 1e-12

    for b in range(1, B + 1):

        for j in range(b, n + 1):

            for k in range(b - 1, j):

                if np.isinf(dp[b - 1, k]):
                    continue

                (
                    bucket_count,
                    _,
                    _,
                    bucket_cost
                ) = bucket_statistics(k, j)

                candidate_cost = (
                    dp[b - 1, k]
                    + bucket_cost
                )

                candidate_balance = (
                    balance[b - 1, k]
                    + bucket_count ** 2
                )

                better = False

                # Primary objective
                if candidate_cost < dp[b, j] - EPS:
                    better = True

                # Tie-breaking only
                elif abs(
                    candidate_cost - dp[b, j]
                ) <= EPS:

                    if (
                        candidate_balance
                        < balance[b, j] - EPS
                    ):
                        better = True

                if better:

                    dp[b, j] = candidate_cost
                    balance[b, j] = (
                        candidate_balance
                    )
                    prev[b, j] = k

    # --------------------------------------------------------
    # Reconstruct optimal partition
    # --------------------------------------------------------

    boundaries = []

    j = n

    for b in range(B, 0, -1):

        k = prev[b, j]

        if k < 0:
            raise RuntimeError(
                "Unable to reconstruct histogram."
            )

        boundaries.append(
            (k, j)
        )

        j = k

    boundaries.reverse()

    # --------------------------------------------------------
    # Construct bucket table
    # --------------------------------------------------------

    buckets = []

    for bucket_no, (left, right) in enumerate(
        boundaries,
        start=1
    ):

        bucket = data.iloc[left:right]

        bucket_freq = (
            bucket["frequency"]
            .to_numpy(dtype=float)
        )

        count = len(bucket)

        mean_frequency = float(
            np.mean(bucket_freq)
        )

        variance = float(
            np.var(
                bucket_freq,
                ddof=0
            )
        )

        cost = float(
            count * variance
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Store the COMPLETE value set.
        # A serial bucket is NOT necessarily a continuous
        # domain range.
        # ----------------------------------------------------

        values = (
            bucket[value_column]
            .tolist()
        )

        buckets.append({

            "bucket":
                bucket_no,

            "num_values":
                count,

            "min_frequency":
                int(bucket_freq.min()),

            "max_frequency":
                int(bucket_freq.max()),

            "mean_frequency":
                mean_frequency,

            "variance":
                variance,

            "cost":
                cost,

            "values":
                values
        })

    buckets_df = pd.DataFrame(
        buckets
    )

    return (
        data,
        buckets_df,
        float(dp[B, n])
    )


# ============================================================
# MAX SELECTIVITY ERROR
# ============================================================

def calculate_max_selectivity_error(
    histogram,
    frequency_data,
    value_column,
    sample_size
):
    """
    Calculate the maximum selectivity error for a serial histogram.

    For every value v:

        actual frequency:
            f(v)

        estimated frequency:
            average frequency of the bucket containing v

        actual selectivity:
            f(v) / N

        estimated selectivity:
            estimated_frequency / N

        selectivity error:
            |estimated selectivity - actual selectivity|

    Therefore:

        E_max =
            max_v |estimated_frequency - actual_frequency| / N

    The bucket membership is taken directly from the serial
    histogram's stored value sets.
    """

    # --------------------------------------------------------
    # Create a lookup:
    #
    #     attribute value -> actual frequency
    #
    # This comes directly from the frequency distribution
    # used to construct the histogram.
    # --------------------------------------------------------

    frequency_lookup = dict(
        zip(
            frequency_data[value_column],
            frequency_data["frequency"]
        )
    )

    errors = []

    # --------------------------------------------------------
    # Examine every value in every serial-histogram bucket
    # --------------------------------------------------------

    for _, bucket in histogram.iterrows():

        bucket_number = int(
            bucket["bucket"]
        )

        average_frequency = float(
            bucket["mean_frequency"]
        )

        bucket_values = bucket["values"]

        # ----------------------------------------------------
        # Calculate error for every value in this bucket
        # ----------------------------------------------------

        for value in bucket_values:

            actual_frequency = float(
                frequency_lookup[value]
            )

            actual_selectivity = (
                actual_frequency
                / sample_size
            )

            estimated_selectivity = (
                average_frequency
                / sample_size
            )

            selectivity_error = abs(
                estimated_selectivity
                - actual_selectivity
            )

            errors.append({

                "bucket":
                    bucket_number,

                "value":
                    value,

                "actual_frequency":
                    actual_frequency,

                "estimated_frequency":
                    average_frequency,

                "actual_selectivity":
                    actual_selectivity,

                "estimated_selectivity":
                    estimated_selectivity,

                "selectivity_error":
                    selectivity_error
            })

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not errors:
        return (
            0.0,
            None,
            pd.DataFrame()
        )

    error_df = pd.DataFrame(
        errors
    )

    # --------------------------------------------------------
    # Find maximum error
    # --------------------------------------------------------

    max_index = (
        error_df[
            "selectivity_error"
        ].idxmax()
    )

    max_error = float(
        error_df.loc[
            max_index,
            "selectivity_error"
        ]
    )

    max_row = (
        error_df.loc[
            max_index
        ]
    )

    return (
        max_error,
        max_row,
        error_df
    )


# ============================================================
# SERIAL HISTOGRAM PLOT
# ============================================================

def plot_histogram(
    buckets,
    value_column,
    output_file
):
    """
    Plot the serial histogram.

    X-axis:
        Frequency

    Y-axis:
        Value set / bucket

    Unlike an equi-width histogram, a serial histogram can
    contain arbitrary attribute values in a bucket. Therefore
    the plot does NOT represent first_value ... last_value as
    a continuous range.
    """

    labels = []

    for _, row in buckets.iterrows():

        values = row["values"]

        # For small buckets, show the actual values.
        # For large buckets, show a compact count.
        if len(values) <= 4:

            value_text = (
                "{"
                + ", ".join(
                    str(v)
                    for v in values
                )
                + "}"
            )

        else:

            value_text = (
                "{"
                + str(len(values))
                + " values}"
            )

        labels.append(
            f"B{int(row['bucket'])}: "
            f"{value_text}"
        )

    labels = labels[::-1]

    frequencies = (
        buckets["mean_frequency"]
        .to_numpy()
        [::-1]
    )

    plt.figure(
        figsize=(12, 9)
    )

    plt.barh(
        labels,
        frequencies
    )

    plt.xlabel(
        "Frequency"
    )

    plt.ylabel(
        "Value Set / Bucket"
    )

    plt.title(
        f"Optimal {len(buckets)}-Bucket "
        f"Serial Histogram: {value_column}"
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()


# ============================================================
# PROCESS ONE ATTRIBUTE
# ============================================================

def process_column(
    csv_file,
    value_column,
    output_file
):

    print("\n")
    print("=" * 70)
    print(
        f"PROCESSING: {value_column}"
    )
    print("=" * 70)

    df = pd.read_csv(
        csv_file
    )

    sample_size = int(
        df["frequency"].sum()
    )

    print(
        f"Sample size: {sample_size}"
    )

    print(
        f"Distinct values: {len(df)}"
    )

    print(
        f"Frequency range: "
        f"{df['frequency'].min()} - "
        f"{df['frequency'].max()}"
    )

    # --------------------------------------------------------
    # Time ONLY histogram construction
    # --------------------------------------------------------

    start_time = time.perf_counter()

    (
        sorted_data,
        buckets,
        total_cost
    ) = optimal_serial_histogram(
        df,
        value_column,
        NUM_BUCKETS
    )

    build_time = (
        time.perf_counter()
        - start_time
    )

    # --------------------------------------------------------
    # Print histogram
    # --------------------------------------------------------

    print("\nOptimal serial histogram:")
    print()

    print(
        buckets[
            [
                "bucket",
                "num_values",
                "min_frequency",
                "max_frequency",
                "mean_frequency",
                "variance",
                "cost"
            ]
        ].to_string(
            index=False
        )
    )

    print(
        f"\nTotal histogram cost: "
        f"{total_cost:.10f}"
    )

    print(
        f"Histogram build time: "
        f"{build_time:.6f} seconds"
    )

    # --------------------------------------------------------
    # Frequency bucket boundaries
    # --------------------------------------------------------

    print(
        "\nFrequency bucket boundaries:"
    )

    for _, row in buckets.iterrows():

        print(
            f"B{int(row['bucket'])}: "
            f"{int(row['min_frequency'])}"
            f" - "
            f"{int(row['max_frequency'])}"
        )

    # --------------------------------------------------------
    # Maximum selectivity error
    # --------------------------------------------------------

    (
        max_error,
        max_row,
        error_df,
    ) = calculate_max_selectivity_error(
        buckets,
        df,
        value_column,
        sample_size
    )

    print(
        "\nMaximum selectivity error:"
    )

    print("\nMaximum selectivity error:")

    if max_row is None:

        print("No values available.")

    else:

        print(
            f"Bucket: {int(max_row['bucket'])}"
        )

        print(
            f"Value: {max_row['value']}"
        )

        print(
            f"Actual frequency: "
            f"{max_row['actual_frequency']}"
        )

        print(
            f"Estimated frequency: "
            f"{max_row['estimated_frequency']}"
        )

        print(
            f"Actual selectivity: "
            f"{max_row['actual_selectivity']:.12f}"
        )

        print(
            f"Estimated selectivity: "
            f"{max_row['estimated_selectivity']:.12f}"
        )

        print(
            f"Maximum selectivity error: "
            f"{max_error:.12f}"
        )

        print(
            f"Maximum percentage error: "
            f"{max_error * 100:.8f}%"
        )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    plot_histogram(
        buckets,
        value_column,
        output_file
    )

    return {
        "sample_size": sample_size,
        "buckets": buckets,
        "total_cost": total_cost,
        "build_time": build_time,
        "max_selectivity_error": max_error,
        "error_df": error_df
    }


# ============================================================
# MAIN
# ============================================================

# if __name__ == "__main__":

#     title_result = process_column(
#         "title_freq_q2.csv",
#         "title",
#         "serial_histogram_title_q2.png"
#     )

#     id_result = process_column(
#         "id_freq_q2.csv",
#         "id",
#         "serial_histogram_id_q2.png"
#     )

#     print("\n")
#     print("=" * 70)
#     print("FINAL SUMMARY")
#     print("=" * 70)

#     print(
#         f"\nTITLE:"
#     )

#     print(
#         f"Build time = "
#         f"{title_result['build_time']:.6f} s"
#     )

#     print(
#         f"Total cost = "
#         f"{title_result['total_cost']:.10f}"
#     )

#     print(
#         f"Max selectivity error = "
#         f"{title_result['max_selectivity_error']:.12f}"
#     )

#     print(
#         f"\nID:"
#     )

#     print(
#         f"Build time = "
#         f"{id_result['build_time']:.6f} s"
#     )

#     print(
#         f"Total cost = "
#         f"{id_result['total_cost']:.10f}"
#     )

#     print(
#         f"Max selectivity error = "
#         f"{id_result['max_selectivity_error']:.12f}"
#     )

#     print("\nPlots generated:")
#     print(
#         "  serial_histogram_title_q2.png"
#     )
#     print(
#         "  serial_histogram_id_q2.png"
#     )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Q2.5 SAMPLE SIZES
    #
    # These are the requested sample sizes.
    # TABLESAMPLE may produce slightly different actual
    # sample sizes, so the program prints the actual N.
    # --------------------------------------------------------

    experiments = [
        {
            "requested_size": 1000,
            "title_file": "title_freq_1000.csv",
            "id_file": "id_freq_1000.csv"
        },

        {
            "requested_size": 5000,
            "title_file": "title_freq_5000.csv",
            "id_file": "id_freq_5000.csv"
        }
    ]

    all_results = []

    # --------------------------------------------------------
    # Run both experiments
    # --------------------------------------------------------

    for experiment in experiments:

        requested_size = (
            experiment["requested_size"]
        )

        title_file = (
            experiment["title_file"]
        )

        id_file = (
            experiment["id_file"]
        )

        print("\n")
        print("=" * 80)
        print(
            f"Q2.5 EXPERIMENT: "
            f"REQUESTED SAMPLE SIZE = {requested_size}"
        )
        print("=" * 80)

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_result = process_column(
            title_file,
            "title",
            f"serial_histogram_title_{requested_size}.png"
        )

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        id_result = process_column(
            id_file,
            "id",
            f"serial_histogram_id_{requested_size}.png"
        )

        # ----------------------------------------------------
        # Store summary
        # ----------------------------------------------------

        all_results.append({

            "requested_sample_size":
                requested_size,

            "title_sample_size":
                title_result["sample_size"],

            "title_build_time":
                title_result["build_time"],

            "title_max_error":
                title_result[
                    "max_selectivity_error"
                ],

            "id_sample_size":
                id_result["sample_size"],

            "id_build_time":
                id_result["build_time"],

            "id_max_error":
                id_result[
                    "max_selectivity_error"
                ]
        })

    # --------------------------------------------------------
    # FINAL Q2.5 SUMMARY
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("Q2.5 FINAL SUMMARY")
    print("=" * 80)

    print()

    for result in all_results:

        print(
            f"Requested sample size: "
            f"{result['requested_sample_size']}"
        )

        print(
            f"  title:"
        )

        print(
            f"    actual N       = "
            f"{result['title_sample_size']}"
        )

        print(
            f"    build time     = "
            f"{result['title_build_time']:.6f} seconds"
        )

        print(
            f"    max error      = "
            f"{result['title_max_error']:.12f}"
        )

        print(
            f"  id:"
        )

        print(
            f"    actual N       = "
            f"{result['id_sample_size']}"
        )

        print(
            f"    build time     = "
            f"{result['id_build_time']:.6f} seconds"
        )

        print(
            f"    max error      = "
            f"{result['id_max_error']:.12f}"
        )

        print()