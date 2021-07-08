FROM python:3.8

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install tesseract-ocr libtesseract-dev build-essential \
    libgmp3-dev libgl1-mesa-glx libsm6 libxext6 poppler-utils

# Bring in our application into the container
ENV PROJECT_HOME=/var/app
WORKDIR $PROJECT_HOME
ADD . $PROJECT_HOME

# Install Python packages
RUN pip install --upgrade pip && pip install pyocr pyyaml scikit-image \
    pandas numpy Pillow opencv-python pdf2image && \
    python setup.py install

RUN useradd -ms /bin/bash ocruser
USER ocruser

# Bring in the configuration
RUN mkdir /home/ocruser/config/ && \
    cp ch_ocr_runner_config.yml /home/ocruser/config/ch_ocr_runner_config.yml

CMD ["python", "./bin/ch_ocr_runner"]
