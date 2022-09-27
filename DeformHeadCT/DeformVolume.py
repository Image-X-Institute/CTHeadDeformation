# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 16:14:11 2022

@author: mgar5380
"""

#External Modules
import re
import shutil
import argparse
import numpy as np
import SimpleITK as sitk
from pathlib import Path

#Platipy Modules
from platipy.imaging.registration.utils import apply_transform

from DeformHeadCT.VolumeInfo import VolumeDeformation
#Custom Mdules
from DeformHeadCT.deformation import (
    PrepareRegistration,
    HeadDeformation
    )

def DeformationScript(InfoFile,RegParamFile='examples/Elastix_BSpline_OpenCL_RigidPenalty.txt',DeleteTempFile=True,DoRigidNonRigidRegistration=True):#,RegenerateExistingFiles=True):
    """
    Main Section of the code

    Parameters
    ----------
    InfoFile : str
        json file containing the information about the volume
    RegParamFile : str
        Rigid/Non-rigid Parameter file for the registration 
    DeleteTempFile : bool,optional
        If True the temporary files created by this function will be deleted after the new dicom files have been created
    RegenerateExistingFiles : bool,optional
        If False if any of the temporary files (except for the deformed CT and registration files) already exist they won't be recreated.
        If True even if the files already exist they will be regenerated

    Returns
    -------
    None.

    """
    
    assert Path(RegParamFile).is_file(), "Elastix parameter file {} does not exist".format(RegParamFile)

    #Get volume information from json file
    VolInfo = VolumeDeformation(InfoFile=InfoFile)
    
    if VolInfo.StructDir:
        structShiftFlag = 1
    else:
        structShiftFlag = 0

    #Oorganise the data and convert dicom volumes to nifti files
    VolInfo.PrepareDcmData()

    #Do the Head Rotation
    HeadDef = HeadDeformation(VolInfo.nifti_directory,VolInfo.patientunderscore,structShiftFlag)

    if np.count_nonzero(VolInfo.angles) > 0:
        assert HeadDef.ApplyHeadRotation(VolInfo.coordinates_cutoff,VolInfo.angles,VolInfo.axes,VolInfo.point_of_rotation) >= 0   

    #Do the rigid shift of the structures
    if structShiftFlag:
        HeadDef.ApplyGTVShift(VolInfo.Structure_Shift,VolInfo.Structure_Names)

    
    if DoRigidNonRigidRegistration:
    
        if np.count_nonzero(VolInfo.angles) > 0 or structShiftFlag:
        
            InitialTransform = sitk.DisplacementFieldTransform(
                sitk.Cast(HeadDef.dvf_field, sitk.sitkVectorFloat64)
            )
        
            #Deform CT volume using initial transformation
            image_ct_deformed = apply_transform(HeadDef.image_ct, transform=InitialTransform, interpolator=sitk.sitkLinear)
        
            #Do the rigid/non-rigid registration
            dvf_New = PrepareRegistration(HeadDef.image_ct,image_ct_deformed,VolInfo.nifti_directory,RegParamFile)
        else:
            dvf_New = HeadDef.dvf_field

    #Cast dvf prior to transformation
    FinalTransform = sitk.DisplacementFieldTransform(
        sitk.Cast(dvf_New, sitk.sitkVectorFloat64)
    )
    
    #Use DVF to deform CT
    image_ct_deformed2 = apply_transform(HeadDef.image_ct, transform=FinalTransform, interpolator=sitk.sitkLinear)

    deformed_structures = {}

    #apply dvf field to deformed_structures
    if structShiftFlag:       
        
        structures = {re.findall(".*_RTSTRUCT_(.*).nii.gz", p.name)[0]: sitk.ReadImage(str(p)) for p in HeadDef.structure_paths}
        for struct in structures:
            #deformed_structures[struct] = apply_field(structures[struct], dvf_transform, structure=True, default_value=0,interp=sitk.sitkLinear)
            deformed_structures[struct] = apply_transform(structures[struct], transform=FinalTransform, default_value=0,interpolator=sitk.sitkLinear)
        
    #Write the deformed ct image and deformed structures to the OutputDir directory
    VolInfo.WriteVolumesToFile(image_ct_deformed2,structShiftFlag,deformed_structures)

    #Delete any temporary files
    if DeleteTempFile:       
        shutil.rmtree(input_dcm_dir = str(VolInfo.nifti_directory) + '/dicom')
        shutil.rmtree(VolInfo.nifti_directory)
        if structShiftFlag:
            shutil.rmtree(Path(VolInfo.OutputDir + '/OutputStructures'))

#DeformationScript('examples/OneAxisRotationAndGTVShift.json','examples/Elastix_BSpline_OpenCL_RigidPenalty.txt',DeleteTempFile=False,RegenerateExistingFiles=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Input is a set of CT dicom files. Deforms the volume and outputs a new set of dicom files containing the deformed CT volume.')
    parser.add_argument('InfoFile', type=str, help='File path of the Input Json file containing the deformation information')
    parser.add_argument('RegParamFile',type=str,default='examples/Elastix_BSpline_OpenCL_RigidPenalty.txt',help='The elastix parameter file that controls the rigid/non-rigid registration. Default location is examples/Elastix_BSpline_OpenCL_RigidPenalty.txt ')

    #Changed so that the default is to delete the temporary files to be in line with the main script. 
    parser.add_argument('DontDeleteTempFile',action='store_true', help='If False will delete the temporary files that are created in the Json file variable TempDirectory.')
    parser.add_argument('DoRigidNonRigidRegistration',action='store_true', help='If True will perform the rigid/non-rigid registration as a final smoothing step using the elastix parameter file.')
    
    args = parser.parse_args()
    assert args.InfoFile, "InfoFile {} does not exist".format(args.Info)
    
    DeformationScript(args.InfoFile,args.RegParamFile,DeleteTempFile=not(args.DontDeleteTempFile),DoRigidNonRigidRegistration=args.DoRigidNonRigidRegistration)
    
    #Map command line arguments to function arguments.
    #DeformationScript(*sys.argv[1:])