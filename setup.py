# -*- coding: utf-8 -*-

from setuptools import setup
import re, io

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',  # It excludes inline comment too
    io.open('DeformHeadCT/__init__.py', encoding='utf_8_sig').read()
    ).group(1)
setup(
    name ='CTHeadDeformation',
    python_requires = '>=3.7',
    packages = ['DeformHeadCT'],
    version = __version__,
    license = 'MIT',
    description = 'Perform Realistic Head Deformations',
    author = 'Mark Gardner',
    author_email='mark.gardner@sydney.edu.au',
    url = 'https://github.sydney.edu.au/Image-X/CTHeadDeformation',
    download_url = '',
    keywords = ['CT', 'deformation', 'head and neck'],
    install_requires=['SimpleITK', 
                      'platipy',
                      'numpy'],
    long_description_content_type = 'text/markdown',
    long_description=open('README.md').read(),
)
