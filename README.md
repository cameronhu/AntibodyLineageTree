# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools.

## 

## Docker Images

Production docker images for fastBCR and ClonalTree are located in the GCP artifcat registry as follows:
- us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod_timing
- us-central1-docker.pkg.dev/profluent-evo/ab-lineages/clonaltree:prod

## Full Pipeline Overview

1. Batch input generation for fastBCR. The fastBCR batch input is the `human_unpaired_heavy_run_to_files.tsv` file mapping run_id to a list of file_paths.
   1. Running `python generate_gcp_input_list.py` will generate the fastBCR batch input and store it at `gs://proevo-ab/lineages/fastbcr/batch/run_to_files.tsv`
2. Run the GCP batch job for fastBCR
   1. `gcloud beta batch jobs submit job-fastbcr-test[X] --location us-central1 --config fastBCR_Docker/fastBCR_batch_config.json`
3. Batch input generation for ClonalTree. The ClonalTree input is a list of all .fasta files generated from the fastBCR pipeline.
   1. Run `./clonalTree_Docker/generate_clonalTree_batch_input.sh`. ClonalTree batch_input will be stored at `gs://proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt`
4. Run the GCP batch job for ClonalTree