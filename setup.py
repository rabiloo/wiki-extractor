"""Setup script for WikiExtractor package."""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version from __init__.py
def get_version():
    with open("__init__.py", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.0.0"

setup(
    name="wiki-extractor",
    version=get_version(),
    author="WikiExtractor Contributors",
    author_email="",
    description="A Python library for extracting clean text from Wikipedia articles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Phongng26/wiki-extractor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Markup",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "wiki-extractor=main:main",
        ],
    },
    keywords="wikipedia, text extraction, markup processing, nlp, text mining",
    project_urls={
        "Bug Reports": "https://github.com/Phongng26/wiki-extractor/issues",
        "Source": "https://github.com/Phongng26/wiki-extractor",
        "Documentation": "https://github.com/Phongng26/wiki-extractor#readme",
    },
)
