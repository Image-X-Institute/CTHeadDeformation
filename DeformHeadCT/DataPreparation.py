# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 11:35:06 2022

@author: mgar5380
"""

import os
import glob
from shutil import copy2
from pathlib import Path

def MoveDCMFiles(Input_dcm_dir,Output_dcm_dir):
    """
    Copies the dicom files across from Input_dcm_dir to Output_dcm_dir, and 
    makes sure the files are in the correct format (.dcm extension) 

    Parameters
    ----------
    Input_dcm_dir : str
        Directory where the initial dicom files are stored.
    Output_dcm_dir : str
        Directory where the dicom files will be written to.

    Returns
    -------
    None.

    """
    
    if Path(Input_dcm_dir).is_dir():    
        dcmList = glob.glob(Input_dcm_dir + '/*')
        print('Copying {} files across to directory'.format(len(dcmList)))
    elif os.path.exists(Path(Input_dcm_dir)):
        dcmList = []
        dcmList.append(Input_dcm_dir)
    else:
        print('File does not exist')
        print(Input_dcm_dir)
    
    assert dcmList, "Input directory is empty"   
    
    #Copy dicom files across to new directory
    for dcmfile in dcmList:
        LoopFileName,LoopFileExt = os.path.splitext(dcmfile)
        #platipy only works when dicom files have the .dcm extension so add the extension if they don't have it. 
        name = os.path.split(dcmfile)[-1]
        if LoopFileExt == '.dcm':            
            copy2(dcmfile,Output_dcm_dir + '/' + name)
        else:
            copy2(dcmfile,Output_dcm_dir + '/' + name + '.dcm')
            
            #os.rename(LoopFileName+LoopFileExt,LoopFileName+LoopFileExt+'.dcm')
            #dcmfile = LoopFileName+LoopFileExt+'.dcm'
        #name = os.path.split(dcmfile)[-1]
        #copy2(Input_dcm_dir + '/' + name,Output_dcm_dir + '/' + name)

def GetPointOfRotation(JsonData):
    """
    Input is the data from the input json data file and the output is the series 
    of 3D points used as the centre of rotation for the head transformations

    Parameters
    ----------
    JsonData : dict
        Deformation and Volume information.

    Returns
    -------
    PointOfRotation : list
        3D points that are the centre of the head rotations. For single rotation 
        list is of size 1x3, for multiple rotations the list is size nx3

    """
    PointOfRotation = []
    try:
        len(JsonData['axes'][0])
        LoopNum = len(JsonData['axes'])
    except:
        LoopNum = 1
            
    
    for i in range(0,LoopNum):
        try:
            len(JsonData['axes'][i])
            AxisArr = JsonData['axes'][i]
        except:
            AxisArr = JsonData['axes']
    
        if abs(AxisArr[0]) == 1:
            RotationPts = JsonData['C1-C2']            
        elif abs(AxisArr[1]) == 1:
            RotationPts = JsonData['C2-C3']
        elif abs(AxisArr[2]) == 1:
            RotationPts = JsonData['Oc-C1']
    
        PointOfRotation.append(RotationPts)
            
    return PointOfRotation