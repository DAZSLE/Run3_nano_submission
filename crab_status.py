"""
Crab status utility
"""

from pathlib import Path
import argparse
import os
import subprocess
import csv
import re
import yaml
import sys
import numpy as np
import matplotlib.pyplot as plt

from datasets.utils import add_bool_arg, print_red
from datasets.get_datasets import DATASETS, YEARS
from datasets.get_mc import SAMPLES


def get_crab_info(directory: Path):
    try:
        # Run crab status command
        result = subprocess.run(
            ["crab", "status", "-d", str(directory)], capture_output=True, text=True, check=True
        )
        output = result.stdout
        # Add error message of cmsenv and grid_certificate if not initiated already by the user
    except subprocess.CalledProcessError as e:
        output = e.stdout.decode("utf-8")

    # Extract relevant information from the output
    finished_values = re.findall(r"finished\s+(\d+\.\d+)%", output)
    jobs_status = float(finished_values[-1]) if finished_values else "0"
    output_dataset = next(
        (line.split()[2] for line in output.splitlines() if "Output dataset:" in line), "N/A"
    )

    return jobs_status, output_dataset


def main(args):
    print("")

    datasets = []
    subsamples = []
    job_status = []

    plot_dir = Path("ProgressPlots")
    csv_file = Path("CrabStatus.csv")

    # Create the header in the consolidated CSV file
    with csv_file.open("w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Dataset", "Subsample","Jobs Status", "Output Dataset"])

    # Loop through the years and samples
    for year in args.years:
        for sample in args.samples:
            isData = sample in DATASETS
            datamc_label = "data" if isData else "mc"
            dir_name = f"{datamc_label}_{year}_{sample}"
            dir_path = Path("crab") / dir_name

            print("Checking", dir_name)
            if not dir_path.exists():
                print_red(f"{dir_path} does not exist!")
                continue

            # Generate a list of directories in the specified path
            directory_list = [d for d in dir_path.iterdir() if d.is_dir() and "crab" in d.name]

            for directory in directory_list:
                print("\tCrab status for", directory)
                jobs_status, output_dataset = get_crab_info(directory)
                print(f"\t\tJob status: {jobs_status}")
                # print(f"\t\tOutput dataset: {output_dataset}")

                datasets.append(dir_name)
                subsamples.append(directory.name[5:-8]) # remove "crab_" and "_MINIAOD"
                job_status.append(float(jobs_status))

                # Append the information to the consolidated CSV file
                with open(csv_file, "a", newline="") as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([directory.name[5:-8], jobs_status, output_dataset])

            # plotter(dir_name, job_status, filename=plot_dir / f"{dir_name}.pdf")

    print(f"Status saved to {csv_file}.")



def plotter(sample, status, filename=None):
    # Define color thresholds
    color_thresholds = [0.0, 25.0, 50.0, 75.0, 90.0, 98.0, 101.0]
    colors = ["red", "orange", "yellow", "lightgreen", "mediumseagreen", "darkgreen"]

    # Assign colors based on the percentage ranges
    bar_colors = []
    for i, percentage in enumerate(status):
        digitized_index = np.digitize(percentage, color_thresholds) - 1
        if 0 <= digitized_index < len(colors):
            bar_colors.append(colors[digitized_index])
        else:
            # Handle the case where the index is out of bounds
            print("Warning: Index out of bounds for percentage:", percentage)
            bar_colors.append("grey")
        sample[i] = sample[i] + "\n" + str(round(float(percentage), 1))

    # Set figure size and resolution
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)

    # Create a 2D plot with custom color
    plt.barh(sample, status, color=bar_colors)
    plt.xlabel("Average Percentage")
    plt.ylabel("Sample Names")
    plt.title("Progress in Each Sample")

    # Add grid lines
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    # Add more tickers for finer bins
    ax.set_xticks(np.arange(0, 101, 5))

    # Add percentage symbols to x-axis ticks
    ax.set_xticklabels([f"{x}%" for x in np.arange(0, 101, 5)])
    ax.axvline(100.0, color="r", lw=2)
    # Add legend
    legend_labels = ["<25%", "25-50%", "50-75%", "75-90%", "90-98%", ">98%"]
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    plt.legend(
        legend_handles,
        legend_labels,
        bbox_to_anchor=(0, 1.02, 1, 0.2),
        loc="lower left",
        mode="expand",
        borderaxespad=0,
        ncol=6,
    )
    plt.tight_layout()

    # Save the figure
    if filename:
        plt.savefig(filename)
        plt.close()
    else:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check crab status for a given year and sample")
    parser.add_argument(
        "--years",
        type=str,
        nargs="+",
        default=YEARS,
        choices=YEARS,
        help="Year to check status for (default: all years)",
    )
    parser.add_argument(
        "--samples",
        type=str,
        nargs="+",
        required=True,
        choices=list(SAMPLES.keys()) + list(DATASETS.keys()),
        help="List of samples to check, e.g. JetMET, HH4b",
    )
    args = parser.parse_args()

    main(args)
