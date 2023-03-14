from setuptools import setup, find_packages

setup(
    author='Ian Selby',
    author_email='ias49@cam.ac.uk',
    description='Tool to label DICOM images with simple checkboxes',
    name='speedy_cxr',
    url='https://gitlab.developers.cam.ac.uk/maths/cia/covid-19-projects/speedy_cxr',
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(include=['speedy_cxr', 'speedy_cxr.*']),
    entry_points={
        'console_scripts': [
            'speedy_cxr=speedy_cxr.main:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # python_requires="",
    # install_requires=[
    # ],
)
