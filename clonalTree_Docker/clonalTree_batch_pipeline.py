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


def run_clonalTree(input_fasta):
    """
    Run the modified R script with input and output folder arguments.

    Parameters:
        input_folder (str): Path to the input folder
        output_folder (str): Path to the output folder.
        r_script_path (str): Path to the fastBCR R script.
    """
    try:

        # Parse the family name from the input_fasta path
        family_name = os.path.basename(input_fasta).replace(".fasta", "")

        # Output file name
        output_file = os.path.join()

        # Run
        result = sp.run(
            [
                "python",
                "src/clonalTree.py",
                "--i",
                input_fasta,
                "--o",
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

        # Check if the input file exists locally
        if os.path.exists(self.args["batch_input"]):
            input_list = [_.split() for _ in open(self.args["batch_input"])]
        else:
            # Parse GCS input file
            bucket, path = self.args["batch_input"].split("/", 1)
            input_list = [_.split("\t")[0] for _ in gcs_read(bucket, path).split("\n")]

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

        for input in self.input_list:

            # parse inputs
            input = input.replace("gs://", "")
            gcs_bucket, gcs_path = input.split("/", 1)
            run_name = input.split("/")[-2]

            # make tmp_dir
            tmp_dir = os.path.join(self.args["tmp_dir"], run_name)
            clonalTree_input_dir = os.path.join(tmp_dir, "clonalTree_input")
            clonalTree_output_dir = os.path.join(tmp_dir, "clonalTree_output")
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(clonalTree_output_dir, exist_ok=True)

            # Download ClonalTree input files into temp
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

            # run ClonalTree
            ...

            dst_dir = f"lineages/clonalTree/output/runs/{run_name}"

            upload_start_time = time.time()

            # Iterate over the files in the output directory
            for file_name in os.listdir(fastBCR_output_directory):
                file_path = os.path.join(fastBCR_output_directory, file_name)

                # Check if it's a file (ignore directories)
                if os.path.isfile(file_path):
                    gcs_upload(
                        src_name=file_path,  # Path to file in fastBCR_output_directory
                        bucket_name=gcs_bucket,  # Destination GCS bucket
                        dst_name=os.path.join(
                            dst_dir, file_name
                        ),  # Destination path in GCS
                    )

            upload_end_time = time.time()

            print(f"Upload time took {upload_end_time - upload_start_time} s")

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
