# Use the official Conda image as a base
FROM continuumio/miniconda3:latest

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set the working directory to root
WORKDIR /root

# Install necessary dependencies
RUN conda update -n base -c defaults conda && \
    conda create -n bioenv python numpy biopython -y && \
    conda clean -a -y

# Activate the conda environment
# RUN echo "conda activate bioenv" >> ~/.bashrc

# Activate the conda environment and install additional packages with pip
RUN source activate bioenv && \
    pip install \ 
    ete3 \
    networkx \
    scipy \ 
    six && \
    rm -rf /root/.cache/pip

# Clone the ClonalTree repository from GitHub
RUN git clone https://github.com/julibinho/ClonalTree.git /root/ClonalTree

# Set the working directory to the cloned ClonalTree repo
WORKDIR /root/ClonalTree

# Activate bioenv conda environment on startup
RUN echo "conda activate bioenv" >> ~/.bashrc

# Default command to start an interactive shell
CMD ["/bin/bash"]
