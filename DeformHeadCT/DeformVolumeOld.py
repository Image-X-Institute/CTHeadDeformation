# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 15:13:47 2022

Deforms a CT or CBCT volume by rotating the head. Output is a deformed dicom volume

@author: mgar5380
"""

#Basics
import sys
import json
import glob
import os
import re
import shutil
import argparse
import numpy as np
import SimpleITK as sitk
from pathlib import Path

#Platipy modules
from platipy.dicom.io.crawl import process_dicom_directory
from platipy.dicom.io.nifti_to_series import convert_nifti_to_dicom_series
from platipy.dicom.io.nifti_to_rtstruct import convert_nifti
from platipy.imaging.generation.mask import get_external_mask
from platipy.imaging.generation.dvf import generate_field_shift
from platipy.imaging.registration.utils import apply_transform

#Custom modules
from DeformHeadCT.deformation import (
    generate_field_rotation,
    PrepareRegistration
    )
from DeformHeadCT.utils import get_head_mask
from DeformHeadCT.DataPreparation import (
    MoveDCMFiles,
    GetPointOfRotation
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
    

    #Read json file to get the deformation variables  
    #RegParamFile = ''
    
    with open(InfoFile) as json_file:
        data = json.load(json_file)
    
    assert Path(RegParamFile).is_file(), "Elastix parameter file {} does not exist".format(RegParamFile)
    
    patient_id = data['name']
    
    #input_dcm_dir = data['input_directory'] + '/' + data['CTDir'] #+ '/CT'
    
    if 'axes' in data:
        axes = data['axes']
    else:
        axes = []
    
    if 'angles' in data:
        angles = data['angles']
    else:
        print('No Head Rotations detected, determined by "angles" variable')
        angles = []
    
    if "StructureFile" in data:
        StructDir = data['StructureFile']
    else:
        print('No "StructureFile" variable detected in Input Json File')
        StructDir = ''    
    
    if StructDir:
        if ('Structure_Shift' in data) and ('Structure_Names' in data):
            structShiftFlag = 1
        else:
            structShiftFlag = 0
        
            if 'Structure_Shift' in data:
                print('No Variable "Structure_Names"')
                
            if 'GTVLabel' in data:
                print('No Variable "Structure_Shift"')
    else:
         structShiftFlag = 0   
    
    #Get centre points of rotation
    if 'angles' in data:
        point_of_rotation = GetPointOfRotation(data)
    
    if 'coordinates_cutoff' in data:
        coordinates_cutoff = data['coordinates_cutoff']
    else:
        if 'angles' in data:
            assert 'coordinates_cutoff' in data, "No variable 'coordinates_cutoff' in json file"
        else:
            coordinates_cutoff = []
            
    
    assert "InputDirectory" in data, "No variable 'InputDirectory' in json file"
    
    InputDir = data['InputDirectory']
    
    assert "OutputDirectory" in data, "No variable 'OutputDirectory' in json file"
    
    OutputDir = data['OutputDirectory']
    
    Path.mkdir(Path(OutputDir),parents=False, exist_ok=True)
    
    if "TempDirectory" in data:
        nifti_directory = Path(data['TempDirectory'])
        
    else:
        print('No Temp directory detected in Input Json File')
        nifti_directory = Path(OutputDir + '/nifti')
    
    Path.mkdir(nifti_directory,parents=False, exist_ok=True)
    
    patientunderscore = patient_id.replace('-','_')
    
    #Move input dicom files into one folder in the folder required for processing (Make sure to delete later)
    
    input_dcm_dir = str(nifti_directory) + '/dicom'
    
    Path.mkdir(Path(input_dcm_dir),parents=False, exist_ok=True)
    
    input_dcm_ct_dir = input_dcm_dir + '/ct'
    Path.mkdir(Path(input_dcm_ct_dir),parents=False, exist_ok=True)
    MoveDCMFiles(InputDir,input_dcm_ct_dir)
    
    if StructDir:
        input_dcm_struct_dir = input_dcm_dir + '/rtstruct'
        Path.mkdir(Path(input_dcm_struct_dir),parents=False, exist_ok=True)
        MoveDCMFiles(StructDir,input_dcm_struct_dir)
    
    #Convert from dicom volumes to nifti volumes. Should auto detect if there is or isn't a struct dir
    process_dicom_directory(input_dcm_dir,output_directory=nifti_directory)

    #Define nifti volumes to work with     
    ct_path = next(iter(nifti_directory.glob(f"{patientunderscore}/IMAGES/*CT*.nii.gz")))

    if StructDir:
        # Read in structures
        structure_paths = nifti_directory.glob(f"{patientunderscore}/STRUCTURES/*.nii.gz")
        structures = {re.findall(".*_RTSTRUCT_(.*).nii.gz", p.name)[0]: sitk.ReadImage(str(p)) for p in structure_paths}

    # Read in image    
    image_ct = sitk.ReadImage(str(ct_path))

    # Automatically generate external mask
    struct_external = get_external_mask(image_ct)
    
    #generate head mask using list of coordinates as cutoff points
    head_mask = get_head_mask(struct_external,coordinates_cutoff, image_ct)
    
    #Define variables
    RotationPt = [];    
    Mask_deformed = [];
    dvf_transform = [];
    dvf_field = sitk.Image(image_ct.GetSize(), sitk.sitkVectorFloat64);
    sitk.Image.CopyInformation(dvf_field,image_ct)    
    
    if np.count_nonzero(angles) > 0:
    
        #Apply the rotations 
        try: 
            len(axes[0])
            LoopNum = len(axes)
        except:
            LoopNum = 1
            
        try:
            angles[0]
        except:
            angles = [angles]
    
        for i in range(0,LoopNum):
            try:
                len(axes[i])
                axisLoop = axes[i]
            except:
                axisLoop = axes
            
            try:
                len(point_of_rotation[i])
                RotationPt.append(point_of_rotation[i])            
            except:
                RotationPt.append(point_of_rotation)
            
            Mask_deformed_loop, dvf_transform_loop, dvf_field_loop, RotationTForm = generate_field_rotation(
                image_ct,
                head_mask,
                tuple(RotationPt[i]),
                axis_of_rotation=axisLoop,
                angle=angles[i]*np.pi/180,
                gaussian_smooth=0
                #mask_bend_from_reference_point = coordinates_cutoff
            )
            Mask_deformed.append(Mask_deformed_loop)
            dvf_transform.append(dvf_transform_loop)
            dvf_field = dvf_field + dvf_field_loop        
    
    #Do the rigid shift of the structures 
    if structShiftFlag:
        if np.count_nonzero(data['Structure_Shift']) > 0:
            if np.size(data['Structure_Shift'][0]) > 1:
                for i in range(0,len(data['Structure_Shift'])):
                    
                    if data['Structure_Names'][i] not in structures:
                        print('No Structure {}'.format(data['Structure_Names'][i]))
                    else:
                    
                        Mask_shift, dvf_shift, dvf_field_shift = generate_field_shift(
                            mask_image = structures[data['Structure_Names'][i]],
                            vector_shift = tuple(data['Structure_Shift'][i]),
                            gaussian_smooth = 2
                        )
                        #dvf_transform.append(dvf_shift)
                        
                        dvfLoop = sitk.Cast(dvf_field_shift, sitk.sitkVectorFloat32)  
                        dvfLoop.CopyInformation(dvf_field)                           
                        
                        try:
                            dvf_field = dvf_field + dvf_field_shift
                        except:
                            dvf_field = dvf_field + sitk.Cast(dvfLoop,sitk.sitkVectorFloat64) 
                        dvf_transform.append(dvf_shift)
                        Mask_deformed.append(Mask_shift)
            else:
                if data['Structure_Names'] not in structures:
                    print('No Structure {}'.format(data['Structure_Names']))
                else:
                    Mask_shift, dvf_shift, dvf_field_shift = generate_field_shift(
                        mask_image = structures[data['Structure_Names']],
                        vector_shift = tuple(data['Structure_Shift']),
                        gaussian_smooth = 2
                    )                
                    dvf_transform.append(dvf_shift)
                    Mask_deformed.append(Mask_shift)
                    
                    dvfLoop = sitk.Cast(dvf_field_shift, sitk.sitkVectorFloat32)  
                    dvfLoop.CopyInformation(dvf_field)     
                
                    try:
                        dvf_field = dvf_field + dvf_field_shift
                    except:
                        dvf_field = dvf_field + sitk.Cast(dvfLoop,sitk.sitkVectorFloat64) 
    
    if DoRigidNonRigidRegistration:
    
        if np.count_nonzero(angles) > 0 or structShiftFlag:
        
            InitialTransform = sitk.DisplacementFieldTransform(
                sitk.Cast(dvf_field, sitk.sitkVectorFloat64)
            )
        
            #Deform CT volume using initial transformation
            image_ct_deformed = apply_transform(image_ct, transform=InitialTransform, interpolator=sitk.sitkLinear)
        
            #Do the rigid/non-rigid registration
            dvf_New = PrepareRegistration(image_ct,image_ct_deformed,nifti_directory,RegParamFile)
        else:
            dvf_New = dvf_field

    #Cast dvf prior to transformation
    FinalTransform = sitk.DisplacementFieldTransform(
        sitk.Cast(dvf_New, sitk.sitkVectorFloat64)
    )
    
    #Use DVF to deform CT
    image_ct_deformed2 = apply_transform(image_ct, transform=FinalTransform, interpolator=sitk.sitkLinear)

    #apply dvf field to deformed_structures
    if StructDir:       
        deformed_structures = {}
        for struct in structures:
            #deformed_structures[struct] = apply_field(structures[struct], dvf_transform, structure=True, default_value=0,interp=sitk.sitkLinear)
            deformed_structures[struct] = apply_transform(structures[struct], transform=FinalTransform, default_value=0,interpolator=sitk.sitkLinear)
            

    outputDirCT = Path(OutputDir + '/ct')    
    outputDirCT.mkdir(exist_ok=True, parents=True)
    
    #write deformed ct to dcm
    convert_nifti_to_dicom_series(
        image=image_ct_deformed2,
        reference_dcm=input_dcm_dir + '/ct',
        output_directory=str(outputDirCT)
    )    
    
    if StructDir:        
        #Create a temporary directory to write the structures to
        TempDirStruct = Path(OutputDir + '/OutputStructures')
        TempDirStruct.mkdir(exist_ok=True, parents=True)
        
        #write structure to nifti format 
        for struct in deformed_structures:
            sitk.WriteImage(deformed_structures[struct],str(TempDirStruct / str(struct + ".nii.gz")))
        
        # rtstruct output dir 
        output_dir_dcm_STRUCT = Path(OutputDir + '/rtstruct')  
        output_dir_dcm_STRUCT.mkdir(exist_ok=True, parents=True)
    
        # dictionary containing path of nifti files
        masks = {}
        for m in os.listdir(TempDirStruct):
            name = m.split('.')[0]
            mask_path = str(TempDirStruct / m)
            masks[name] = mask_path    
    
        #convert nifti files to struct file
        convert_nifti(
            dcm_path = str(outputDirCT / "0.dcm"),
            mask_input = masks, 
            output_file = str(output_dir_dcm_STRUCT / "struct.dcm")
        )       
    
    #Delete any temporary files
    if DeleteTempFile:       
        shutil.rmtree(input_dcm_dir)
        shutil.rmtree(nifti_directory)
        if StructDir:
            shutil.rmtree(TempDirStruct)

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