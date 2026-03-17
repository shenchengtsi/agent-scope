from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentscope",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
    },
    python_requires=">=3.8",
    author="AgentScope Team",
    author_email="agentscope@example.com",
    description="Agent debugging and observability platform - SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shenchengtsi/agent-scope",
    project_urls={
        "Bug Reports": "https://github.com/shenchengtsi/agent-scope/issues",
        "Source": "https://github.com/shenchengtsi/agent-scope",
        "Documentation": "https://github.com/shenchengtsi/agent-scope/blob/main/docs/",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="agent, debugging, observability, monitoring, llm, ai",
)