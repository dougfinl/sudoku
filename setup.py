import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sudokustepper",
    version="0.2.2",
    author="Douglas Finlay",
    author_email="douglas@douglasfinlay.com",
    description="A tool for stepping through, and visualising Sudoku solving algorithms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dougfinl/sudokustepper",
    packages=["sudokustepper"],
    python_requires=">=3",
    install_requires=["PyQt5"],
    entry_points={
        "gui_scripts": [
            "sudokustepper = sudokustepper.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Programming Language :: Python :: 3",
    ],
)
