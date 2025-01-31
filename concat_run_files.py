from collections import defaultdict
import os
import random
import pandas as pd
import time
from google.cloud import storage
import io
import psutil
import argparse


def get_memory_usage():
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024**3)  # Convert to GB


# generate data reader function
def read_data(file_paths):
    all_run_data = pd.DataFrame()  # df of data
    for file in file_paths:
        single_file_data = pd.read_csv(file, header=1)  # read and append to data
        all_run_data = pd.concat([all_run_data, single_file_data], ignore_index=True)
    return all_run_data


########## TO EDIT - Add UUIDs ###########

# # generate function to prepare fastbcr_input from data object
# def oas_to_fastbcr(data):
# 	# generates fastbcr_input
# 	# returns fastbcr data


def write_to_gcs(data, path):
    """
    Write a pandas DataFrame to a CSV file in a GCP bucket.

    Parameters:
    - data (pd.DataFrame): The pandas DataFrame to write.
    - path (str): The GCS path where the file will be written, in the format "bucket_name/folder_name/file_name.csv".

    Returns:
    - None
    """
    if not path.endswith(".csv"):
        path += ".csv"

    # Split the GCS path into bucket and blob (object path)
    bucket_name, *blob_path = path.split("/", 1)
    blob_path = blob_path[0] if blob_path else ""

    if not bucket_name or not blob_path:
        raise ValueError(
            "Invalid GCS path format. Expected 'bucket_name/path_to_file.csv'."
        )

    # Create an in-memory file-like buffer for the CSV
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)  # Move the pointer to the start of the buffer

    # Initialize a GCS client
    client = storage.Client()

    # Get the bucket and blob
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Upload the CSV content to GCS
    blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")

    print(f"DataFrame successfully written to {path}")


def pipeline(file_paths, out_path):
    data = read_data(file_paths)
    # fastbcr_data = oas_to_fastbcr(data)
    write_to_gcs(data, out_path)


def test_read_write():
    # Testing of read_data and write_to_gcs functions
    file = [
        "/export/share/cameronhu/oas/unpaired/unpaired_human/unpaired_human_heavy/batch_1/1279049_1_Heavy_Bulk.csv.gz"
    ]
    run_file = "1279049_1_Heavy_Bulk.csv.gz"

    out_bucket = "proevo-ab/lineages/fastbcr/input/runs"
    run_id = run_file.split("_")[0]

    test_data = read_data(file)
    print(test_data)
    out_dir = os.path.join(out_bucket, run_id)
    write_to_gcs(test_data, out_dir)


if __name__ == "__main__":

    # Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=str)
    parser.add_argument("input_dir", type=str)
    parser.add_argument("output_dir", type=str)
    parser.add_argument("--max_sequences", type=int)

    run_to_files = ...
    out_dir = "proevo-ab/lineages/fastbcr/input/runs"

    # Select the first n runs from the dictionary
    num_runs = 10
    # run_ids = dict(itertools.islice(run_to_files.items(), num_runs))
    random_run_ids = random.sample(list(run_to_files.items()), num_runs)
    run_ids = dict(random_run_ids)
    print(run_ids)

    # Track the total processing time
    start_total = time.time()

    # Process each run
    for run, file_paths in run_ids.items():
        start = time.time()
        initial_memory = get_memory_usage()
        output_path = os.path.join(out_dir, run)
        print(output_path)

        # Run the pipeline for the given file paths and output path
        pipeline(file_paths, output_path)

        # Calculate memory usage
        final_memory = get_memory_usage()
        max_memory_used = final_memory - initial_memory

        end = time.time()
        print(f"Time for {run}: {end - start:.2f} seconds")
        print(f"Max memory utilized for {run}: {max_memory_used:.2f} GB")

    # Calculate and print the total processing time
    end_total = time.time()
    print(f"Total time for {num_runs} runs: {end_total - start_total:.2f} seconds")


# def parallel_process(run_to_files, out_dir):
#     def process_run(run_id, file_paths):
#         try:
#             print(f"Processing run {run_id}...")
#             output_path = os.path.join(out_dir, f"{run_id}_output")
#             pipeline(file_paths, output_path)
#             print(f"Completed run {run_id}")
#         except Exception as e:
#             print(f"Error in run {run_id}: {e}")

#     with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
#         tasks = [(run_id, file_paths) for run_id, file_paths in run_to_files.items()]
#         results = [pool.apply_async(process_run, args=(run_id, file_paths)) for run_id, file_paths in tasks]
#         for result in results:
#             result.get()

# #if __name__ == "__main__":
# #    run_to_files = list_samples()
# #    out_dir = "/path/to/output"
# #    parallel_process(run_to_files, out_dir)
