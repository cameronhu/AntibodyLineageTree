# Start with the official R base image
FROM r-base:latest

# Set environment variables for R
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary system dependencies for R packages
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libxml2-dev \
    libssl-dev \
    libgit2-dev \
    build-essential \
    libgsl-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install FastBCR and its R dependencies
RUN R -e "install.packages('BiocManager')" && \
    R -e "BiocManager::install(c('proj4', 'msa', 'ggtree', 'ggmsa'))" && \
    R -e "install.packages('devtools')" && \
    R -e "devtools::install_github('ZhangLabTJU/fastBCR', ref = 'v1.1.3')"

# RUN R -e "install.packages(c('remotes', 'devtools'), repos='https://cloud.r-project.org/')" \
#     && R -e "remotes::install_github('arcadia-fast/fastbcr')" \
#     && R -e "library(FastBCR)"

# Set the working directory inside the container
WORKDIR /app

# Copy any scripts or data files into the container (optional)
# COPY . /app

# Set the default command to run R
CMD ["R"]
