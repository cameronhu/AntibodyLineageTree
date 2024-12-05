import argparse
import tempfile
import sys
import os
import sys
import os
import time
import numpy as np
import shutil
import multiprocessing as mp
import subprocess as sp
import pandas as pd
import gc
import csv
import uuid

from pprint import pprint
from google.cloud import storage

__version__ = "0.0.1"


def gcs_copy(bucket_name, src_name, dst_name):
    client = storage.Client(project="profluent-evo")
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(src_name)
    blob.download_to_filename(dst_name)


def gcs_upload(src_name, bucket_name, dst_name):
    client = storage.Client(project="profluent-evo")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dst_name)
    blob.upload_from_filename(src_name)


def gcs_read(bucket_name, src_name):
    client = storage.Client(project="profluent-evo")
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(src_name)
    try:
        return blob.download_as_text()
    except Exception as e:
        print(f"Error reading file from GCS: {e}")
        return None


def concat_data_from_directory(directory_path, run, output_dir):
    """
    Reads and concatenates data from all files in a given directory into a single DataFrame.

     Args:
        directory_path (str): Path to the directory containing the files to be read.
        run (str): A string used to name the output file.
        output_dir (str): Path to the output directory

    Returns:
        num_seqs (int): Total number of unique sequences in this run
    """
    dataframes = []

    # List all files in the directory
    file_paths = [
        os.path.join(directory_path, file)
        for file in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, file))
    ]

    # Read and concatenate data from each file
    for file in file_paths:
        single_file_data = pd.read_csv(file, header=1)
        dataframes.append(single_file_data)

    all_run_data = pd.concat(dataframes, ignore_index=True)
    num_seqs = len(all_run_data)

    # Generate unique sequence_ids
    all_run_data["sequence_id"] = [str(uuid.uuid4()) for _ in range(num_seqs)]

    # Define output file name and path
    output_file_name = f"{run}_ALL.csv"
    output_file_path = os.path.join(output_dir, output_file_name)

    # Write the final DataFrame to a CSV file
    all_run_data.to_csv(output_file_path, index=False)
    print(f"Data concatenated and written to {output_file_path}")
    print(f"# of sequences is {num_seqs}")

    # Clear the DataFrame from memory
    del all_run_data
    del dataframes  # Clear the list of DataFrames
    gc.collect()  # Explicit garbage collection to reclaim memory
    print("Memory cleared.")

    return num_seqs


