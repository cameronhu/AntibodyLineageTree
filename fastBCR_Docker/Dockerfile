# Start with the official R base image
FROM rocker/r-base:latest

WORKDIR /root

# Copy pipeline script
COPY fastBCR_batch_pipeline.py /root

# Install tools for Miniconda installation, and R dependencies
# Commented out some unsure installations
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    # apt-transport-https \
    # ca-certificates \
    # gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Conda dir and Python path
ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh 

# Install BioPython via Conda
RUN conda install -y biopython && conda clean -afy

# Install additional Python packages via pip
RUN pip install \
    argparse \
    pandas \
    numpy \
    google-cloud-storage && \
    rm -rf /root/.cache/pip

# Install R dependencies
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

# Copy local version of fastBCR package
COPY profluent-fastBCR profluent-fastBCR

# Copy the R script into the container and run it to install fastBCR
COPY install_packages.R /tmp/install_packages.R

# Run the R script
RUN Rscript /tmp/install_packages.R

# GCP Authentication
# COPY application_default_credentials.json gcs-service-account-key.json
# ENV GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json
# Mount the application_default_credentials.json when running the container

# Entrypoint: run the batch_pipeline command
ENTRYPOINT [ "python", "batch_pipeline.py" ]
