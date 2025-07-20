from setuptools import setup, find_packages
import os

setup(
    name="syft-widget",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ipywidgets>=8.0.0",
        "requests>=2.28.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="A toolkit for interactive Jupyter widgets with server/snapshot switching",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
)