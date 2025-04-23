import os
import subprocess
import csv
import re
import yaml
import pandas as pd
import sys
import numpy as np
import matplotlib.pyplot as plt

def get_crab_info(directory):
    try:
        # Run crab status command
        result = subprocess.run(['crab', 'status', '-d', directory], capture_output=True, text=True, check=True)
        output = result.stdout
        #Add error message of cmsenv and grid_certificate if not initiated already by the user
    except subprocess.CalledProcessError as e:
        output = e.stdout.decode('utf-8')

    # Extract relevant information from the output
    finished_values = re.findall(r'finished\s+(\d+\.\d+)%', output)
    jobs_status = float(finished_values[-1]) if finished_values else '0'
    output_dataset = next((line.split()[2] for line in output.splitlines() if 'Output dataset:' in line), 'N/A')

    return jobs_status, output_dataset

########The following function is not very nice and can cause user dependent issues: better ideas required########
def modify_das_path(das_path):
    parts = das_path.split('/')
    if len(parts) >= 4:
        # Find the index of the first occurrence of "-"
        first_dash_index = parts[2].find("-")
        if first_dash_index != -1:
            parts[2] = parts[2][first_dash_index + 1:]
        substring_to_drop = "_BTV_Run3"
        start_index = parts[2].find(substring_to_drop)
        if start_index != -1:
            parts[2] = parts[2][:start_index]
        modified_path = f'/{parts[1]}/{parts[2]}/MINIAODSIM'
        modified_plotpath = f'{parts[1]}'
        return modified_path, modified_plotpath 
##############################################################################    

def main(base_path, output_path, yaml_path, csv_ext):
    # Specify the name of the CSV file
    need_to_copy=None
    if not os.path.exists(output_path):
        need_to_copy="root://eosuser.cern.ch/"+output_path
        output_path=os.getcwd()
        os.system("mkdir -p csvoutputs/")
        os.system("mkdir -p ProgressPlots/")
    csv_file = os.path.join(output_path, f'csvoutputs/crab_info_{csv_ext}.csv')
    png_file = os.path.join(output_path, f'ProgressPlots/{csv_ext}.png')

    # Create the header in the consolidated CSV file
    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Dataset', 'Jobs Status', 'DAS Path'])

    # Load YAML data
    with open(yaml_path) as yaml_file:  
        yaml_data = yaml.safe_load(yaml_file)
    # Extract the list from the YAML file
    yaml_list_str = yaml_data['campaign']['datasets']
    yaml_list = [item.strip() for item in yaml_list_str.split('\n')] if isinstance(yaml_list_str, str) else []

    # Generate a list of directories in the specified path
    directory_list = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and 'crab' in d]
    data_list = []
    job_status = []
    sample_name = []
    # Loop through the directory list and get crab info for each directory
    for directory in directory_list:
        print(f"Running crab status for directory: {directory}")
        directory_path = os.path.join(base_path, directory)
        jobs_status, output_dataset = get_crab_info(directory_path)
        print(f"Job status: {jobs_status}")

        # Modify the DAS Path
        modified_das_path, modified_plot_path  = modify_das_path(output_dataset)
        data_list.append(modified_das_path)
        job_status.append(float(jobs_status))
        sample_name.append(modified_plot_path)

        # Append the information to the consolidated CSV file
        with open(csv_file, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([modified_das_path, jobs_status, output_dataset])
    print(f'csv file created and saved in the www eos area. Every execution will overwrite the previous csv.: {csv_file}')
    #print(data_list)
    #Plot the progress bars for each job
    plotter(sample_name,job_status,filename=png_file)
    
    # Find in YAML list that are missing in modified_das_path
    missing_samples = [yaml_value for yaml_value in yaml_list if yaml_value not in data_list]
    # Print missing samples
    if missing_samples and missing_samples!=['']:
        for missing_sample in missing_samples:
            print(f"Samples missing in CSV: {missing_sample}")
    else:
        print("Nothing is missing for production.")
    if need_to_copy is not None:
        os.system(f"xrdcp -f  -p --silent csvoutputs/* {need_to_copy}/csvoutputs/.")
        os.system(f"xrdcp -f -p --silent ProgressPlots/* {need_to_copy}/ProgressPlots/.")
def plotter(sample, status, filename=None):
    # Define color thresholds
    color_thresholds = [0.0, 25.0, 50.0, 75.0, 90.0, 98.0, 101.0]
    colors = ['red', 'orange', 'yellow', 'lightgreen', 'mediumseagreen', 'darkgreen']

    # Assign colors based on the percentage ranges
    bar_colors = []
    for i,percentage in enumerate(status):
        digitized_index = np.digitize(percentage, color_thresholds) - 1
        if 0 <= digitized_index < len(colors):
            bar_colors.append(colors[digitized_index])
        else:
            # Handle the case where the index is out of bounds
            print("Warning: Index out of bounds for percentage:", percentage)
            bar_colors.append('grey')
        sample[i]=sample[i]+"\n"+str(round(float(percentage),1))

    # Set figure size and resolution
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)

    # Create a 2D plot with custom color
    plt.barh(sample, status, color=bar_colors)
    plt.xlabel('Average Percentage')
    plt.ylabel('Sample Names')
    plt.title('Progress in Each Sample')

    # Add grid lines
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    # Add more tickers for finer bins
    ax.set_xticks(np.arange(0, 101, 5))

    # Add percentage symbols to x-axis ticks
    ax.set_xticklabels([f'{x}%' for x in np.arange(0, 101, 5)])
    ax.axvline(100.,color='r',lw=2)
    # Add legend
    legend_labels = ['<25%', '25-50%', '50-75%', '75-90%', '90-98%', '>98%']
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    plt.legend(legend_handles, legend_labels,bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left",mode="expand", borderaxespad=0, ncol=6)
    plt.tight_layout()
    
    # Save the figure
    if filename:
        plt.savefig(filename)
    else:
        plt.show()

if __name__ == "__main__":
    import sys

    # Check if base_path and yaml_path are provided as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python crab_status.py <crab_dir_path> <crab_yml to compare>")
        sys.exit(1)

    base_path = sys.argv[1]
    csv_ext = os.path.basename(os.path.normpath(base_path))
    print(csv_ext)
    yaml_path = sys.argv[2]
    output_path = "/eos/user/b/btvweb/www/BTVNanoProduction/" 
    main(base_path, output_path,yaml_path,csv_ext)
