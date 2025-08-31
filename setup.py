from setuptools import setup, find_packages
from pathlib import Path

# Function to read requirements from requirements.txt
def parse_requirements(filename="requirements.txt"):
    """Load requirements from a pip requirements file."""
    try:
        with open(Path(__file__).parent / filename, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print(f"Warning: '{filename}' not found. No dependencies will be installed.")
        return []

setup(
    name="augment-tools-core",
    version="2.0.4",
    author="BasicProtein", # 您可以修改为您的名字
    author_email="your.email@example.com", # 您可以修改为您的邮箱
    description="Core tools for VS Code maintenance, inspired by augment-vip.",
    long_description=Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/BasicProtein/AugmentCode-Free", # 项目的URL
    packages=find_packages(where=".", exclude=["tests*", ".venv*"]), # Finds augment_tools_core
    install_requires=parse_requirements(),
    python_requires=">=3.7", # 根据 common_utils.py 中的 f-string 和 Pathlib 用法，至少需要 3.6+，3.7+ 更安全
    entry_points={
        "console_scripts": [
            "augment-tools = augment_tools_core.cli:main_cli",
            "augment-tools-gui = main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable", # 根据开发阶段调整
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License", # 假设是 MIT，如果不是请修改
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    project_urls={ # Optional
        'Bug Reports': 'https://github.com/BasicProtein/AugmentCode-Free/issues',
        'Source': 'https://github.com/BasicProtein/AugmentCode-Free',
    },
)