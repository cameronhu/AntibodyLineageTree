import subprocess
import pandas as pd


import subprocess
import pandas as pd
import gcsfs


def filter_batch_tsv(input_file, output_file):
    # Command to list directories in gs://proevo-ab/lineages/fastbcr/output/runs
    cmd = ["gsutil", "ls", "gs://proevo-ab/lineages/fastbcr/output/runs/"]

    # Run the command and capture output
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
    )

    # Parse out the run_ids from these directory names
    existing_run_ids = set()
    for line in result.stdout.strip().split("\n"):
        parts = line.strip().split("/")
        if parts[-1] == "":
            run_id = parts[-2]
        else:
            run_id = parts[-1]
        existing_run_ids.add(run_id)

    # Use gcsfs to handle files on GCS
    fs = gcsfs.GCSFileSystem()

    # Read the input file from GCS
    with fs.open(input_file, "r") as f:
        df = pd.read_csv(f, sep="\t", dtype=str)

    # Filter out rows whose run_id is in the existing_run_ids
    filtered_df = df[~df["run_id"].isin(existing_run_ids)]

    # Write the filtered DataFrame back to GCS
    with fs.open(output_file, "w") as f:
        filtered_df.to_csv(f, sep="\t", index=False)

    print(f"Filtered file written to {output_file}")


if __name__ == "__main__":

    filter_batch_tsv(
        input_file="gs://proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv",
        output_file="gs://proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_file_batch_5.tsv",
    )
