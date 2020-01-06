FROM python:3.8

ENV PROJECT_HOME=/var/app
ENV DOWNLOAD_DIRECTORY=${PROJECT_HOME}/deployment/downloads
ENV CHECKSUM_DIR=${PROJECT_HOME}/deployment/checksums
ENV MINICONDA_VERSION=Miniconda3-4.6.14-Linux-x86_64.sh
ENV MINICONDA_URL=https://repo.continuum.io/miniconda/${MINICONDA_VERSION}
ENV MINICONDA_CHECKSUM=${CHECKSUM_DIR}/miniconda.md5sum.txt

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install tesseract-ocr libtesseract-dev build-essential \
    libgmp3-dev libgl1-mesa-glx libsm6 libxext6 poppler-utils

# Download and set up miniconda
RUN wget --directory-prefix=${DOWNLOAD_DIRECTORY} ${MINICONDA_URL} && \
    chmod u+r+x ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} && \
    ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} -b -p ${USER_HOME}/miniconda

RUN . ${USER_HOME}/miniconda/etc/profile.d/conda.sh && \
    conda activate && conda install pip pandas numpy Pillow pyyaml --yes && \
    conda install -c conda-forge opencv scikit-image --yes && \
    conda env list

# Bring in our application into the container
WORKDIR $PROJECT_HOME
ADD . $PROJECT_HOME

# Install Python packages
RUN pip install --upgrade pip && pip install pyocr pyyaml scikit-image \
    opencv-python pdf2image && \
    python setup.py install

RUN useradd -ms /bin/bash ocruser
USER ocruser

# Bring in the configuration
RUN mkdir /home/ocruser/config/ && \
    cp ch_ocr_runner_config.yml /home/ocruser/config/ch_ocr_runner_config.yml

EXPOSE 8888

CMD ["python", "./bin/ch_ocr_runner"]

