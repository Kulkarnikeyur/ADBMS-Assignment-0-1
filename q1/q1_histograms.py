import pandas as pd
import matplotlib.pyplot as plt
import re
import ast


df = pd.read_csv("q1_histogram_boundaries.csv")

# attribute = "id"
# numeric = True
attribute = "title"
numeric = False
row = df[df["attname"] == attribute].iloc[0]


bounds_string = row["histogram_bounds"]


bounds_string = bounds_string.strip("{}")
bounds = [x.strip() for x in bounds_string.split(",")]

# Convert numeric boundaries to numbers
try:
    bounds = [float(x) for x in bounds]
except ValueError:
    # For string-valued attributes such as title
    bounds = [x.strip('"') for x in bounds]

# 3. Number of buckets
num_buckets = len(bounds) - 1

# 4. Frequency
# For an equi-depth histogram, every bucket has approximately the same number of tuples.

N = 2528312

frequency = N / num_buckets

frequencies = [frequency] * num_buckets

if numeric:

    # ----------------------------------------------
    # NUMERIC ATTRIBUTE (e.g. id)
    # ----------------------------------------------

    for i in range(num_buckets):

        left = bounds[i]
        right = bounds[i + 1]

        plt.bar(
            left,
            frequencies[i],
            width=right - left,
            align="edge",
            edgecolor="black",
            color="blue"
        )

    # Show only every nth boundary
    step = 5

    tick_positions = bounds[::step]
    tick_labels = [str(int(x)) for x in tick_positions]

    plt.xticks(
        tick_positions,
        tick_labels,
        rotation=45,
        ha="right"
    )

else:

    # ----------------------------------------------
    # STRING ATTRIBUTE (e.g. title)
    # ----------------------------------------------

    # Give each boundary a numerical position
    positions = list(range(len(bounds)))

    # Draw bars between consecutive boundaries
    for i in range(num_buckets):

        plt.bar(
            i,
            frequencies[i],
            width=1,
            align="edge",
            edgecolor="black",
            color="blue"
        )

    # Show only every nth boundary
    step = 2

    tick_positions = positions[::step]
    tick_labels = bounds[::step]

    plt.xticks(
        tick_positions,
        tick_labels,
        rotation=45,
        ha="right"
    )


plt.xlabel("Value Boundaries")
plt.ylabel("Frequency")
plt.title(f"Histogram of {attribute}")

plt.tight_layout()
plt.show()
