from setuptools import setup, find_packages

setup(
    name="agentscope",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
    author="AgentScope Team",
    description="Agent debugging and observability platform",
    long_description=open("README.md").read() if __file__ else "",
    long_description_content_type="text/markdown",
    url="https://github.com/shenchengtsi/agent-scope",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)