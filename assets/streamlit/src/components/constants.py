"""
Copyright © Amazon.com and Affiliates
This code is being licensed under the terms of the Amazon Software License available at https://aws.amazon.com/asl/
----------------------------------------------------------------------
File content:
    Streamlit constants
"""

MAX_ATTRIBUTES = 50
MAX_DOCS = 50
MAX_FEW_SHOTS = 50

MAX_CHARS_DOC = 500_000
MAX_CHARS_NAME = 100
MAX_CHARS_DESCRIPTION = 100_000
MAX_CHARS_FEW_SHOTS_INPUT = 100_000
MAX_CHARS_FEW_SHOTS_OUTPUT = 100_000

DEFAULT_ATTRIBUTES = 1
DEFAULT_DOCS = 1
DEFAULT_FEW_SHOTS = 1

GENERATED_QRCODES_PATH = "tmp/"

SUPPORTED_EXTENSIONS = [
    "txt",
    "pdf",
    "png",
    "jpg",
    "tiff",
    "docx",
    "doc",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
    "html",
    "htm",
    "md",
    "mp3",
    "wav",
]

SUPPORTED_EXTENSIONS_BEDROCK = [
    "pdf",
    "png",
    "jpg",
]
