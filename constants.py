"""Shared constants for the media sorter application."""

IMAGE_FORMATS = {"jpg", "png", "jpeg", "gif", "bmp", "webp", "ico", "tiff", "tif"}
VIDEO_FORMATS = {"mp4", "avi", "mov", "mkv", "webm", "wmv", "flv", "m4v", "mpg", "mpeg"}
MEDIA_FORMATS = IMAGE_FORMATS | VIDEO_FORMATS
MAX_IMAGE_DIMENSION = 4096
