"""Setup script for AgentScope SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentscope-monitor",
    version="0.5.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AgentScope - Distributed tracing and monitoring for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentscope",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.25.0",
        "loguru>=0.6.0",
    ],
    extras_require={
        "nanobot": ["nanobot-ai>=0.1.0"],
        "dev": ["pytest", "black", "flake8", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "agentscope=agentscope.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
