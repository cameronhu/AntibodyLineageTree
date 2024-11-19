# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools

## FastBCR Input Generation

- `list_samples()` generates 3660 runs from just the human heavy chains. There are ~4000 runs total when querying the BigQuery db.
- Running pipeline on 64 GB had insufficient memory for run: "proevo-ab/lineages/fastbcr/input/runs/SRR8365422". Increased to 124GB and testing.
- Completed SRR8365422 at 124 GB, but was close to 100 GB of total memory. SRR8365422 has 4_545_677 unique  sequences, and 6_177_127 total sequences. ~950 seconds to complete this processing.
- SRR8365433 crashed memory, has 25,705,003 total sequences, ~5 million unique sequences

## Requirements 

- Installation of R >= 4.1.0. Create a conda environment and install R through conda. 
- Within the conda environment, run the following commands:
`conda install -c conda-forge r-base r-essentials`. 
- Verify R is working with `R --version`.

Update - cannot install RStudio Desktop IDE on the GCP VM, as it requires a graphical component that doesn't exist in the VM. Run `sudo apt remove --purge rstudio` to remove attempts at the desktop installation.
- Next, download the appropriate version of R-Studio. For this Cameron's VM, the OS is Debian 12. This is the most recent R-Studio at time of writing:  
`wget https://download1.rstudio.org/electron/jammy/amd64/rstudio-2024.09.1-394-amd64.deb`
- Install with the following command:  
`sudo apt install -y ./rstudio-2024.09.1-394-amd64.deb`

