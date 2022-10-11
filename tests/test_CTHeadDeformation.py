# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 10:30:33 2022

@author: mgar5380
"""
import os
import subprocess
from pathlib import Path
import sys
import numpy as np
from shutil import rmtree
import glob
import json

'''
For testing/ example purposes it's safest to manually append the path variable to ensure our 
package will always be found. This isn't necessary once we actually install the package 
because installation in python essentially means "copying the package to a place where it can be found"
'''
this_file_loc = Path(__file__)
sys.path.insert(0, str(this_file_loc.parent.parent))
# note: insert(0) means that the path is above is the FIRST place that python will look for imports
# sys.path.append means that the path above is the LAST place
#from DeformHeadCT.DeformVolume import DeformationScript
from DeformHeadCT.VolumeInfo import VolumeDeformation
from DeformHeadCT.DataPreparation import (
    MoveDCMFiles,
    GetPointOfRotation
    )


def test_VolumeInfoInit():
    '''
    Test whether the initialisation of the VolumeInfo class creates the class variables properly
    '''
    
    patient_id = 'zz_Elshin'
    patientunderscore = 'zz_Elshin'
    
    axes = [-1,0,0]
    angles = [2.5]
    Structure_Shift = [1,0,0]
    coordinates_cutoff = [[85, 303, 261], [72, 202, 254]]
    
    VertDict = {}
    VertDict['Oc-C1'] = [118, 239, 258]
    VertDict['C1-C2'] = [111, 235, 257]
    VertDict['C2-C3'] = [101, 230, 256]
    
    InputDir = 'examples/PhantomDicomData'
    StructDir = 'test'
    OutputDir = 'examples/TestingGitHubThing'
    nifti_directory = 'examples/TestingTempDir'
    Structure_Names = 'test'
    
    #Create variable using custom inputs
    TestInfo = VolumeDeformation(patient_id = patient_id,patientunderscore = patientunderscore, axes = axes, angles = angles,
                                 Structure_Shift = Structure_Shift,OutputDir = OutputDir, nifti_directory = nifti_directory,
                                 Structure_Names = Structure_Names,InputDir = InputDir,StructDir = StructDir,
                                 coordinates_cutoff=coordinates_cutoff,VertDict=VertDict)
    
    assert TestInfo.patient_id == patient_id, 'patient_id variables are not equal {} {}'.format(TestInfo.patient_id,patient_id)
    assert TestInfo.patientunderscore == patientunderscore, 'patientunderscore variables are not equal {} {}'.format(TestInfo.patientunderscore,patientunderscore)
    
    assert TestInfo.axes == axes, 'axes variables are not equal {} {}'.format(TestInfo.axes,axes)
    assert TestInfo.angles == angles, 'angles variables are not equal {} {}'.format(TestInfo.angles,angles)
    assert TestInfo.Structure_Shift == Structure_Shift, 'Structure_Shift variables are not equal {} {}'.format(TestInfo.Structure_Shift,Structure_Shift)
    assert TestInfo.coordinates_cutoff == coordinates_cutoff, 'co-ordinates_cutoff variables are not equal {} {}'.format(TestInfo.coordinates_cutoff,coordinates_cutoff)
    assert TestInfo.point_of_rotation == [VertDict['C1-C2']], 'Point(s) of Rotation are not equal {} {}'.format(TestInfo.point_of_rotation,VertDict['Oc-C1'])
    
    assert TestInfo.InputDir == InputDir, 'InputDir variables are not equal {} {}'.format(TestInfo.InputDir,InputDir)
    assert TestInfo.StructDir == StructDir, 'StructDir variables not are equal {} {}'.format(TestInfo.StructDir,StructDir)
    assert TestInfo.OutputDir == OutputDir, 'OutputDir variables not are equal {} {}'.format(TestInfo.OutuputDir,OutputDir)
    assert TestInfo.nifti_directory == Path(nifti_directory), 'nifti_directory variables are not equal {} {}'.format(TestInfo.nifti_directory,nifti_directory)
    assert TestInfo.Structure_Names == Structure_Names, 'Structure_Names variables are not equal {} {}'.format(TestInfo.Structure_Names,Structure_Names)
    
    JsonInfoFile = 'examples/OneAxisRotation.json'
    
    #Create variable using a json file
    JsonTestInfo = VolumeDeformation(InfoFile=JsonInfoFile)
    
    assert JsonTestInfo.patient_id == patient_id, 'patient_id variables are not equal {} {}'.format(JsonTestInfo.patient_id,patient_id)
    assert JsonTestInfo.patientunderscore == patientunderscore, 'patientunderscore variables are not equal {} {}'.format(JsonTestInfo.patientunderscore,patientunderscore)
    
    assert JsonTestInfo.axes == axes, 'axes variables are not equal {} {}'.format(JsonTestInfo.axes,axes)
    assert JsonTestInfo.angles == angles, 'angles variables are not equal {} {}'.format(JsonTestInfo.angles,angles)
    #assert JsonTestInfo.Structure_Shift == Structure_Shift, 'Structure_Shift variables are not equal {} {}'.format(JsonTestInfo.Structure_Shift,Structure_Shift)
    assert JsonTestInfo.coordinates_cutoff == coordinates_cutoff, 'co-ordinates_cutoff variables are not equal {} {}'.format(JsonTestInfo.coordinates_cutoff,coordinates_cutoff)
    assert JsonTestInfo.point_of_rotation == [VertDict['C1-C2']], 'Point(s) of Rotation are not equal {} {}'.format(JsonTestInfo.point_of_rotation,VertDict['Oc-C1'])
    
    
    assert JsonTestInfo.InputDir == InputDir, 'InputDir variables are not equal {} {}'.format(JsonTestInfo.InputDir,InputDir)
    #assert JsonTestInfo.StructDir == StructDir, 'StructDir variables not are equal {} {}'.format(JsonTestInfo.StructDir,StructDir)
    assert JsonTestInfo.OutputDir == OutputDir, 'OutputDir variables not are equal {} {}'.format(JsonTestInfo.OutuputDir,OutputDir)
    assert JsonTestInfo.nifti_directory == Path(nifti_directory), 'nifti_directory variables are not equal {} {}'.format(JsonTestInfo.nifti_directory,nifti_directory)
    #assert JsonTestInfo.Structure_Names == Structure_Names, 'patientunderscore variables are not equal {} {}'.format(JsonTestInfo.Structure_Names,Structure_Names)

    assert Path(nifti_directory).is_dir(),'TempDirectory {} not created'.format(JsonTestInfo.nifti_directory)
    assert Path(OutputDir).is_dir(),'InputDirectory {} not created'.format(JsonTestInfo.OutputDir)
    
    rmtree(nifti_directory)
    rmtree(Path(OutputDir))
    
def test_RotationPoint():
    '''
    Test whether the rotation points can be extracted from anatomic landmarks
    '''
    VertDict = {}
    VertDict['Oc-C1'] = [118, 239, 258]
    VertDict['C1-C2'] = [111, 235, 257]
    VertDict['C2-C3'] = [101, 230, 256]

    VertDict['axes'] = [[1,0,0],[0,1,0],[0,0,1]]
    VertDict['angles'] = [1,1,1]    
    
    point_of_rotation = GetPointOfRotation(VertDict)
    
    assert point_of_rotation[0] == VertDict['C1-C2'], 'Error in point_of_rotation[0]'
    assert point_of_rotation[1] == VertDict['C2-C3'], 'Error in point_of_rotation[1]'
    assert point_of_rotation[2] == VertDict['Oc-C1'], 'Error in point_of_rotation[2]'
    
def test_PrepareDcmData():
    '''
    Puts the data into a format that can be recognised by platipy
    '''
    JsonInfoFile = 'examples/OneAxisRotation.json'
    
    JsonTestInfo = VolumeDeformation(InfoFile=JsonInfoFile)    
    
    #Oorganise the data and convert dicom volumes to nifti files
    JsonTestInfo.PrepareDcmData()

    input_dcm_dir = str(JsonTestInfo.nifti_directory) + '/dicom'
    
    assert Path(input_dcm_dir).is_dir(),'Dicom directory not created'
    
    input_dcm_ct_dir = input_dcm_dir + '/ct'
    
    assert Path(input_dcm_ct_dir).is_dir(),'CT directory not created'
    
    OriginalFileList = glob.glob(JsonTestInfo.InputDir + '/*')
    
    for OriginalFile in OriginalFileList:
        
        FileName = os.path.basename(OriginalFile)
        
        assert input_dcm_ct_dir + '/' + FileName, '{} file does not exist'.format(FileName)
    
    rmtree(JsonTestInfo.OutputDir)
    #rmtree(str(JsonTestInfo.nifti_directory))
    rmtree(input_dcm_dir)
    
def test_ElastixInstalled():
    
    home_dir = Path(os.path.expanduser('~'))  # may have to update for github system
    elastix_dir = home_dir / 'ElastixDownload' / 'elastix-5.0.1-linux' / 'bin'
    elastix_lib_dir = home_dir / 'ElastixDownload' / 'elastix-5.0.1-linux' / 'lib'
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + ':' + str(elastix_dir)
    my_env["LD_LIBRARY_PATH"] = my_env["LD_LIBRARY_PATH"] + ':' + str(elastix_lib_dir)
    #bashCommand = "/home/runner/ElastixDownload/elastix-5.0.1-linux/bin/elastix -h"
    bashCommand = "elastix -h"
    assert subprocess.Popen(bashCommand.split(), env=my_env) == 0, 'Error with installation of elastix'
    
"""
def test_ElastixInstalled():
    
    #command_run = subprocess.call('elastix -h')
    command_run = subprocess.run('elastix -h')
    
    command_run.check_returncode()
    
    #assert command_run == 0, 'Error with installation of elastix'
    #assert command_run.exit_code == 0, 'Error with installation of elastix'
"""
"""
def test_DeformationScript():
    '''
    Test the whole thing
    '''
    JsonInfoFile = 'examples/OneAxisRotation.json'
    
    paraFile = 'examples/Elastix_BSpline_OpenCL_RigidPenalty.txt'
    
    DeformationScript(JsonInfoFile,RegParamFile=paraFile)
"""    
    
    
