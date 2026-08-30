import matplotlib.pyplot as plt

sample_sizes = [981, 2809, 4827]

id_times = [
    46.481996,
    486.547166,
    1156.711741
]

title_times = [
    48.719692,
    434.904839,
    1207.060048
]

plt.figure(figsize=(8, 5))

plt.plot(
    sample_sizes,
    id_times,
    marker="o",
    label="id"
)

plt.plot(
    sample_sizes,
    title_times,
    marker="o",
    label="title"
)

plt.xlabel("Sample Size")
plt.ylabel("Histogram Construction Time (seconds)")
plt.title("Sample Size vs Histogram Construction Time")

plt.xticks(sample_sizes)
plt.grid(True)
plt.legend()

plt.tight_layout()

plt.savefig(
    "q2_7_sample_size_vs_time.png",
    dpi=300
)

plt.show()