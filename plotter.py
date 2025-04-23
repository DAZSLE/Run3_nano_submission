import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set the directory where your CSV files are located
csv_directory = "/eos/user/b/btvweb/www/BTVNanoProduction/"

# Get a list of all CSV files in the directory
csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]

# Initialize lists to store data for plotting
csv_names = []
avg_percentages = []

# Loop through each CSV file
for csv_file in csv_files:
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(os.path.join(csv_directory, csv_file))

    # Get the average of the percentage column
    avg_percentage = df['Jobs Status'].mean()

    # Append data to lists
    csv_names.append(csv_file)
    avg_percentages.append(avg_percentage)

# Define color thresholds
color_thresholds = [0, 25, 50, 75, 90, 98, 100]
colors = ['red', 'orange', 'yellow', 'lightgreen', 'mediumseagreen', 'darkgreen']

# Assign colors based on the percentage ranges
bar_colors = [colors[np.digitize(percentage, color_thresholds) - 1] for percentage in avg_percentages]

# Extract file names without prefixes and extensions
csv_names = [csv_file.replace("crab_info_", "").replace(".csv", "") for csv_file in csv_names]

# Set figure size and resolution
fig, ax = plt.subplots(figsize=(15, 10), dpi=150)

# Create a 2D plot with custom colors
plt.barh(csv_names, avg_percentages, color=bar_colors)
plt.xlabel('Average Percentage')
plt.ylabel('Sample Names')
plt.title('Progress in Each Sample')

# Add grid lines
ax.grid(axis='x', linestyle='--', alpha=0.7)

# Add more tickers for finer bins
ax.set_xticks(np.arange(0, 101, 5))

# Add percentage symbols to x-axis ticks
ax.set_xticklabels([f'{x}%' for x in np.arange(0, 101, 5)])

# Add legend
legend_labels = ['<25%', '25-50%', '50-75%', '75-90%', '90-98%', '>98%']
legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
plt.legend(legend_handles, legend_labels, loc='lower right')

# Save the plot as a PNG file
plt.savefig("/eos/user/b/btvweb/www/BTVNanoProduction/overall_progress.png")

