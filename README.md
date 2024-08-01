Speedy QC <img src="speedy_qc/assets/1x/grey.png" alt="App Logo" width="75" style="float: right;">
=====================

Speedy QC is a customisable annotation tool for medical images. Originally developed for 
image quality control (QC) of machine learning datasets, the application may be
used to quickly check the quality of the images and/or to label them with ground truth. The viewer
supports DICOM, PNG, JPEG and other common image formats. Bounding boxes may be added to demarcate the findings.

The program may be run from the command line or as an executable, which can be downloaded or 
created from the source code (instructions below).

Primarily developed for use on Mac OS X, but also compatible with Linux and Windows.

![Screenshot](speedy_qc/assets/screenshot.png)

> **Warning:** Please note that this application is still in development and there may be unresolved bugs and issues. 
> Use at your own risk!
> 
## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
  - [Inputs and Outputs](#inputs-and-outputs)
    - [Checkboxes](#checkboxes)
    - [Bounding Boxes](#bounding-boxes)
    - [Radiobuttons](#radiobuttons)
  - [Progress](#progress)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
- [Customisation](#customisation)
  - [Configuration Wizard](#configuration-wizard)
  - [YAML File](#yaml-file)
- [Backup Files](#backup-files)
- [Executable Application](#executable-application)

Installation
------------

Install the package using pip:

```bash
pip install git+https://github.com/selbs/speedy_qc
```

It is recommended to install the package in a Python 3.10 virtual environment as it was this
version of python used in development. However, other versions of Python 3 should still work.

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

Alternatively, the app may be run from an executable (see below).

### Inputs and Outputs

#### Checkboxes

Checkboxes are stored as integers:  

| Checkbox Value  |   Meaning   |
|:---------------:|:-----------:|
|        0        | False / No  |
|        1        |  Uncertain  |
|        2        | True / Yes  |

#### Bounding Boxes

- Added to the image by clicking and dragging the mouse.
- Multiple boxes may be added to each image and for each finding.
- The box is labelled with the name of the last checked checkbox.
- Moved by clicking and dragging the box. 
- Deleted by right-clicking on the box and selecting `Remove` from the menu.

#### Radiobuttons

Radiobuttons are stored as integers with the meaning of the integer corresponding to the order of the radiobuttons
inputted in the configuration wizard. For example, if the radiobuttons are `['Normal', 'Abnormal']`, then the values
will be `0` for `Normal` and `1` for `Abnormal`.

### Progress

Your progress through the folder of images is shown in the progress bar at the bottom of the window.

### Keyboard Shortcuts

|                                                                Key                                                                 |       Action        |
|:----------------------------------------------------------------------------------------------------------------------------------:|:-------------------:|
|                             <kbd>←</kbd>, <kbd>B</kbd>, <kbd>Back</kbd>, <kbd>⌫</kbd>, <kbd>DEL</kbd>                              |   Previous image    |
|                                     <kbd>→</kbd>, <kbd>↵</kbd>, <kbd>N</kbd>, <kbd>Space</kbd>                                     |     Next image      |
| <kbd>⌘</kbd> /<kbd>Ctrl</kbd><kbd>→</kbd>, <kbd>⌘</kbd> /<kbd>Ctrl</kbd><kbd>N</kbd>, <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>Space</kbd> | Next unviewed image |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>F</kbd>                                              |     Go to image     |
|                                                     <kbd>+</kbd>, <kbd>=</kbd>                                                     |       Zoom in       |
|                                                     <kbd>-</kbd>, <kbd>_</kbd>                                                     |      Zoom out       |
|                                                            <kbd>I</kbd>                                                            |  Invert greyscale   |
|                                               <kbd>⌘</kbd>/<kbd>Ctrl</kbd> + Scroll                                                |    Window width     |
|                                                       <kbd>⇧</kbd> + Scroll                                                        |    Window centre    |
|                                                            <kbd>W</kbd>                                                            |   Reset windowing   |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>W</kbd>                                              |   Auto-windowing    |
|                                                            <kbd>R</kbd>                                                            | Rotate images right |
|                                                            <kbd>L</kbd>                                                            | Rotate images left  |
|                                    <kbd>1</kbd>, <kbd>2</kbd>, <kbd>3</kbd>, <kbd>4</kbd>, etc                                     | Select radiobutton  |
|                                                            <kbd>S</kbd>                                                            |        Save         |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>S</kbd>                                              |       Save as       |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>E</kbd>                                              |    Export to CSV    |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>Q</kbd>                                              |        Quit         |
|                                              <kbd>⌘</kbd>/<kbd>Ctrl</kbd><kbd>T</kbd>                                              |     Reset Theme     |


Note: <kbd>⌘</kbd> + Scroll and <kbd>⇧</kbd> + Scroll are only currently available on Mac OS X.

### Conflict Resolution

Speedy QC can also be used to resolve conflicts between 2 annotators.

To do this:
1. When creating a new annotations project define the task using the same
definitions as the multiple annotators.
2. Check the `Resolve Conflicts between Annotators` checkbox.
3. Select the json file containing the annotations of the first and second annotators.

When resolving conflicts:
- You will only showed the images that exhibit at least one disagreement between the two annotators.
- You will not be able to modify the annotations of pathology that both annotators agree on.
- You will see all bounding boxes and notes of both annotators.
- You cannot draw new bounding boxes or make notes
- Radiobuttons are currently ignored completely in conflict resolution.
- You should save as .json file as exporting to .csv has not been tested.

Customisation
-------------

The program can be customised to suit the user's needs. The following options are available:
- Select which checkboxes are required
- Select whether checkboxes can be set to 'uncertain' (i.e. 1 - see above / tristate checkboxes)
- Select whether radiobuttons are required
- Change the maximum number of backups
- Backup frequency in minutes
- Change the backup directory
- Change the log directory

### YAML File

These configuration settings are stored in the `config.yml` file in the `speedy_qc` directory. This
can be edited directly if desired or a new version can be created and loaded when starting a new annotation project.


Backup Files
------------

Work is automatically backed up every 5 minutes, but this interval can be customised. By default, the backups are 
stored in the user's home directory (`~`) in the folder `~/speedy_qc/backups` and up to the latest ten backups are 
stored. The number of backups, the backup interval and the backup directory can be customised in the configuration 
wizard or the `config.yml` file.


Executable Application
----------------------

A downloadable executable should be available soon. In the meantime, the program can be run from the command line
or an executable can be created from the source code using the instructions below.

### Creating an Executable

An executable can be created using `py2app` for Mac OS X or `py2exe` for Windows. The customised `setup_py2app_****.py`
scripts have been included for `py2app` for both 86x64 (*Intel*) and arm64 (*Apple Silicon*) architectures on OS X. 
These may work out of the box but may need some tweaking for your local environment. For example, if the libffi library 
is in a different directory (see below) or if you are using a different version of Python (3.10) to that used in 
development (e.g. a `|` operator is used to join dictionaries for example, which is new in Python 3.9, so this would need
changing for Python 3.8).

To create an executable with `py2app` on 86x64, the following command can be used from inside the `speedy_qc` directory
on a 86x64 Mac, or using an 86x64 conda environment or using Rosetta 2 on a arm64 Mac:

```bash
python setup_86x64.py py2app
```

For arm64, the following command can be used, but note that if using conda, it must be an arm64 conda environment:

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

#### Creating a Universal Binary

A universal binary can be created by combining the two executables created by `py2app`. This can be done using the
`lipo` command after both executables have been created (e.g. inside arm64 and 86x64 conda environments). 
To create a universal binary for the 86x64 and arm64 executables, use the following commands:

```bash
mkdir -p "dist/universal/Speedy QC.app/"
cp -R "dist/arm64/Speedy QC.app/" "dist/universal/Speedy QC.app/"
rm -rf "dist/universal/Speedy QC.app/Contents/MacOS/Speedy QC"
rm -rf "dist/universal/Speedy QC.app/Contents/MacOS/Python"
lipo -create -output "dist/universal/Speedy QC.app/Contents/MacOS/Speedy QC" "dist/arm64/Speedy QC.app/Contents/MacOS/Speedy QC" "dist/86x64/Speedy QC.app/Contents/MacOS/Speedy QC"
lipo -create -output "dist/universal/Speedy QC.app/Contents/MacOS/Python" "dist/arm64/Speedy QC.app/Contents/MacOS/Python" "dist/86x64/Speedy QC.app/Contents/MacOS/Python"
```

#### libffi

The libffi library is required for the executable to run on MacOS. This can be installed using Homebrew:

```bash
brew install libffi
```

If using a arm64 Mac, the libffi library will be installed in the `/opt/homebrew/Cellar` directory, whilst the 86x64
version will be installed in the `/usr/local/opt` directory. The `setup_86x64.py` and `setup_arm64.py` scripts
have been configured to look for the library in the `/opt/homebrew` directory. If the library is installed in a
different directory, the `setup_86x64.py` and `setup_arm64.py` scripts will need to be modified accordingly.