def run_fastBCR(input_folder, output_folder, r_script_path):
    """
    Run the modified R script with input and output folder arguments.

    Parameters:
        input_folder (str): Path to the input folder.
        output_folder (str): Path to the output folder.
        r_script_path (str): Path to the fastBCR R script.

    Raises:
        RuntimeError: If the R script fails.
    """
    try:
        result = sp.run(
            [
                "Rscript",
                r_script_path,
                "--input_folder",
                input_folder,
                "--output_folder",
                output_folder,
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        print("R script output:", result.stdout)
    except sp.CalledProcessError as e:
        print("Error running R script:", e.stderr)
        raise RuntimeError(f"fastBCR R script failed: {e.stderr}")


class Pipeline:
    def __init__(self):
        self.parse_args()
        self.fetch_inputs()

    def fetch_inputs(self):
        """
        Fetches the run-to-files mapping from the batch input file and stores it in self.run_to_files.
        It uses self.args['batch_input'] to locate the .tsv file and parses the data into a dictionary.
        Only parses the number of inputs as calculated by batch_size

        Populates:
            self.run_to_files (dict): Dictionary mapping run IDs to their corresponding list of file paths.
        """
        input_start = self.args["batch_size"] * self.args["batch_task_index"]
        input_stop = input_start + self.args["batch_size"]

        # Initialize run_to_files dictionary
        run_to_files = {}

        # Check if the input file exists locally or in GCS
        if os.path.exists(self.args["batch_input"]):
            with open(self.args["batch_input"], "r") as f:
                lines = f.readlines()
        else:
            # Parse GCS input file
            bucket, path = self.args["batch_input"].split("/", 1)
            tsv_content = gcs_read(bucket, path)
            lines = tsv_content.split("\n")

        # Exclude the header and fetch the relevant batch lines
        lines = lines[1:]  # Exclude header
        batch_lines = lines[input_start:input_stop]

        client = storage.Client(project="profluent-evo")
        gcs_dir = "lineages/fastbcr/output/runs/"

        # Populate the run_to_files dictionary
        for line in batch_lines:
            if line.strip():  # Skip empty lines
                run_id, files_str = line.split("\t")
                run_to_files[run_id] = eval(
                    files_str
                )  # Convert stringified list to a Python list

                # Check if the run_id exists as a folder in the specified GCS directory
                run_folder_path = f"{gcs_dir}{run_id}/"
                blobs = list(
                    client.list_blobs(
                        bucket_or_name="proevo-ab",
                        prefix=run_folder_path,
                        delimiter="/",
                    )
                )

                if blobs:
                    # If run_id folder exists in GCS, terminate the program
                    print("FastBCR already performed")
                    sys.exit(0)  # Exit the program successfully

        self.gcs_run_to_files = run_to_files

    def parse_args(self):

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--batch_task_index", type=int, default=os.environ.get("BATCH_TASK_INDEX")
        )
        parser.add_argument("--batch_size", type=int)
        parser.add_argument("--batch_input", type=str)
        parser.add_argument("--cpu_count", type=int, default=os.cpu_count())
        parser.add_argument("--tmp_dir", type=str, default=tempfile.mkdtemp())
        args = vars(parser.parse_args())
        required = ["batch_task_index", "batch_size", "batch_input"]
        for field in required:
            if args[field] is None:
                sys.exit("Error: required field missing: %s" % field)
        self.args = args

    def main(self, threads=1):

        # pprint(self.gcs_run_to_files)
        for run, file_list in self.gcs_run_to_files.items():

            start_time = time.time()

            # make tmpdir
            run_name = run
            tmp_dir = os.path.join(self.args["tmp_dir"], run_name)
            concat_output_directory = os.path.join(tmp_dir, "fastBCR_input")
            fastBCR_output_directory = os.path.join(tmp_dir, "fastBCR_output")
            clonotype_temp_dir = os.path.join(tmp_dir, "fastBCR_clonotypes")
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(concat_output_directory, exist_ok=True)
            os.makedirs(fastBCR_output_directory, exist_ok=True)
            os.makedirs(clonotype_temp_dir, exist_ok=True)

            try:
                # Download raw OAS input files into temp
                for input in file_list:
                    input = input.replace("gs://", "")
                    gcs_bucket, gcs_path = input.split("/", 1)
                    # run_name = os.path.basename(gcs_path).replace(".csv", "")

                    # copy input
                    dst_name = f"{tmp_dir}/{os.path.basename(gcs_path)}"
                    gcs_copy(gcs_bucket, gcs_path, dst_name)

                # Concatenate all run files into one, saved as tmp_dir/fastBCR_input/{run_name}_ALL.csv

                num_seqs = concat_data_from_directory(
                    tmp_dir, run, concat_output_directory
                )

                # run fastbr
                run_fastBCR(
                    input_folder=concat_output_directory,
                    output_folder=fastBCR_output_directory,
                    r_script_path="fastBCR_pipeline.R",
                )

                # Move generated summary file to tmp_dir
                # Path to the generated single_cluster_summary.csv
                summary_file_path = os.path.join(
                    fastBCR_output_directory, "single_cluster_summary.csv"
                )
                if os.path.exists(summary_file_path):
                    # Move the file from the output folder to tmp_dir
                    moved_summary_file = os.path.join(
                        tmp_dir, "single_cluster_summary.csv"
                    )
                    shutil.move(summary_file_path, moved_summary_file)
                    summary_file_path = moved_summary_file
                    print(f"Moved single_cluster_summary.csv to {summary_file_path}")

                # Move all additional CSV files to the temporary clonotype directory
                for file_name in os.listdir(fastBCR_output_directory):
                    file_path = os.path.join(fastBCR_output_directory, file_name)
                    if file_name.endswith(".csv") and os.path.isfile(file_path):
                        shutil.move(
                            file_path, os.path.join(clonotype_temp_dir, file_name)
                        )

                # Upload all clonotype-related CSV files to GCS
                clonotype_gcs_dir = f"lineages/fastbcr/output/run_clonotypes/{run_name}"
                for file_name in os.listdir(clonotype_temp_dir):
                    file_path = os.path.join(clonotype_temp_dir, file_name)
                    gcs_upload(
                        src_name=file_path,
                        bucket_name=gcs_bucket,
                        dst_name=os.path.join(clonotype_gcs_dir, file_name),
                    )
                print(f"Uploaded clonotype CSVs to {clonotype_gcs_dir}")

                gcs_dst_dir = f"lineages/fastbcr/output/runs/{run_name}"

                # If there aren't any fastBCR outputs
                if len(os.listdir(fastBCR_output_directory)) == 0:
                    # Create a dummy file to ensure the directory exists
                    dummy_file_path = os.path.join(
                        fastBCR_output_directory, "no_fastBCR.txt"
                    )
                    with open(dummy_file_path, "w") as f:
                        f.write("")  # Create an empty file

                    # Upload the dummy file to create the folder in GCS
                    gcs_upload(
                        src_name=dummy_file_path,  # Path to the dummy file
                        bucket_name=gcs_bucket,  # Destination GCS bucket
                        dst_name=os.path.join(
                            gcs_dst_dir, "no_fastBCR.txt"
                        ),  # Destination path in GCS
                    )
                    os.remove(dummy_file_path)

                # Iterate over the files in the output directory
                for file_name in os.listdir(fastBCR_output_directory):
                    file_path = os.path.join(fastBCR_output_directory, file_name)

                    # Check if it's a file (ignore directories)
                    if os.path.isfile(file_path):
                        gcs_upload(
                            src_name=file_path,  # Path to file in fastBCR_output_directory
                            bucket_name=gcs_bucket,  # Destination GCS bucket
                            dst_name=os.path.join(
                                gcs_dst_dir, file_name
                            ),  # Destination path in GCS
                        )

                end_time = time.time()

                # If summary statistics exist
                # Read the summary CSV file into a pandas DataFrame
                # Write to a CSV
                # Upload to GCS
                if os.path.exists(summary_file_path):
                    summary_df = pd.read_csv(summary_file_path)
                    summary_data = summary_df.iloc[0]

                    data_dic = {
                        "run": run_name,
                        "num_seqs": num_seqs,
                        "time": start_time - end_time,
                        "number_of_clusters": summary_data["number.of.clusters"],
                        "average_size_of_clusters": summary_data[
                            "average.size.of.clusters"
                        ],
                        "number_of_clustered_seqs": summary_data[
                            "number.of.clustered.seqs"
                        ],
                        "number_of_all_seqs": summary_data["number.of.all.seqs"],
                        "proportion_of_clustered_sequences": summary_data[
                            "proportion.of.clustered.sequences"
                        ],
                    }

                    # Write statistics to GCS
                    statistics_file_path = os.path.join(
                        tmp_dir, f"{run_name}_run_statistics.csv"
                    )

                    # Write data_dic to CSV file
                    # Open the file in append mode to add data without overwriting existing entries
                    with open(statistics_file_path, mode="w", newline="") as file:
                        # Define the fieldnames based on the keys of the dictionary
                        fieldnames = data_dic.keys()

                        # Create a DictWriter object
                        writer = csv.DictWriter(file, fieldnames=fieldnames)

                        # If the file is empty (i.e., it doesn't exist or is new), write the header
                        writer.writeheader()

                        # Write the dictionary to the CSV file
                        writer.writerow(data_dic)

                    print(f"Data written to {statistics_file_path}")

                    stats_gcs_dir = f"lineages/fastbcr/output/run_stats"
                    stats_basename = f"{run_name}_run_statistics.csv"
                    gcs_upload(
                        src_name=statistics_file_path,  # Path to file in fastBCR_output_directory
                        bucket_name=gcs_bucket,  # Destination GCS bucket
                        dst_name=os.path.join(
                            stats_gcs_dir, stats_basename
                        ),  # Destination path in GCS
                    )
            except RuntimeError as e:
                print(
                    f"Pipeline terminated due to lack of sequences to cluster in Rscript: {e}"
                )

        # clean up
        shutil.rmtree(f"{tmp_dir}")


if __name__ == "__main__":

    pipeline = Pipeline()
    pipeline.main()


# Have to set BATCH_TASK_INDEX ENV variable

"""
The Docker container should have an entrypoint into this Python script. This Python script requires additional arguments, hence the argparse().
These additional arguments include --batch_input, --batch_size, and --BATCH_TASK_INDEX
However, these additional arguments should be supplied by the GCP Batch job script.
"""
