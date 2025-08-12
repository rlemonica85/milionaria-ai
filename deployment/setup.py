#!/usr/bin/env python3
"""
Setup script para Milionária AI

Instalação:
    pip install -e .
    
Ou para instalação completa:
    python setup.py install
"""

from setuptools import setup, find_packages
from pathlib import Path

# Ler o README para descrição longa
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Ler requirements.txt
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            requirements.append(line)

setup(
    name="milionaria-ai",
    version="1.0.0",
    author="Rodrigo",
    author_email="rodrigo@example.com",
    description="Sistema inteligente de análise e predição para +Milionária",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rodrigo/milionaria-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "gpu": [
            "cuml>=23.10.0",
            "cupy-cuda11x>=12.0.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "milionaria=src.cli.app:main",
            "milionaria-update=milionaria:main",
            "milionaria-streamlit=app_streamlit:main",
        ],
    },
    include_package_data=True,
    package_data={
        "milionaria-ai": [
            "configs/*.yaml",
            "configs/*.yml",
            "tasks/*.ps1",
            "tasks/*.py",
        ],
    },
    zip_safe=False,
)