# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools.

## Running Pipelines
Run the following code to run the batch jobs from scratch

### Clone Git Repo
```
git clone https://github.com/Profluent-AI/lineage_tree.git
cd lineage_tree
```

### FastBCR
```
python generate_gcp_input_list.py
gcloud beta batch jobs submit job-fastbcr-[X] --location us-central1 --config fastBCR_Docker/fastBCR_batch_config.json
```

### ClonalTree
```
./clonalTree_Docker/generate_clonalTree_batch_input.sh
gcloud beta batch jobs submit job-ClonalTree-[X] --location us-central1 --config clonalTree_Docker/clonalTree_batch_config.json
```

## Docker Images

Production docker images for fastBCR and ClonalTree are located in the GCP artifcat registry as follows:
- us-central1-docker.pkg.dev/profluent-evo/ab-lineages/fastbcr:prod_timing
- us-central1-docker.pkg.dev/profluent-evo/ab-lineages/clonaltree:prod

## Full Pipeline Overview

1. Batch input generation for fastBCR. The fastBCR batch input is the `human_unpaired_heavy_run_to_files.tsv` file mapping run_id to a list of file_paths.
   1. Running `python generate_gcp_input_list.py` will generate the fastBCR batch input and store it at `gs://proevo-ab/lineages/fastbcr/batch/run_to_files.tsv`
2. Run the GCP batch job for fastBCR
   1. `gcloud beta batch jobs submit job-fastbcr-batch-[X] --location us-central1 --config fastBCR_Docker/fastBCR_batch_config.json`
3. Batch input generation for ClonalTree. The ClonalTree input is a list of all .fasta files generated from the fastBCR pipeline.
   1. Run `./clonalTree_Docker/generate_clonalTree_batch_input.sh`. ClonalTree batch_input will be stored at `gs://proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt`
4. Run the GCP batch job for ClonalTree
   1. `gcloud beta batch jobs submit job-clonaltree-batch-[X] --location us-central1 --config clonalTree_Docker/clonalTree_batch_config.json`

## Pipeline Inputs and Outputs

All input and output files, including batch_inputs and pipeline outputs, are stored in GCS, within the `profluent-evo` bioinformatics project. Specifically, all lineage tree data is stored within the `proevo-ab/lineages` directory.

### FastBCR 

FastBCR pipeline takes in an input generated from the raw OAS directories, and outputs three different directories on GCS: runs, run_clonotypes, run_stats.

#### FastBCR Input
- Batch Input: `proevo-ab/lineages/fastbcr/batch`
- For this initial run, batch inputs are generated from the raw OAS data files stored in `proevo-ab/oas/unpaired/unpaired_human/unpaired_human_heavy`
- Different raw OAS file directories can be generated as batch_input files by modifying the input_dir path in `generate_gcp_input_list.py`
- Example: `gs://proevo-ab/lineages/fastbcr/batch/human_unpaired_heavy_run_to_files.tsv`

![fastBCR_batch_input](analysis/fastBCR_batch_input.png)
   - `run_id` - the run_ID of all the files, in correspondence with the OAS raw data
   - `file_paths` - list of GCS file paths to raw OAS data associated with the run
#### FastBCR Output
All fastBCR pipeline outputs are stored in the `proevo-ab/lineages/fastbcr/output` directory.

##### runs
- The `runs/` directory contains the .fasta file outputs of fastBCR, which correspond to inferred clonal families. The FASTA files are organized into their run directories. These FASTA files are used as the input to ClonalTree
- Example file: `gs://proevo-ab/lineages/fastbcr/output/runs/1279050/ClonalFamily_1.fasta`
![clonal_family_fasta](analysis/clonal_family_fasta.png)
   - Clonotype ID followed by @ abundancy

##### run_stats
- `run_stats` contains clonal family statistics, organized by each run.
- Example file: `gs://proevo-ab/lineages/fastbcr/output/run_stats/1279050_run_statistics.csv`
![run_statistics](analysis/run_statistics.png)
  - Contains average number of clonal families, average size of clonal families, percentage of raw sequences actually mapped to clonal families, and some timing statistics

##### run_clonotypes
- `run_clonotypes` is the mapping of the inferred clonotypes from fastBCR back to their original OAS data files.
- Example file: `gs://proevo-ab/lineages/fastbcr/output/run_clonotypes/1279050/Clonotypes_ClonalFamily_1.csv`
![run_clonotypes](analysis/clonotype_csv.png)
  - `clonotype_index` is the fastBCR generated clonotype index. Clonotypes may be linked to multiple raw sequence indices from the OAS data file
  - `clonotype_count` is the number of raw OAS sequences associated with this clonotype
  - `clone_count` is the total abundancy of this clonotype
  - `clone_fre` is the frequency of this clonotype as a percentage of all sequences in the raw OAS dataframe
  - `orign_index` is the raw OAS dataframe index for the representative sequence that is used for the clonotype. Should be contained within the `index_match` list
  - `index_match` is the raw sequence indices are stored in the  column. `index_match` is an R list of all the dataframe indices that match up to this clonotype
  
### ClonalTree
All ClonalTree related files are stored in the `proevo-ab/lineages/clonalTree` GCS directory. ClonalTree outputs two files, a .nk file in ree structure, and a .nk.csv file with the same information in more human-interpretable fomrat.

#### ClonalTree Input
- Batch input for the ClonalTree pipeline is generated from the FASTA files generated by fastBCR.
- These Batch inputs are stored at `proevo-ab/lineages/clonalTree/batch`
- Example: `gs://proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt`
![clonalTree_batch_input](analysis/clonalTree_batch_input.png)
   - List of FASTA files generated by fastBCR, each representing a clonal family. 

#### ClonalTree Outputs
ClonalTree outputs both standard .nk files and .nk.csv files that are more human interpretable.
- Lineage trees are stored in the `proevo-ab/lineages/clonalTree/output/runs` directory, organized by run.

##### Newick Format

- Example: `gs://proevo-ab/lineages/clonalTree/output/runs/1279050/1279050_ClonalFamily_1.abRT.nk`
![nk](analysis/newick.png)
   - Clonal tree in Newick format

##### Newick CSV Format
- Example: `gs://proevo-ab/lineages/clonalTree/output/runs/1279050/1279050_ClonalFamily_1.abRT.nk.csv`
![nk_csv](analysis/nk_csv.png)
   - First column: parent clonotype_id
   - Second column: child clonotype_id
   - Third column: distance (nt) from parent to child

##### Representative Tree Graph
![clonal_tree](analysis/ERR1812282_ClonalFamily_12.abRT.nk.png)

## Analysis 
- Analysis is within the `analysis/` directory. fastBCR and ClonalTree stats are organized in their own notebooks.