import matplotlib.pyplot as plt

sample_sizes = [981, 2809, 4827]

id_errors = [
    0.0,
    0.0,
    0.0
]

title_errors = [
    0.0,
    0.0,
    0.0
]

plt.figure(figsize=(8, 5))

plt.plot(
    sample_sizes,
    id_errors,
    marker="o",
    label="id"
)

plt.plot(
    sample_sizes,
    title_errors,
    marker="o",
    label="title"
)

plt.xlabel("Sample Size")
plt.ylabel("Maximum Selectivity Error")
plt.title("Sample Size vs Maximum Selectivity Error")

plt.xticks(sample_sizes)

plt.grid(True)
plt.legend()

plt.tight_layout()

plt.savefig(
    "q2_8_sample_size_vs_max_selectivity_error.png",
    dpi=300
)

plt.show()