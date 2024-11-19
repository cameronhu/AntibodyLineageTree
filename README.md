# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools

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

