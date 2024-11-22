import argparse
import tempfile
import sys
import os
import sys
import os
import gzip
import json
import time
import numpy as np
import shutil
import multiprocessing as mp
import subprocess as sp
import pandas as pd
import gc

from pprint import pprint
from google.cloud import storage

__version__ = "0.0.1"


def gcs_copy(bucket_name, src_name, dst_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(src_name)
    blob.download_to_filename(dst_name)


def gcs_upload(src_name, bucket_name, dst_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dst_name)
    blob.upload_from_filename(src_name)


def gcs_read(bucket_name, src_name):
    client = storage.Client()
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
        None
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

    # Define output file name and path
    output_file_name = f"{run}_ALL.csv"
    output_file_path = os.path.join(output_dir, output_file_name)

    # Write the final DataFrame to a CSV file
    all_run_data.to_csv(output_file_path, index=False)
    print(f"Data concatenated and written to {output_file_path}")
    print(f"# of sequences is {len(all_run_data)}")

    # Clear the DataFrame from memory
    del all_run_data
    del dataframes  # Clear the list of DataFrames
    gc.collect()  # Explicit garbage collection to reclaim memory
    print("Memory cleared.")


def run_fastBCR(input_folder, output_folder, r_script_path):
    """
    Run the modified R script with input and output folder arguments.

    Parameters:
        input_folder (str): Path to the input folder
        output_folder (str): Path to the output folder.
        r_script_path (str): Path to the fastBCR R script.
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


class Pipeline:
    def __init__(self):
        self.parse_args()
        self.fetch_inputs()
        # pprint(self.args)

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

        # Populate the run_to_files dictionary
        for line in batch_lines:
            if line.strip():  # Skip empty lines
                run_id, files_str = line.split("\t")
                run_to_files[run_id] = eval(
                    files_str
                )  # Convert stringified list to a Python list

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

            # make tmpdir
            run_name = run
            tmp_dir = os.path.join(self.args["tmp_dir"], run_name)
            concat_output_directory = os.path.join(tmp_dir, "fastBCR_input")
            fastBCR_output_directory = os.path.join(tmp_dir, "fastBCR_output")
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(concat_output_directory, exist_ok=True)
            os.makedirs(fastBCR_output_directory, exist_ok=True)

            # Download raw OAS input files into temp
            for input in file_list:
                input = input.replace("gs://", "")
                gcs_bucket, gcs_path = input.split("/", 1)
                # run_name = os.path.basename(gcs_path).replace(".csv", "")

                # copy input
                dst_name = f"{tmp_dir}/{os.path.basename(gcs_path)}"
                gcs_copy(gcs_bucket, gcs_path, dst_name)

            # Concatenate all run files into one, saved as tmp_dir/fastBCR_input/{run_name}_ALL.csv
            start_time = time.time()
            concat_data_from_directory(tmp_dir, run, concat_output_directory)
            end_time = time.time()

            print(
                f"Concatenating files to generate fastBCR input took {end_time - start_time} time"
            )

            # run fastbr

            # Testing with mounted lineage_tree volume
            run_fastBCR(
                input_folder=concat_output_directory,
                output_folder=fastBCR_output_directory,
                r_script_path="/lineage_tree/fastBCR_pipeline.R",
            )

            # run_fastBCR(
            #     input_folder=concat_output_directory,
            #     output_folder=fastBCR_output_directory,
            #     r_script_path="fastBCR_pipeline.R",
            # )

            # files = ["ERR4077973.csv"]
            # dst_dir = f"lineages/fastbcr/output/runs/{run_name}"
            # for file in files:
            #     gcs_upload(
            #         src_name=os.path.join(tmp_dir, file),  # path to file in tmp_dir
            #         bucket_name=gcs_bucket,  # destination gcs_bucket
            #         dst_name=os.path.join(dst_dir, file),
            #     )

        # clean up
        # shutil.rmtree(f"{tmp_dir}")


if __name__ == "__main__":

    pipeline = Pipeline()
    pipeline.main()


# Have to set BATCH_TASK_INDEX ENV variable

"""
The Docker container should have an entrypoint into this Python script. This Python script requires additional arguments, hence the argparse().
These additional arguments include --batch_input, --batch_size, and --BATCH_TASK_INDEX
However, these additional arguments should be supplied by the GCP Batch job script.
"""
