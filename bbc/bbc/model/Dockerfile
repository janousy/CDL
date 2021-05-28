# Determined Image
FROM determinedai/environments:cuda-10.2-pytorch-1.7-tf-1.15-gpu-0.13.0

# Custom Configuration
RUN apt-get update && \
   DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
   apt-get install -y unzip python-opencv graphviz
COPY bbc/model/src/requirements.txt /tmp/pip_requirements.txt
RUN conda create --name env
RUN conda clean --all --force-pkgs-dirs --yes
RUN eval "$(conda shell.bash hook)" && \
   conda activate env && \
   pip install --requirement /tmp/pip_requirements.txt