import runpy

print("=" * 80)
print("RUNNING Q2 SERIAL HISTOGRAM EXPERIMENTS")
print("=" * 80)

# Q2.5: construct the optimal serial histograms and generate histogram plots.
runpy.run_path("plot_serial_histograms(5).py", run_name="__main__")

print("\n" + "=" * 80)
print("GENERATING Q2.7 SAMPLE-SIZE VS BUILD-TIME PLOT")
print("=" * 80)
runpy.run_path("Q2_7.py", run_name="__main__")

print("\n" + "=" * 80)
print("GENERATING Q2.8 SAMPLE-SIZE VS MAX SELECTIVITY-ERROR PLOT")
print("=" * 80)
runpy.run_path("q2_8.py", run_name="__main__")

print("\n" + "=" * 80)
print("ALL Q2 CODE EXECUTED SUCCESSFULLY")
print("=" * 80)
