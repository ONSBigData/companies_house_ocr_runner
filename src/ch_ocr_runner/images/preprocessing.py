# -*- coding: utf-8 -*-
import PIL.Image
import cv2
import numpy as np
import skimage.filters


def preprocess_image(im: PIL.Image):
    im = _grayscale(im)
    im = _binarize(im)
    im = _denoise(im)
    return im


def _grayscale(im: PIL.Image) -> PIL.Image:
    return im.convert("L")


def _binarize(im: PIL.Image) -> np.array:
    im = np.array(im)
    thresh = skimage.filters.threshold_otsu(im)
    im = (im > thresh) * 255
    return im


def _denoise(im: np.array) -> PIL.Image:
    im = skimage.util.invert(im)

    kernel = np.ones((2, 2), np.uint8)
    im = cv2.morphologyEx(im.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

    im = skimage.util.invert(im)

    return PIL.Image.fromarray(im)
