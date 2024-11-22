import argparse
import tempfile
import sys
import os
import Bio.SeqIO
import sys
import os
import gzip
import json
import time
import numpy as np
import shutil
import multiprocessing as mp
import subprocess as sp

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


class Pipeline:
    def __init__(self):
        self.parse_args()
        self.fetch_inputs()
        pprint(self.args)

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

        self.run_to_files = run_to_files

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

    def run_main(self):
        for input in self.input_list:
            try:
                self.main(input)
                print(f"input: {input}: success")
            except Exception as error:
                print(f"input: {input}: failure: {error}")

    def main(self, input, threads=1):
        # parse inputs
        input = input.replace("gs://", "")
        gcs_bucket, gcs_path = input.split("/", 1)
        run_name = os.path.basename(gcs_path).replace(".csv", "")

        # make tmpdir
        tmp_dir = os.path.join(self.args["tmp_dir"], run_name)
        os.makedirs(tmp_dir, exist_ok=True)

        # copy input
        dst_name = f"{tmp_dir}/{os.path.basename(gcs_path)}"
        gcs_copy(gcs_bucket, gcs_path, dst_name)

        # run fastbr
        # ....
        # ....
        # ....

        files = ["ERR4077973.csv"]
        dst_dir = f"lineages/fastbcr/output/runs/{run_name}"
        for file in files:
            gcs_upload(
                src_name=os.path.join(tmp_dir, file),  # path to file in tmp_dir
                bucket_name=gcs_bucket,  # destination gcs_bucket
                dst_name=os.path.join(dst_dir, file),
            )

        # clean up
        shutil.rmtree(f"{tmp_dir}")


if __name__ == "__main__":

    pipeline = Pipeline()
    pipeline.run_main()


# Have to set BATCH_TASK_INDEX ENV variable

"""
The Docker container should have an entrypoint into this Python script. This Python script requires additional arguments, hence the argparse().
These additional arguments include --batch_input, --batch_size, and --BATCH_TASK_INDEX
However, these additional arguments should be supplied by the GCP Batch job script.
"""
