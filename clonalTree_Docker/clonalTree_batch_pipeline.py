import argparse
import tempfile
import sys
import os
import sys
import os
import gzip
import json
import time
import shutil
import multiprocessing as mp
import subprocess as sp
import gc
import csv

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


def gcs_file_exists(bucket_name, file_path):
    """
    Check if a specific file exists in a GCS bucket.

    Args:
        bucket_name (str): Name of the GCS bucket.
        file_path (str): Path to the file within the bucket.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    client = storage.Client(project="profluent-evo")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.exists()


def gcs_list_files(bucket_name, dst_name):
    # Initialize the GCS client
    client = storage.Client(project="profluent-evo")

    # Access the bucket
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=dst_name)

    # List and return all file names
    files = [
        blob.name for blob in blobs if not blob.name.endswith("/")
    ]  # Exclude directories
    return files


def run_clonalTree(input_fasta, output_path):
    """
    Run the modified R script with input and output folder arguments.

    Parameters:
        input_fasta (str): Path to the input FASTA file
        output_path (str): Path to save the output
    """
    try:
        # Run
        result = sp.run(
            [
                "python",
                "ClonalTree/src/clonalTree.py",
                "-i",
                input_fasta,
                "-o",
                output_path,
                "-a",
                "1",
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
        The batch_input is a txt file listing all the FASTA file inputs for ClonalTree
        Parses the appropriate number of FASTA files and saves as self.input_list

        Populates:
            self.run_to_files (dict): Dictionary mapping run IDs to their corresponding list of file paths.
        """
        input_start = self.args["batch_size"] * self.args["batch_task_index"]
        input_stop = input_start + self.args["batch_size"]

        # Check if the input file exists locally
        if os.path.exists(self.args["batch_input"]):
            with open(self.args["batch_input"]) as f:
                input_list = f.read().splitlines()
        else:
            # Parse GCS input file
            bucket, path = self.args["batch_input"].split("/", 1)
            # Return a list of FASTA filepaths
            input_list = gcs_read(bucket, path).split("\n")

        # Save the input_list as attribute
        self.input_list = input_list[input_start:input_stop]

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

        # Each input is a path to a FASTA file input to ClonalTree
        for input in self.input_list:

            # parse inputs
            input = input.replace("gs://", "")
            gcs_bucket, gcs_path = input.split("/", 1)
            run_name = input.split("/")[-2]
            tmp_dir = os.path.join(self.args["tmp_dir"], run_name)

            # Check if the output file for this input already exists. If so, skip this input
            # Generate the output directory and file path specific to this input
            output_dir = f"lineages/clonalTree/output/runs/{run_name}"
            output_file_name = (
                f"{run_name}_{os.path.basename(gcs_path).replace('.fasta', '.abRT.nk')}"
            )
            output_file_path = os.path.join(output_dir, output_file_name)

            # Check if the output file for this input already exists. If so, skip this input
            if gcs_file_exists(gcs_bucket, output_file_path):
                print(
                    f"Output file {output_file_path} already exists. Skipping input {input}."
                )
                continue

            # make tmp_dir
            clonalTree_input_dir = os.path.join(tmp_dir, "clonalTree_input")
            clonalTree_output_dir = os.path.join(tmp_dir, "clonalTree_output")
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(clonalTree_input_dir, exist_ok=True)
            os.makedirs(clonalTree_output_dir, exist_ok=True)

            ###############################

            # Download ClonalTree input files into temp
            dst_name = os.path.join(
                clonalTree_input_dir, f"{run_name}_{os.path.basename(input)}"
            )
            gcs_copy(gcs_bucket, gcs_path, dst_name)

            # run ClonalTree, saving output to clonalTree_output_dir

            for file_name in os.listdir(clonalTree_input_dir):
                # Generate input path
                fasta_path = os.path.join(clonalTree_input_dir, file_name)

                # Generate output path
                # Parse the family name from the input_fasta path
                output_file_name = os.path.basename(fasta_path).replace(
                    ".fasta", ".abRT.nk"
                )
                output_file_path = os.path.join(clonalTree_output_dir, output_file_name)

                run_clonalTree(fasta_path, output_file_path)

            gcs_dst_dir = f"lineages/clonalTree/output/runs/{run_name}"

            # Iterate over the files in the output directory
            for file_name in os.listdir(clonalTree_output_dir):
                file_path = os.path.join(clonalTree_output_dir, file_name)

                # Check if it's a file (ignore directories)
                if os.path.isfile(file_path):
                    gcs_upload(
                        src_name=file_path,  # Path to file in fastBCR_output_directory
                        bucket_name=gcs_bucket,  # Destination GCS bucket
                        dst_name=os.path.join(
                            gcs_dst_dir, file_name
                        ),  # Destination path in GCS
                    )

        # clean up
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":

    pipeline = Pipeline()
    pipeline.main()
