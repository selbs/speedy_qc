Speedy QC for Desktop <img src="https://github.com/selbs/speedy_qc/blob/master/speedy_qc/assets/1x/grey.png" alt="App Logo" width="100" style="margin-right: 16px;">
=====================


![Screenshot](https://github.com/selbs/speedy_qc/blob/master/speedy_qc/assets/screenshot.png)

Speedy QC is a DICOM viewer and labeller for single DICOM files in a directory, i.e. X-rays. The program may be
used to quickly check the quality of the images and to label them with the required ground truth for
training a deep learning model.

The program may be run from the command line or as an executable, explained below.

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

Customisation
-------------

List the required checkboxes in the `config.yml` file and the checkboxes will be automatically updated. 
The maximum number of backups and the backup directory can also be changed.

If you're using an executable, the config.yml file can still be edited in 
`Speedy QC.app/Contents/Resources/config.yml`, which can be edited in the terminal or if using Mac OS X,
you can right-click on the executable and select `Show Package Contents`, then navigate to the `Resources` folder.


Creating an Executable
----------------------

An executable can be created using `py2app` for Mac OS X or `py2exe` for Windows. The customised `setup_py2app_****.py`
scripts have been included for `py2app` for both 86x64 and arm64 architectures on OS X. These may work out of the box
but may need some tweaking for your local environment. For example, if you are using a different version of Python
(3.10) used in development or if the libffi library is in a different directory (see below).

To create an executable with `py2app` on 86x64, the following command can be used from inside the `speedy_qc` directory:

```bash
python setup_86x64.py py2app
```

For arm64, the following command can be used:

```bash
python setup_arm64.py py2app
```

The finished executable will be in the `dist` folder, which can be moved to the `Applications` folder as required.

If experiencing issues with `py2app` on Mac OS X, you can run the program the terminal to see more information:

```bash
'dist_86x64/Speedy QC.app/Contents/MacOS/Speedy QC'
```

or alternatively compile the program in alias mode:

```bash
python setup_86x64.py py2app -A
```
In both cases, replace '86x64' with 'arm64' for the arm64 executable as necessary.

`PyInstaller` may also work to create an executable but has not been tested.

### Creating a Universal Binary

A universal binary can be created by combining the two executables created by `py2app`. This can be done using the
`lipo` command after both executables have been created (e.g. inside arm64 and 86x64 conda environments). 
To create a universal binary for the 86x64 and arm64 executables, use the following commands:

```bash
mkdir -p "dist/universal/Speedy QC.app/"
cp -R "dist/arm64/Speedy QC.app/" "dist/universal/Speedy QC.app/"
lipo -create -output "dist/universal/Speedy QC.app/Contents/MacOS/Python" "dist/arm64/Speedy QC.app/Contents/MacOS/Python" "dist/86x64/Speedy QC.app/Contents/MacOS/Python"
```

### libffi

The libffi library is required for the executable to run on MacOS. This can be installed using Homebrew:

```bash
brew install libffi
```

If using a arm64 Mac, the libffi library will be installed in the `/opt/homebrew/Cellar` directory, whilst the 86x64
version will be installed in the `/usr/local/opt` directory. The `setup_86x64.py` and `setup_arm64.py` scripts
have been configured to look for the library in the `/opt/homebrew` directory. If the library is installed in a
different directory, the `setup_86x64.py` and `setup_arm64.py` scripts will need to be modified accordingly.
