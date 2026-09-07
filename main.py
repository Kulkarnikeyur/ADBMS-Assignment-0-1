import subprocess
import sys
import os


def run_script(script_path):
    print("\n" + "=" * 70)
    print(f"RUNNING: {script_path}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=os.path.dirname(script_path) or None
    )

    if result.returncode != 0:
        print("\n" + "=" * 70)
        print(f"ERROR: {script_path} failed.")
        print("Stopping execution.")
        print("=" * 70)
        sys.exit(result.returncode)

    print("\n" + "=" * 70)
    print(f"COMPLETED: {script_path}")
    print("=" * 70)


def main():

    project_dir = os.path.dirname(os.path.abspath(__file__))

    scripts = [
        os.path.join(project_dir, "Q1", "q1_histograms.py"),

        os.path.join(project_dir, "Q2", "Optimal_serial_histo.py"),
        os.path.join(project_dir, "Q2", "error_plot.py"),
        os.path.join(project_dir, "Q2", "extrapolate.py"),
    ]

    for script in scripts:
        run_script(script)

    print("\n" + "=" * 70)
    print("ALL PROJECT TASKS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
