from google.cloud import storage
from collections import defaultdict
import os


def list_samples_gcs(input_dir, output_path):
    """
    Lists files in a GCP bucket directory and organizes them by 'run_id', then writes a TSV to GCS.

    Args:
        input_dir (str): GCS directory path
        output_path (str): GCS path for the output TSV file
    """
    # Parse the input GCS path
    bucket_name, prefix = input_dir.split("/", 1)
    if prefix.endswith("/"):
        prefix = prefix[:-1]

    # Initialize GCS client and bucket
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Dictionary to store run IDs and corresponding file paths
    run_to_files = defaultdict(list)

    # List all objects under the prefix
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        if not blob.name.endswith("/"):  # Skip directories
            file_name = os.path.basename(blob.name)
            run_id = file_name.split("_")[0]  # Extract run_id from filename
            file_path = f"gs://{bucket_name}/{blob.name}"
            run_to_files[run_id].append(file_path)

    # Prepare the TSV content
    tsv_lines = ["run_id\tfile_paths"]
    for run_id, files in run_to_files.items():
        files_list = str(files)
        tsv_lines.append(f"{run_id}\t{files_list}")
    tsv_content = "\n".join(tsv_lines)

    # Upload the TSV to the output GCS path
    output_bucket_name, output_key = output_path.replace("gs://", "").split("/", 1)
    output_bucket = client.bucket(output_bucket_name)
    output_blob = output_bucket.blob(output_key)
    output_blob.upload_from_string(tsv_content)

    print(f"TSV file successfully written to {output_path}")


if __name__ == "__main__":

    list_samples_gcs(
        input_dir="proevo-ab/oas/unpaired/unpaired_human/unpaired_human_heavy",
        output_path="gs://proevo-ab/lineages/fastbcr/batch/run_to_files.tsv",
    )
