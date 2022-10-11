## CT Head Deformation

[![Python application](https://github.com/ACRF-Image-X-Institute/CTHeadDeformation/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/ACRF-Image-X-Institute/CTHeadDeformation/actions/workflows/python-app.yml)
[![codecov](https://codecov.io/gh/ACRF-Image-X-Institute/CTHeadDeformation/branch/main/graph/badge.svg?token=WETEA11B5D)](https://codecov.io/gh/ACRF-Image-X-Institute/CTHeadDeformation)

**Author:** *Mark Gardner*

The CTHeadDeformation module is an open-sourced library for taking CT and cone-beam CT (CBCT) scans and deforming these scans in a way that simulates realistic head motion. Deforming CT and CBCT scans can be used for:

- Studying how realistic patient motion can affect the treatment plan/delivered treatment dose.
- Data augmentation for training robust deep-learning networks.
- Simulating how realistic patient motion can affect the accuracy of CT/CBCT reconstructions.
- Other applications involving realistic patient head motion.

The image below shows example of how the original CT volume (left) can be realistically deformed to simulate a patient tilting their head up (right). The red lines are added to show how the anatomical landmarks have either moved or remained stationary after the deformation is complete.

![image](https://media.github.sydney.edu.au/user/5547/files/cf5b651f-fcde-4603-a6d7-d487df5e9904)

Further information can be found in the repo wiki (https://github.sydney.edu.au/ACRF-Image-X-Institute/CTHeadDeformation/wiki) which is updated (semi) regularly. 

## Setup/Build/Install

The module can be installed using pip:

```
pip install CTHeadDeformation
```

This code uses the platipy repo (https://github.com/pyplati/platipy). If the platipy module is not automatically installed when installing the CTHeadDeformation code, the platipy library can be installed separately using the installation instructions (https://pyplati.github.io/platipy/getting_started.html). 

Install elastix (https://elastix.lumc.nl/index.php)

Add the elastix.exe program pathfile to the system path.

## Usage

The code DeformVolume.py is the main function. The deformation information is passed to this function in the form of a .json file. There are examples of .json files in the examples directory. The path to this json file is then the main input for the function DeformVolume.py

Example:
Open up the file OneAxisRotation.json and tell the json file to deform the dicom files in directory "dicomSource" by changing
```
"InputDirectory":""
```

to  

```
"InputDirectory":"dicomSource"
```

Also change the variable "name" to the 'Patient's name' variable as defined in the dicom metadata. 

### Run in python script

```
from DeformHeadCT.DeformVolume import DeformationScript
JsonInfoFile = 'examples/OneAxisRotation.json'
DeformationScript(JsonInfoFile)
```

### Command Line

In a command line (such as anaconda command prompt) navigate to the directory that the CTHeadDeformation repo was cloned to and run 
```python DeformVolume.py examples/OneAxisRotation.json```

By default the code will automatically use the elastix parameter in the examples folder, and will automatially locate the BoneMask volume required for the deformation. 

Dicom Files of head and neck CT scans are avaiable at (https://www.cancerimagingarchive.net/collections/), subject to their licence agreements. 

## Directory Structure

* DeformHeadCT - Contains the main python script and supporting functions

* examples - contains example .json files as well as an example elastix file.


