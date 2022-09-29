# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:25:28 2022

Example of how to setup and run the Head deformation code

@author: Mark Gardner

Last Edited: 25/07/2022

"""

import json
from pathlib import Path
import sys

def ChangeJsonFile(InfoFile,NewVars):
    '''
    Function for writing data to the example json files
    '''  
    with open(InfoFile) as json_file:
        data = json.load(json_file)
    
    for key in NewVars:
        data[key] = NewVars[key]
    
    with open(InfoFile,'w') as json_file:
        json.dump(data,json_file)  


'''
For testing/ example purposes it's safest to manually append the path variable to ensure our 
package will always be found. This isn't necessary once we actually install the package 
because installation in python essentially means "copying the package to a place where it can be found"
'''
this_file_loc = Path(__file__)
sys.path.insert(0, str(this_file_loc.parent.parent))
'''
Now we can guarantee that the package will be found we can import it:
'''

from DeformHeadCT.DeformVolume import DeformationScript
'''
 Do a simple one axis head rotation
'''

'''
Define the location of the json file
'''
InfoFile = 'examples/OneAxisRotation.json'
elastixParamFile = 'examples/Elastix_BSpline_OpenCL_RigidPenalty.txt'

'''
Change the template json file variables to input the location of the dicom files
'''
#NewVars = {}

#NewVars['name'] = 'CHIRP_01'
#NewVars['InputDirectory'] = "Z://2RESEARCH/1_ClinicalData/CHIRP/Blacktown/Patient Files/PAT01/Planning Data and CBCTs/2/10/CT/20220201"
#NewVars['OutputDirectory'] = 'dicom'

#ChangeJsonFile(InfoFile,NewVars)

'''
Run the function
'''
DeformationScript(InfoFile,RegParamFile=elastixParamFile)