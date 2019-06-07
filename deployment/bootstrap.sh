#!/usr/bin/env bash
#
# Used (by vagrant) to provision a server for OCR.
#
# NOTE: OCR won't start automatically, the ch_ocr_runner process must be started separately to this
SCRIPT_NAME=ch_ocr_server_setup

function log {
    timestamp=`date "+%Y-%m-%d %H:%M:%S"`
    echo "[$SCRIPT_NAME] ${timestamp}: $1"
}

function apt_install {
    sudo apt-get -y install $@
    if [ $? -ne 0 ]; then
        log "apt_install of $@ failed."
        exit 1
    fi
}

function pip_install {
    for p in $@; do
        pip install $p
        if [ $? -ne 0 ]; then
            log "pip install of $p failed."
            exit 1
        fi
    done
}

function miniconda_setup {
    # Download Miniconda3
    if [[ ! -e ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} ]]; then
        wget --no-verbose --directory-prefix=$DOWNLOAD_DIRECTORY $MINICONDA_URL
    fi

    # Verify the download
    if md5sum --check $MINICONDA_CHECKSUM; then
        log "checked md5sum for miniconda"
    else
        log "bad md5sum for miniconda, exiting script"
        exit 1
    fi

    # Install Miniconda
    if [[ ! -e ${USER_HOME}/miniconda ]]; then
        log "Installing miniconda"
        bash ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} -b -p ${USER_HOME}/miniconda
    fi
}

log "Setting up machine for Companies House OCR Runner"

log "Setting environment dependent arguments"
if [ ${USER} == "vagrant" ] || [ ${SUDO_USER} == "vagrant" ]; then
    log "Running script in VM setup by Vagrant"
    PROJECT_HOME=/vagrant
    USER_HOME=/home/vagrant
else
    log "Running non-vagrant setup"
    PROJECT_HOME=$HOME/companies_house_ocr_runner
    USER_HOME=$HOME
fi

log "Setting common arguments"
DOWNLOAD_DIRECTORY=${PROJECT_HOME}/deployment/downloads
CHECKSUM_DIR=${PROJECT_HOME}/deployment/checksums

MINICONDA_VERSION=Miniconda3-4.6.14-Linux-x86_64.sh
MINICONDA_URL=https://repo.continuum.io/miniconda/${MINICONDA_VERSION}
MINICONDA_CHECKSUM=${CHECKSUM_DIR}/miniconda.md5sum.txt

log "PROJECT_HOME=$PROJECT_HOME"
log "DOWNLOAD_DIRECTORY=$DOWNLOAD_DIRECTORY"
log "CHECKSUM_DIR=$CHECKSUM_DIR"

sudo apt-get -y update
sudo apt-get -y upgrade
sudo pip install --upgrade pip

log "Install Tesseract"
apt_install tesseract-ocr libtesseract-dev

log "Install Python"
echo apt_install python3-dev build-essential libgmp3-dev

apt_install libgl1-mesa-glx
apt_install libsm6 libxext6

log "Install poppler"
apt_install poppler-utils

log "Setup Miniconda"
miniconda_setup

bash ${DOWNLOAD_DIRECTORY}/${MINICONDA_VERSION} -b -p ${USER_HOME}/miniconda

# Set up miniconda to run here
log "Activating conda env"
. ${USER_HOME}/miniconda/etc/profile.d/conda.sh

conda activate

conda install pip pandas numpy Pillow pyyaml --yes
conda install -c conda-forge opencv scikit-image --yes

conda env list

pip_install pyocr
pip_install pdf2image

if [ $USER == "vagrant" ] || [ $SUDO_USER == "vagrant" ]; then
    log "Installing editable version of ch_ocr_runner"
    pip install -e $PROJECT_HOME
        
        
    log "Set up .bashrc"
    # Add some arguments to .bashrc
    #TODO make this idempotent
    if [[ ! -e extralines_added.lock ]]; then
        echo 'source /vagrant/deployment/.bashrc_extralines' >> /home/vagrant/.bashrc
        touch extralines_added.lock
    else
        echo "Extra lines already added to .bashrc, skipping"
    fi

    mkdir /home/vagrant/config
    cp /vagrant/deployment/ch_ocr_runner_config.yml /home/vagrant/config/
else
    log "Installing ch_ocr_runner"
    pip install ${PROJECT_HOME}
fi
