FROM ubuntu:22.04

# Set the working directory inside the container
WORKDIR /ClinVar_Search

# Copy the current directory contents into the container at /app
COPY . /ClinVar_Search

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
# Install dependencies for Miniconda + general utilities

RUN apt-get update && apt-get install -y \
    git \
    wget\
    bzip2

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

# Add conda to PATH
ENV PATH="/opt/conda/bin:${PATH}"

# accept Tos
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r


# Create a conda environment from the YAML file
RUN conda env create -f environment.yml
RUN /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && \
 conda activate ClinVar_Search &&\
 pip install -e. &&\
 pip install -r requirements.txt && \
 chmod +x startapp.sh"
 

 ARG DEFAULT_PORT=5000
 ENV PORT=$DEFAULT_PORT

 EXPOSE $PORT


#define entry point
ENTRYPOINT ["./startapp.sh"]


