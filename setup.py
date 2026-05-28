from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="AgentI-py",
    version="1.0.0",
    author="AgentI Contributors",
    description="LINE Agent I (WebView and Native) Python Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/AgentI-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "sseclient-py>=1.9.0",
        "python-dotenv>=1.0.0",
    ],
)
