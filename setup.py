from setuptools import setup, find_packages

setup(
    author='Ian Selby',
    author_email='ias49@cam.ac.uk',
    description='Tool to label DICOM images with simple checkboxes',
    name='speedy_qc',
    url='https://github.com/selbs/speedy_cxr',
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(include=['speedy_qc', 'speedy_qc.*']),
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
        "Bottleneck==1.3.5",
        "certifi==2022.6.15",
        "flit-core==3.6.0",
        "install==1.3.5",
        "mkl-service==2.4.0",
        "numexpr==2.8.4",
        "pandas==1.5.3",
        "pip==23.0.1",
        "pydicom==2.3.1",
        "pylibjpeg==1.4.0",
        "numpy>=1.21.0",
        "PyQt5==5.15.9",
        "python-gdcm==3.0.21",
        "QDarkStyle==3.0.2",
        "setuptools-scm==7.0.4"
    ]
)
