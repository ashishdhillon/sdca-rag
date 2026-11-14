"""SDCA Research Project Source Package."""

import os

# Prevent OpenMP runtime conflict between faiss-cpu and torch on macOS
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
