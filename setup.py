"""Setup script for WikiExtractor package."""

from setuptools import setup, find_packages

setup(
    name="wiki-extractor",
    version="3.0.0",
    author="WikiExtractor Contributors",
    author_email="",
    description="A Python library for extracting clean text from Wikipedia articles",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rabiloo/wiki-extractor",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
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
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
            "ruff>=0.0.241",
        ],
    },
    keywords="wikipedia, text extraction, markup processing, nlp, text mining",
    project_urls={
        "Bug Reports": "https://github.com/rabiloo/wiki-extractor/issues",
        "Source": "https://github.com/rabiloo/wiki-extractor/wiki-extractor",
        "Documentation": "https://github.com/rabiloo/wiki-extractor/wiki-extractor#readme",
    },
)
