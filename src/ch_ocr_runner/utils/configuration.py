# -*- coding: utf-8 -*-
"""
Provides configuration for the project.
Defaults are defined in the `Config` class definition.
They are overridden by values in ~/config/presscuts_config.yml.
Warning:
    Modifying config values is not prevented.
    Config is implemented as a singleton, so any modification will
    be visible anywhere else the configuration is used.
Usage:
    ``
    config = configuration.get_config()
    config.CONFIG_NAME
    ``
@author: Philip Lee
"""
import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

CONFIG_FILEPATH = str(
    Path.home().joinpath("config").joinpath("ch_ocr_runner_config.yml")
)


class Singleton(type):
    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):

        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance
        else:
            return cls.__instance


class ConfigProvider(metaclass=ABCMeta):

    source_name = "Unnamed Source"

    @abstractmethod
    def fetch_config(self):
        raise NotImplementedError("ConfigProviders must implement fetch_config")


class YamlConfigProvider(ConfigProvider):
    def __init__(self, filepath):
        self.filepath = filepath
        self.source_name = f"Yaml file: {filepath}"

    def fetch_config(self):

        if os.path.isfile(self.filepath):

            logger.info(f"Reading config from {self.filepath}")
            print("Reading config from", self.filepath)
            with open(self.filepath, "rb") as f:
                yaml_conf = yaml.load(f, Loader=yaml.FullLoader)

            return yaml_conf.items()

        else:
            logger.info(f"Config file: {self.filepath} does not exist.")
            return list()


# Private method from enum
def _is_dunder(name):
    """Returns True if a __dunder__ name, False otherwise."""
    return (
        name[:2] == name[-2:] == "__"
        and name[2:3] != "_"
        and name[-3:-2] != "_"
        and len(name) > 4
    )


# Private method from enum
def _is_sunder(name):
    """Returns True if a _sunder_ name, False otherwise."""
    return (
        name[0] == name[-1] == "_"
        and name[1:2] != "_"
        and name[-2:-1] != "_"
        and len(name) > 2
    )


def _is_under(name):
    return _is_sunder(name) or _is_dunder(name)


class Config(metaclass=Singleton):
    """Defines the configuration names and defaults for the project."""

    config_provider = YamlConfigProvider(filepath=CONFIG_FILEPATH)

    def __init__(self):

        self.LOG_LEVEL = logging.DEBUG

        self.DATA_DIR = os.path.join(os.path.expanduser("~"), "data", "companies_house")
        self.PDF_DIR = os.path.join(self.DATA_DIR, "pdfs")
        self.WORKING_DIR = os.path.join(self.DATA_DIR, "working")

        self.WORK_BATCH_ALLOCATION_FILEPATH = os.path.join(
            self.DATA_DIR, "pdf_batch_allocation.csv"
        )

        self.MACHINE_ENV_VAR = "CH_OCR_MACHINE_ID"

        self.OCR_DPI = 300
        self.IMAGE_FORMAT = "tiff"
        self.IMAGE_SUFFIX = ".tif"

        self.PREPROCESS_REPORT_FREQUENCY = 50

        for key, value in Config.config_provider.fetch_config():

            if key in self.__dict__ and not _is_under(key):
                logger.info(
                    f"Overriding default value of {key} with value from {Config.config_provider.source_name}"
                )
                self.__dict__[key] = value

    def log_config(self):
        logger.info(f"LOG_LEVEL: {self.LOG_LEVEL}")
        logger.info(f"DATA_DIR: {self.DATA_DIR}")
        logger.info(f"PDF_DIR: {self.PDF_DIR}")
        logger.info(f"WORKING_DIR: {self.WORKING_DIR}")
        logger.info(
            f"WORK_BATCH_ALLOCATION_FILEPATH: {self.WORK_BATCH_ALLOCATION_FILEPATH}"
        )
        logger.info(f"MACHINE_ENV_VAR: {self.MACHINE_ENV_VAR}")
        logger.info(f"OCR_DPI: {self.OCR_DPI}")
        logger.info(f"IMAGE_FORMAT: {self.IMAGE_FORMAT}")
        logger.info(f"IMAGE_SUFFIX: {self.IMAGE_SUFFIX}")
        logger.info(f"PREPROCESS_REPORT_FREQUENCY: {self.PREPROCESS_REPORT_FREQUENCY}")


def get_config():
    return Config()


if __name__ == "__main__":

    log_format = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s"
    logging.basicConfig(format=log_format)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logger.info("Logging out config")

    config = get_config()
    config.log_config()
