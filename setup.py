"""
TelcoCLI packaging setup.

For more details on how to operate this file, check
https://w.amazon.com/index.php/Python/Brazil
"""

import os

from setuptools import find_packages, setup

# Declare your non-python data files:
# Files underneath configuration/ will be copied into the build preserving the
# subdirectory structure if they exist.
data_files = []
for root, dirs, files in os.walk("configuration"):
    data_files.append(
        (os.path.relpath(root, "configuration"), [os.path.join(root, f) for f in files])
    )

setup(
    # include data files
    data_files=data_files,
    name="telcocli",
    version="1.0.0",
    description="AWS Telco CLI - Command line tools for AWS Telco operations",
    author="Amazon Web Services",
    license="MIT-0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.0",
        "botocore>=1.0",
        "rich>=14.0",  # For enhanced console output and logging
        "mcp>=0.1.0",  # Model Context Protocol support
    ],
    extras_require={
        "test": [
            "pytest>=8.0",
            "pytest-cov>=4.0",
            "coverage>=7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telcocli=telco_cli.cli:main",
            "telcocli-mcp=telco_cli.mcp_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
