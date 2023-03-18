Speedy QC for Desktop
=====================

DICOM viewer and labeller for single DICOM files in a directory, i.e. X-rays.

Primarily for use on Mac OS X, but should work on Linux and Windows.

Installation
------------

Install the package using pip:

```bash
pip install git+https://github.com/selbs/speedy_qc
```

It is recommended to install the package in a virtual environment with Python 3.10, used in development.
However, other versions of Python 3 should still work.

You can also clone the package from GitHub and install it manually:

```bash
git clone https://github.com/selbs/speedy_qc.git
cd speedy_qc
pip install .
```

Usage
-----

Run the following command in the command line:

```bash
speedy_qc
```

Customisation
-------------

List the required checkboxes in the checkboxes.yml file and the checkboxes will be automatically updated. 
The maximum number of backups and the backup directory can also be changed.

Creating an Executable
----------------------

An executable can be created using py2app for Mac OS X or py2exe for Windows. PyInstaller may also work but
has not been tested.

To create an executable with py2app, the following command can be used from inside the speedy_qc directory:

```bash
python setup.py py2app
```

The finished executable will be in the `dist` folder, which can be moved to the `Applications` folder as required.


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

Backup Files
------------

Work is automatically backed up in the user's home directory (`~`) in the folder `.speedy_qc_backups`.
This is a hidden folder and will hold up to the latest ten backups. A backup will be made every ten minutes to
allow for recovery in case of a crash. The number of backups and the backup directory can be customised
in the `config.yml` file.
