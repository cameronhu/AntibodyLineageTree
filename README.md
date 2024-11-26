# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools

# fastBCR

## Running fastBCR Production (Batch) Container

For testing and building the production container, `fastbcr:prod`, first navigate to the fastBCR_Docker dir, then run the following commands.

Build the container:
```
docker build -t fastbcr:prod .
```

Test container without mounting of volume (production). Uses the input run_to_files list from GCP:
```
docker run --rm --batch_task_index=0 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv'
```

Test the container with mounting of volume:
```
docker run -it -v /home/cameronhu/lineage_tree:/lineage_tree fastbcr:prod --batch_task_index=0 --batch_size=1 --batch_input='proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv'
```

Input list file GCP path: `proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv`


Building the Docker container and pushing to artifact repository:
```
docker build -f Dockerfile . -t fastbcr:prod
docker tag fastbcr:prod us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr
docker tag fastbcr:[NEW_TAG] us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:[NEW_TAG]
docker push us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:[NEW_TAG]
```

### fastBCR Batch job submission command
Run the following command in bash:
`gcloud beta batch jobs submit job-fastbcr-test3 --location us-central1 --config batch_config.json`

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

# ClonalTree

## Docker container dev
From the ClonalTree directory:
```docker build -t clonaltree .```
```docker run --rm -it --rm -v /home/cameronhu/lineage_tree:/lineage_tree clonaltree```

## Running ClonalTree test inputs

Within the clonaltree Docker container, within the ~/ClonalTree directory, run the following command:

```python src/clonalTree.py -i /lineage_tree/clonalTree_Docker/test/input/1279050/ClonalFamily_1.fasta -o /lineage_tree/clonalTree_Docker/test/output/ClonalFamily_1.abRT.nk```
