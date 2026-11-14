"""Pytest configuration and environment harmonization for macOS OpenMP runtimes."""

import os

# Prevent OpenMP library conflict between faiss-cpu and PyTorch on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
