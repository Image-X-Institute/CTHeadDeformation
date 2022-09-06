# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 10:45:57 2022

@author: mgar5380
"""

from pathlib import Path
import sys
import numpy as np
from shutil import rmtree
import glob

'''
For testing/ example purposes it's safest to manually append the path variable to ensure our 
package will always be found. This isn't necessary once we actually install the package 
because installation in python essentially means "copying the package to a place where it can be found"
'''
this_file_loc = Path(__file__)
sys.path.insert(0, str(this_file_loc.parent.parent))
# note: insert(0) means that the path is above is the FIRST place that python will look for imports
# sys.path.append means that the path above is the LAST place
from DeformHeadCT.DeformVolume import DeformationScript
from DeformHeadCT.DataPreparation import MoveDCMFiles,GetPointOfRotation
from platipy.dicom.download.tcia import get_hn_data,fetch_data,get_patients_in_collection

def test_Moving_Dicom_Files():
    '''
    Download some dicom data from The Cancer Imaging Archive, move the data and evaluate whether it has been successful. 

    '''
    CollectionStr = 'Lung Phantom'
    
    outputDir = './tcia'
    
    NewDir = './tciaCopied'
    
    data = fetch_data(CollectionStr,
               patient_ids = get_patients_in_collection(CollectionStr) ,
               modalities=['CT'],
               nifti=False,
               output_directory=outputDir)
    
    try:
       
        patient_id = next(iter(data)) 
        
        dicomStr = next(iter(data[next(iter(data))]['DICOM']['CT'])) 
       
        InputDcmDir = str(data[patient_id]['DICOM']['CT'][dicomStr])
       
        Path.mkdir(Path(NewDir),parents=False, exist_ok=True) 
       
        MoveDCMFiles(Input_dcm_dir=InputDcmDir, Output_dcm_dir=NewDir) 
       
        filesInput = glob.glob(InputDcmDir + '/*') 
       
        filesOutput = glob.glob(NewDir + '/*.dcm')
        
        assert len(filesOutput) == len(filesInput)
       
        rmtree(Path(outputDir))
        rmtree(Path(NewDir))
    except Exception:
        rmtree(Path(outputDir))
        rmtree(Path(NewDir))
        assert False 
        
def test_Get_Head_Rotation_Point():
    '''
    Read Head rotation point from example json file
    '''
    
    InputJsonFile = 'examples/OneAxisRotation.json'
    
    PointOfRotation = GetPointOfRotation(InputJsonFile)
    
    PtRot2 = [93, 228, 258]
    
    for i in range(0,len(PointOfRotation)):
        assert PointOfRotation[i] == PtRot2[i]
    