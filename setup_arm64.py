from setuptools import setup, find_packages

APP = ['speedy_qc/main.py']
OPTIONS = {'iconfile': 'speedy_qc/assets/icns/white_panel.icns', 'includes': ['_cffi_backend'],
           'resources': ['speedy_qc/assets', 'speedy_qc/config.yml', 'speedy_qc/log.conf'],
           'dylib_excludes': ['libgfortran.3.dylib'],
           'frameworks': ['/opt/homebrew/Cellar/libffi/3.4.4/lib/libffi.8.dylib'],
           'dist_dir': 'dist/arm64',
           } | dict(plist=dict(NSRequiresAquaSystemAppearance=False,
                               CFBundleIconFile="speedy_qc/assets/icns/white_panel.icns",
                               ))

setup(
    app=APP,
    author='Ian Selby',
    author_email='ias49@cam.ac.uk',
    description='Tool to label single DICOM images using custom checkboxes',
    name='Speedy QC',
    url='https://github.com/selbs/speedy_qc',
    use_scm_version=True,
    setup_requires=["setuptools_scm>=7.0.4", "py2app>=0.28"],
    packages=find_packages(),
    include_package_data=True,
    options={'py2app': OPTIONS},
    entry_points={
        'console_scripts': [
            'speedy_qc=speedy_qc.main:main',
            'speedy_config=speedy_qc.config_wizard:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Bottleneck>=1.3.5",
        "flit-core>=3.6.0",
        "install>=1.3.5",
        "pandas>=1.5.3",
        "pip>=23.0.1",
        "pydicom==2.3.1",
        "pylibjpeg==1.4.0",
        "numpy>=1.21.0",
        "setuptools>=42.0.0",
        "PyQt6>=6.2",
        "python-gdcm>=3.0.21",
        "PyYAML>=6.0",
        "qimage2ndarray>=1.10.0",
        "qt-material>=2.14",
        "QtAwesome>=1.2.3",
        "matplotlib>=3.4.3"
    ],
)
