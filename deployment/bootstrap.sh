#!/usr/bin/env bash

DOWNLOAD_DIRECTORY=/vagrant/deployment/downloads
CHECKSUM_DIR=/vagrant/deployment/checksums

MINICONDA_VERSION=Miniconda3-4.6.14-Linux-x86_64.sh

MINICONDA_URL=https://repo.continuum.io/miniconda/${MINICONDA_VERSION}
MINICONDA_CHECKSUM=${CHECKSUM_DIR}/miniconda.md5sum.txt

apt-get -y update
apt-get -y upgrade

echo "Install Tesseract"
apt-get install -y tesseract-ocr
apt-get install -y libtesseract-dev

apt-get install -y python3-dev build-essential libgmp3-dev

apt-get install -y libgl1-mesa-glx
apt-get install -y libsm6 libxext6

# Download Miniconda3
if [[ ! -e ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} ]]; then
    wget --no-verbose --directory-prefix=$DOWNLOAD_DIRECTORY $MINICONDA_URL
fi

# Verify the download
if md5sum --check $MINICONDA_CHECKSUM; then
    echo "checked md5sum for miniconda"
else
    echo "bad md5sum for miniconda, exiting script"
    exit 1
fi

# Install Miniconda
if [[ ! -e /home/vagrant/resources/checksums/miniconda ]]; then
    bash ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} -b -p /home/vagrant/miniconda
fi


# Set up miniconda to run here
. /home/vagrant/miniconda/etc/profile.d/conda.sh

conda activate

# Install Python dependencies
conda install pip pandas numpy Pillow --yes

pip install pyocr

echo "Installing editable version of ch_ocr_runner"
pip install -e /vagrant/

echo "Set up .bashrc"
# Add some arguments to .bashrc
#TODO make this idempotent
if [[ ! -e extralines_added.lock ]]; then
    echo 'source /vagrant/deployment/.bashrc_extralines' >> /home/vagrant/.bashrc
    touch extralines_added.lock
else
    echo "Extra lines already added to .bashrc, skipping"
fi
