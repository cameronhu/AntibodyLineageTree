# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools

# fastBCR

## Running fastBCR Production (Batch) Container

For testing the production container, `fastbcr:prod`

```
docker run -it -v /home/cameronhu/lineage_tree:/lineage_tree fastbcr:prod --batch_task_index=0 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv'
```

Input list file GCP path: `proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv`


#### In testing 
```
gcloud auth login
docker run -it -e GOOGLE_APPLICATION_CREDENTIALS=/root/application_default_credentials.json -v /home/cameronhu/lineage_tree:/lineage_tree -v /home/cameronhu/.config/gcloud/application_default_credentials.json:/root/application_default_credentials.json fastbcr bash
```

Building the Docker container and pushing to artifact repository:
```
docker build -f Dockerfile . -t fastbcr:prod
docker tag fastbcr:prod us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:latest
docker push us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:latest

```

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

### fastBCR Batch job submission command
Preliminary code from Stephen for the "prodigal-batch" job:

```
gcloud beta batch jobs submit prodigal-batch --location us-central1 --config batch_config.json
```

## FastBCR Input Generation Notes

- `list_samples()` generates 3660 runs from just the human heavy chains. There are ~4000 runs total when querying the BigQuery db.
- Running pipeline on 64 GB had insufficient memory for run: "proevo-ab/lineages/fastbcr/input/runs/SRR8365422". Increased to 124GB and testing.
- Completed SRR8365422 at 124 GB, but was close to 100 GB of total memory. SRR8365422 has 4_545_677 unique  sequences, and 6_177_127 total sequences. ~950 seconds to complete this processing.
- SRR8365433 crashed memory, has 25,705,003 total sequences, ~5 million unique sequences
- Updated to 250 GB memory, was able to run SRR8283795 with 7.6 million unique sequences

# ClonalTree

## Docker container dev
From the ClonalTree directory:
```docker build -t clonaltree .```
```docker run --rm -it --rm -v /home/cameronhu/lineage_tree:/lineage_tree clonaltree```

## Running ClonalTree test inputs

Within the clonaltree Docker container, within the ~/ClonalTree directory, run the following command:

```python src/clonalTree.py -i /lineage_tree/clonalTree_Docker/test/input/1279050/ClonalFamily_1.fasta -o /lineage_tree/clonalTree_Docker/test/output/ClonalFamily_1.abRT.nk```
