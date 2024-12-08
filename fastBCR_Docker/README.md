# fastBCR Docker Container Dev

This Dockerfile builds a container on top of the `rocker/r-base:latest`, installing all necessary R dependencies to run fastBCR. Also installs a Python version so a Python script can execute the fastBCR pipeline script.

## Running fastBCR Production (Batch) Container

For testing and building the production container, `fastbcr:prod`, first navigate to the fastBCR_Docker dir, then run the following commands.

Build the container:
```
docker build -t fastbcr:prod .
```
Test container with bind mount of new fastBCR_batch_pipeline.py
```
docker run --rm -v /home/cameronhu/lineage_tree/fastBCR_Docker/fastBCR_batch_pipeline.py:/root/fastBCR_batch_pipeline.py fastbcr:prod_timing --batch_task_index=1 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv'
```

Test container without mounting of volume (production). Uses the input run_to_files list from GCP:
```
docker run --rm fastbcr:prod_timing --batch_task_index=1 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv' 
```

Test the container with mounting of volume:
```
docker run -it -v /home/cameronhu/lineage_tree:/lineage_tree fastbcr:prod --batch_task_index=0 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv'
```

Input list file GCP path: `proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv`


Building the Docker container and pushing to artifact repository:

```
docker build -f Dockerfile . -t fastbcr:prod
docker tag fastbcr:prod us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod
docker push us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod
```
## Dec 3rd v1.1.3 New Updates Container
```
docker build --no-cache -f Dockerfile . -t fastbcr:prod_timing
docker tag fastbcr:prod_timing us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod_timing
docker push us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod_timing
```

### fastBCR Batch job submission command
Run the following command in bash:
`gcloud beta batch jobs submit job-fastbcr-test[X] --location us-central1 --config batch_config.json`

## Running fastBCR Docker Test Container in interactive mode

A Docker container exits to run the fastBCR input generation and fastBCR pipeline: `fastbcr`. For timing purposes, run the following command to mount the `lineage_tree` repository to the container:

```
docker run -it -v /home/cameronhu/lineage_tree:/lineage_tree fastbcr bash
```

Then, within the container, run the following script to perform a timing test on the first 10 generated inputs:

```
cd ../lineage_tree;
chmod +x fastBCR_batch_timing_loop.sh
./fastBCR_batch_timing_loop.sh
tail -f timings_log.txt
```

## FastBCR Input Generation Notes

- `list_samples()` generates 3660 runs from just the human heavy chains. There are ~4000 runs total when querying the BigQuery db.
- Running pipeline on 64 GB had insufficient memory for run: "proevo-ab/lineages/fastbcr/input/runs/SRR8365422". Increased to 124GB and testing.
- Completed SRR8365422 at 124 GB, but was close to 100 GB of total memory. SRR8365422 has 4_545_677 unique  sequences, and 6_177_127 total sequences. ~950 seconds to complete this processing.
- SRR8365433 crashed memory, has 25,705,003 total sequences, ~5 million unique sequences
- Updated to 250 GB memory, was able to run SRR8283795 with 7.6 million unique sequences

### Batch Processing Notes

```
gsutil ls -d gs://proevo-ab/lineages/fastbcr/output/runs/*/ | wc -l
```

Counts the number of subdirectories within the `proevo-ab/lineages/fastbcr/output/runs/` directory on GCS. Each completed run should have a directory for it, even if there were no generated clonal families from fastBCR.
3463 runs out of 3660 completed with 32 GB memory. 197 additional runs needed for processing.

#### FastBCR Batch input generation filtering
`filter_fastBCR_batch_input.py` takes in the original `human_unpaired_heavy_run_to_files.tsv` batch_input file, and checks on GCS for any directories that have already been created corresponding to the run names in the input file. Creates a new filtered .tsv file on GCS within the `proevo-ab/lineages/fastbcr/batch` directory. This new filtered .tsv file should be used as future batch_input for next iterations of the fastBCR workflow with larger file sizes.

Batch 4 run with 64 GB memory, 8vCPU.

After Batch 4, 156 additional runs leftover in `human_unpaired_heavy_run_to_file_batch_5.tsv`. Batch 5 run with e2-highmem-16, 128 GB, 16vCPU.