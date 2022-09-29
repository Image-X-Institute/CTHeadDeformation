# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 13:58:20 2022

@author: mgar5380
"""
#External Modules
import os
import json
import SimpleITK as sitk
from pathlib import Path

#Platipy Modules
from platipy.dicom.io.crawl import process_dicom_directory
from platipy.dicom.io.nifti_to_rtstruct import convert_nifti
from platipy.dicom.io.nifti_to_series import convert_nifti_to_dicom_series

#CTHeadDeformation Modules
from DeformHeadCT.DataPreparation import (
    MoveDCMFiles,
    GetPointOfRotation
    )

"""
TODO
Add more input checking options
Add gaussian smoothing option for both head rotation and GTV shift
"""

class VolumeDeformation:
    
    def __init__(self,InfoFile = '',patient_id = '',patientunderscore = '',axes = [],angles = [],
                 InputDir = '',StructDir = '',OutputDir = '/Output',nifti_directory = '/temp',Structure_Shift = '',
                 Structure_Names = '',coordinates_cutoff = [], VertDict = {}, verbose=True):
        '''

        Parameters
        ----------
        InfoFile : str, optional
            The file location of the .json file containing the information about the volume being deformed. If empty variables need to be 
            manually entered. If InfoFile is not empty all initial variables are extracted from json file. The default is ''.
        patient_id : str, optional
            patient id as described by the dicom file. The default is ''.
        patientunderscore : str, optional
            patient_id but blank spaces are replaced by underscores. If empty the patientunderscore will be genreated using patient_id. 
            The default is ''.
        axes : array, optional
            nx3 array where the nth element is the axis around which the volume will rotate. See wiki for more info The default is [].
        angles : (float | arr), optional
            angles of rotation. If empty no head rotation will be done. The default is [].
        InputDir : str, optional
            Directory of the ct dicom files to be deformed. The default is ''.
        StructDir : str, optional
            Location of the STRUCT dicom file. The default is ''.
        OutputDir : str, optional
            Directory where the dicom values of the deformed CT will be written to. The default is '/Output'.
        nifti_directory : str, optional
            Location of the temp directory where temporary files will be written to. The default is '/temp'.
        Structure_Shift : array, optional
            1x3 array describing the magnitude of the rigid displacement of the structures in "Structure_Names". The default is ''.
        Structure_Names : (str | array), optional
            The structures to be shifted. The default is ''.
        coordinates_cutoff : array, optional
            2x3 array annotating the co-ordinates that seperate the head and the shoulders. See the wiki for more information. The default is [].
        VertDict : dict, optional
            Voxel location of the intervertebral gaps for the CT scan to be deformed. The default is {}.
        verbose : bool, optional
            If True all the warning messages will be displayed. Messages can be useful for debugging. If False no messages displayed.
            The default is True.

        Returns
        -------
        None.

        '''
        if InfoFile:
            if verbose:
                print('Defining volume parameters using input json file')
            
            #Read json file
            with open(InfoFile) as json_file:
                data = json.load(json_file)               
            
            self.patient_id = data['name']
            
            self.patientunderscore = self.patient_id.replace('-','_')
            
            if 'axes' in data:
                self.axes = data['axes']
            else:
                self.axes = ''

            if 'angles' in data:
                self.angles = data['angles']
                if 'coordinates_cutoff' in data:
                    self.coordinates_cutoff = data['coordinates_cutoff']
                else:
                    if verbose:
                        print('No "coordinates_cutoff" variable detected')
                        
                self.point_of_rotation = GetPointOfRotation(data)
            else:
                self.angles = ''
                if verbose:
                    print('No Head Rotations detected, determined by "angles" variable')     
            
            if 'InputDirectory' in data:
                self.InputDir = data['InputDirectory']
            else:
                if verbose:
                    print('No "InputDirectory" variable detected in input json file')
                self.InputDir = -1  
            
            if 'OutputDirectory' in data:
                self.OutputDir = data['OutputDirectory']
            else:
                self.OutputDir = ''
                if verbose:
                    print('No "OutputDirectory" variable detected in input json file')
  
            if 'TempDirectory' in data:
                self.nifti_directory = Path(data['TempDirectory']) 
            else:
                self.nifti_directory = ''
                if verbose:
                    print('No "TempDirectory" variable detected in input json file')
  
            if 'StructureFile' in data:
                self.StructDir = data['StructureFile']
                
                if 'Structure_Names' in data and 'Structure_Shift' in data:
                    self.Structure_Names = data['Structure_Names']
                    self.Structure_Shift = data['Structure_Shift']
                else:
                    if verbose:
                        print('Variable "Structure_Names" or "Structure_Shift" not provided')
                
            else:
                self.StructDir = ''
                if verbose:
                    print('No "StructureFile" variable detected in Input Json File')

        else:
            if verbose:
                print('Defining volume parameters manually')
            
            self.patient_id = patient_id
            
            #If patientunderscore variable not entered then it can be created using patient_id
            if not patientunderscore:
                self.patientunderscore = self.patient_id.replace('-','_')
            else:
                self.patientunderscore = patientunderscore
            
            self.axes = axes
            self.angles = angles
            self.Structure_Shift = Structure_Shift
            self.coordinates_cutoff = coordinates_cutoff
            
            self.InputDir = InputDir
            self.StructDir = StructDir
            self.OutputDir = OutputDir
            self.nifti_directory = Path(nifti_directory)
            self.Structure_Names = Structure_Names
            
            data = {};
            data['axes'] = self.axes
            if 'Oc-C1' in VertDict:
                data['Oc-C1'] = VertDict['Oc-C1']
            if 'C1-C2' in VertDict:
                data['C1-C2'] = VertDict['C1-C2']
            if 'C2-C3' in VertDict:
                data['C2-C3'] = VertDict['C2-C3']
            #Other vertebrae added in case a more complex model gets used in the future but not needed
            if 'C3-C4' in VertDict:
                data['C3-C4'] = VertDict['C3-C4']
            if 'C4-C5' in VertDict:
                data['C4-C5'] = VertDict['C4-C5']
            if 'C5-C6' in VertDict:
                data['C5-C6'] = VertDict['C5-C6']
            if 'C6-C7' in VertDict:
                data['C6-C7'] = VertDict['C6-C7']
            
            self.point_of_rotation = GetPointOfRotation(data)
           
        # Create output and temporary directories if they don't already exist
        Path.mkdir(self.nifti_directory,parents=False, exist_ok=True)
        Path.mkdir(Path(self.OutputDir),parents=False, exist_ok=True)       
        
        
    def PrepareDcmData(self):
        
        """
        Put the dicom files into the format required by platipy, and convert the dicom files to nifti files. 
        Nifti files stored in TempDirectory.
        
        """
        
        #Move input dicom files into one folder            
        input_dcm_dir = str(self.nifti_directory) + '/dicom'
        Path.mkdir(Path(input_dcm_dir),parents=False, exist_ok=True)
        
        #Create dicom/ct
        input_dcm_ct_dir = input_dcm_dir + '/ct'
        Path.mkdir(Path(input_dcm_ct_dir),parents=False, exist_ok=True)
        MoveDCMFiles(self.InputDir,input_dcm_ct_dir)
        
        #If Structure shift is required, move structure information into dicom/rtstruct
        if self.StructDir:
            input_dcm_struct_dir = input_dcm_dir + '/rtstruct'
            Path.mkdir(Path(input_dcm_struct_dir),parents=False, exist_ok=True)
            MoveDCMFiles(self.StructDir,input_dcm_struct_dir)
        
        #Convert from dicom volumes to nifti volumes. Should auto detect if there is or isn't a struct dir
        process_dicom_directory(input_dcm_dir,output_directory=self.nifti_directory)
        
    def WriteVolumesToFile(self,image_ct_deformed,structShiftFlag=0,deformed_structures = {}):
        """
        Write the deformed ct volume and structures to dicom formats in the directory OutputDir

        Parameters
        ----------
        image_ct_deformed : SimpleITK.Image
            The deformed ct image.
        structShiftFlag : bool or int or whatever, optional
            If true the structures in deformed_structures flag will be written. If 0 then only the image_ct_deformed will be written
        deformed_structures : TYPE, optional
            DESCRIPTION. The default is {}.

        Returns
        -------
        None.

        """
        #Define CT variables
        outputDirCT = Path(self.OutputDir + '/ct')    
        outputDirCT.mkdir(exist_ok=True, parents=True)
        
        input_dcm_dir = str(self.nifti_directory) + '/dicom'
                   
        #write deformed ct to dcm
        convert_nifti_to_dicom_series(
            image=image_ct_deformed,
            reference_dcm=input_dcm_dir + '/ct',
            output_directory=str(outputDirCT)
        )                
               
        if structShiftFlag:
            #Create a temporary directory to write the structures to
            TempDirStruct = Path(self.OutputDir + '/OutputStructures')
            TempDirStruct.mkdir(exist_ok=True, parents=True)
            
            #write structure to nifti format 
            for struct in deformed_structures:
                sitk.WriteImage(deformed_structures[struct],str(TempDirStruct / str(struct + ".nii.gz")))
            
            # rtstruct output dir 
            output_dir_dcm_STRUCT = Path(self.OutputDir + '/rtstruct')  
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