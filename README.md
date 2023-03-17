Speedy QC for Desktop
=====================

DICOM viewer and labeller for single DICOM files in a directory, i.e. X-rays.

Primarily for use on Mac OS X, but should work on Windows and Linux as well.

Installation
------------

Install the package using pip:

```bash
pip install git+https://github.com/selbs/speedy_qc
```

It is recommended to install the package in a virtual environment.

Usage
-----

Run the following command in the command line:

```bash
speedy_qc
```

Customisation
-------------

List the required checkboxes in the checkboxes.yml file and the checkboxes will be automatically updated.

Creating an Executable
----------------------

If conda environment is called 'speedy_qc' using python 3.10, the following command can be used to create an 
executable for the application:

```bash
pyinstaller --paths=/usr/local/anaconda3/envs/speedy_qc/lib/python3.10/site-packages 
--collect-submodules=pydicom -F --windowed --argv-emulation 
--name=speedy_qc speedy_qc/main.py
```

Keyboard Shortcuts
------------------

| Key            | Action             |
|----------------|--------------------|
| B              | Previous image     |
| N              | Next image         |
| + / =          | Zoom in            |
| - / _          | Zoom out           |
| I              | Invert grayscale   |
| R              | Rotate image right |
| L              | Rotate image left  |
| S              | Save to CSV        |
| Ctrl + Q       | Quit               |
| Ctrl + Scroll  | Window Width       |
| Shift + Scroll | Window Center      |
