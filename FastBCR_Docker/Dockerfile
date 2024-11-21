# Start with the official R base image
FROM rocker/r-base:latest

# Install necessary system dependencies for R and its packages
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libxml2-dev \
    libssl-dev \
    libgit2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libcairo2-dev \
    libpango1.0-dev \
    build-essential \
    libgsl-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    pkg-config \
    libproj-dev \
    cmake \ 
    libarchive-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# R dependency install from R script
# Copy the R script into the container
COPY install_packages.R /tmp/install_packages.R

# Run the R script
RUN Rscript /tmp/install_packages.R

# R dependency installation debugging
# RUN R --no-save --no-restore -e ".libPaths()"

# Install R dependencies step by step
# RUN R -e "install.packages('BiocManager')" && \
#     R -e "BiocManager::install(c('proj4', 'msa', 'ggtree', 'ggmsa'), ask=FALSE)" && \
#     R -e "install.packages(c('systemfonts', 'textshaping', 'ragg', 'pkgdown'))" && \
#     R -e "install.packages('devtools')"
    # R -e "devtools::install_github('ZhangLabTJU/fastBCR', ref='v1.1.3')"

# Set the working directory inside the container
WORKDIR /app

# Default command: run R
CMD ["R"]
