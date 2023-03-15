Speedy CXR
============

DICOM Viewer for viewing single DICOM files in a directory, i.e. X-rays.

Primarily for use on Mac OS X, but should work on Windows and Linux as well.

Installation
------------

Install the package using pip:

```bash
pip install git+https://github.com/selbs/speedy_cxr
```

It is recommended to install the package in a virtual environment.

Usage
-----

Run the following command in the command line:

```bash
speedy_cxr
```

Creating an Executable
----------------------

If conda environment is called 'speedy_cxr' using python 3.10, the following command can be used to create an 
executable for the application:

```bash
pyinstaller --paths=/usr/local/anaconda3/envs/speedy_cxr/lib/python3.10/site-packages 
--collect-submodules=pydicom -F --windowed --argv-emulation 
--name=speedy_cxr speedy_cxr/main.py
```