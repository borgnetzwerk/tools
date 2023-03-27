# Work in Progress
import json
import wordcloud
from wordcloud import WordCloud, ImageColorGenerator
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import cv2


def generate_wordcloud(dict_word_count, output_file_path='wordcloud.png', width=1920, height=1080):
    """
    Generates a wordcloud as a PNG image from a dictionary containing word count information.

    Args:
        dict_word_count: A dictionary containing word count information.
        output_file_path: The path and file name to save the generated image. Default is 'wordcloud.png'.
        width: The width of the generated image. Default is 1920.
        height: The height of the generated image. Default is 1080.

    Returns:
        None.
    """

    if not output_file_path.endswith(".png"):
        output_file_path += ".png"
    wc = WordCloud(width=width, height=height)
    wc.generate_from_frequencies(dict_word_count)
    wc.to_file(output_file_path)


def generate_wordcloud_mask(dict_word_count, mask_path, output_file_path='wordcloud_mask.png', width=1920, height=1080):
    """
    Generates a wordcloud as a PNG image from a dictionary containing word count information and a mask image.

    Args:
        dict_word_count: A dictionary containing word count information.
        mask_path: The path of the mask image to be used.
        output_file_path: The path and file name to save the generated image. Default is 'wordcloud_mask.png'.
        width: The width of the generated image. Default is 1920.
        height: The height of the generated image. Default is 1080.

    Returns:
        None.
    """
    if not output_file_path.endswith(".png"):
        output_file_path += ".png"
    mask = np.array(Image.open(mask_path))
    if len(mask.shape) == 2:
        mask = np.stack((mask,) * 3, axis=-1)  # convert grayscale to RGB


    # Calculate the aspect ratio of the mask
    mask_width, mask_height = mask.shape[1], mask.shape[0]
    mask_aspect_ratio = mask_width / mask_height

    # Adjust the width and height parameters to maintain the aspect ratio of the mask
    if width / height > mask_aspect_ratio:
        # The wordcloud will be constrained by height
        width = int(height * mask_aspect_ratio)
    else:
        # The wordcloud will be constrained by width
        height = int(width / mask_aspect_ratio)


    # Resize the mask image if it is smaller than the desired width and height
    mask_height, mask_width, _ = mask.shape
    if mask_width < width or mask_height < height:
        mask = cv2.resize(mask, (width, height))

    wc = WordCloud(mask=mask, width=width, height=height)
    wc.generate_from_frequencies(dict_word_count)
    # image_colors = ImageColorGenerator(mask)
    # wc.recolor(color_func=random_color)
    wc.to_file(output_file_path)


def generate_mask(image_path, mask_file_path=None):
    """
    Generates a mask image from an input image.

    Args:
        image_path: The path of the input image.
        mask_file_path: The path and file name to save the generated mask image. Default is 'mask.png'.

    Returns:
        The file path of the generated mask image.
    """
    if mask_file_path is None:
        mask_file_path = os.path.join(os.path.dirname(image_path), "mask.png")

    # Read the input image and convert it to grayscale
    image = np.array(Image.open(image_path).convert('L'))

    # Loop through different thresholds until the mask has at least 25% black pixels
    for threshold in range(256):
        # Threshold the image using the current threshold value
        binary = (image > threshold).astype(np.uint8) * 255

        # Calculate the percentage of black pixels in the binary image
        black_pixels_percent = np.count_nonzero(binary == 0) / binary.size

        # If the percentage of black pixels is at least 25%, save the binary image as the mask and return the file path
        if black_pixels_percent >= 0.25:
            Image.fromarray(binary).save(mask_file_path)
            return mask_file_path

    # If no threshold results in a mask with at least 25% black pixels, raise an error
    raise ValueError(
        "Could not generate a mask with at least 25% black pixels")
