from setuptools import setup, find_packages
import os

print("*"*100)
print("Running setup.py")
print("*"*100)

setup(
    author='Ian Selby',
    author_email='ias49@cam.ac.uk',
    description='Tool to label single DICOM images using custom checkboxes',
    name='speedy_qc',
    url='https://github.com/selbs/speedy_qc',
    use_scm_version=True,
    setup_requires=["setuptools_scm>=7.0.4"],
    packages=find_packages(include=['speedy_qc', 'speedy_qc.*']),
    include_package_data=True,
    package_data={'': ['assets/*', 'checkboxes.yml']},
    entry_points={
        'console_scripts': [
            'speedy_qc=speedy_qc.main:main',
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
        "PyQt6>=6.4.2",
        "python-gdcm>=3.0.21",
        "PyYAML>=6.0",
        "qimage2ndarray>=1.10.0",
        "qt-material>=2.14",
        "QtAwesome>=1.2.3",
    ],
)

print("*"*100)
print(os.path.join('your_package_name', 'icons', '*'))
print("*"*100)
