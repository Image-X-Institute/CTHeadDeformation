# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 15:26:22 2022

@author: mgar5380
"""
#External Modules
import os
import re
import SimpleITK as sitk
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation

#Platipy Modules
#from platipy.imaging.registration.registration import apply_field
from platipy.imaging.generation.dvf import generate_field_shift
from platipy.imaging.registration.utils import apply_transform
from platipy.imaging.generation.mask import get_bone_mask
from platipy.imaging.generation.mask import get_external_mask

#Internal Modules
from DeformHeadCT.utils import get_head_mask

"""
TODO
Add option for gaussian smoothing
"""

class HeadDeformation():
    
    def __init__(self,nifti_directory,patientunderscore,structShiftFlag = 0):
        """
        Initialise class

        Parameters
        ----------
        nifti_directory : Path
            Path to temporary directory.
        patientunderscore : str
            patient identifier.
        structShiftFlag : bool, optional
            If 1 (Or True or whatever) the structures will be shifted. The default is 0.

        Returns
        -------
        None.

        """
        #Define nifti volumes to work with     
        ct_path = next(iter(nifti_directory.glob(f"{patientunderscore}/IMAGES/*CT*.nii.gz")))
        
        # Read in image    
        self.image_ct = sitk.ReadImage(str(ct_path))
        
        if structShiftFlag:
            self.structure_paths = list(nifti_directory.glob(f"{patientunderscore}/STRUCTURES/*.nii.gz"))
        else:
            self.structure_paths = list('')
    
        #Define dvf_field
        self.dvf_field = sitk.Image(self.image_ct.GetSize(), sitk.sitkVectorFloat64);
        sitk.Image.CopyInformation(self.dvf_field,self.image_ct)    
    
    def ApplyHeadRotation(self,coordinates_cutoff,angles,axes,point_of_rotation):
        """
        Generates a deformation to rotate the head, which is stored in dvf_field

        Parameters
        ----------
        coordinates_cutoff: array
            2x3 array annotating the co-ordinates that seperate the head and the shoulders. See the wiki for more information.
        angles : (float | arr)
            angles of rotation. If empty no head rotation will be done. 
        axes : array
            nx3 array where the nth element is the axis around which the volume will rotate. See wiki for more info.
        point_of_rotation : array
            nx3 array where each nth element is the centre voxel around which the head rotations will occur. .

        Returns
        -------
        Return 0 if no error, returns -1 if there is a problem with the input variables

        """
        if not angles:
            print('"angles" variable cannot be empty')
            return -1
        
        #Get Masks
        # Automatically generate external mask
        struct_external = get_external_mask(self.image_ct)
        
        #generate head mask using list of coordinates as cutoff points
        head_mask = get_head_mask(struct_external,coordinates_cutoff, self.image_ct)            
        
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
        
        #Define variables. Do they get used? Who knows. But they are living their best life.   
        Mask_deformed = [];
        dvf_transform = [];
        
        for i in range(0,LoopNum):
            if LoopNum > 1:
                axisLoop = axes[i]
                RotationPt = point_of_rotation[i]
            else:
                axisLoop = axes
                RotationPt = point_of_rotation[0]
                
            print(LoopNum)
            print(RotationPt)
                
            Mask_deformed_loop, dvf_transform_loop, dvf_field_loop, RotationTForm = generate_field_rotation(
                self.image_ct,
                head_mask,
                tuple(RotationPt),
                axis_of_rotation=axisLoop,
                angle=angles[i]*np.pi/180,
                gaussian_smooth=0
                #mask_bend_from_reference_point = coordinates_cutoff
            )
            Mask_deformed.append(Mask_deformed_loop)
            dvf_transform.append(dvf_transform_loop)
            self.dvf_field = self.dvf_field + dvf_field_loop   
    
        return 0
    
    def ApplyGTVShift(self,Structure_Shift,Structure_Names):
        """
        Rigidly Shift the structures defined by Structure_Names by the amount described in Structure_Shift

        Parameters
        ----------
        Structure_Shift : array
            1x3 array describing the magnitude of the rigid displacement of the structures in "Structure_Names".
        Structure_Names : (str | array),
            The structures to be shifted.

        Returns
        -------
        None.

        """
        structures = {re.findall(".*_RTSTRUCT_(.*).nii.gz", p.name)[0]: sitk.ReadImage(str(p)) for p in self.structure_paths}
        
        if np.size(Structure_Shift[0]) > 1:
            for i in range(0,len(Structure_Shift)):
                
                if Structure_Names[i] not in structures:
                    print('No Structure {}'.format(Structure_Names[i]))
                else:
                
                    Mask_shift, dvf_shift, dvf_field_shift = generate_field_shift(
                        mask_image = structures[Structure_Names[i]],
                        vector_shift = tuple(Structure_Shift[i]),
                        gaussian_smooth = 2
                    )
                    #dvf_transform.append(dvf_shift)
                    
                    dvfLoop = sitk.Cast(dvf_field_shift, sitk.sitkVectorFloat32)  
                    dvfLoop.CopyInformation(self.dvf_field)                           
                    
                    try:
                        self.dvf_field = self.dvf_field + dvf_field_shift
                    except:
                        self.dvf_field = self.dvf_field + sitk.Cast(dvfLoop,sitk.sitkVectorFloat64) 
                    #dvf_transform.append(dvf_shift)
                    #Mask_deformed.append(Mask_shift)
        else:
            if Structure_Names not in structures:
                print('No Structure {}'.format(Structure_Names))
            else:
                Mask_shift, dvf_shift, dvf_field_shift = generate_field_shift(
                    mask_image = structures[Structure_Names],
                    vector_shift = tuple(Structure_Shift),
                    gaussian_smooth = 2
                )                
                #dvf_transform.append(dvf_shift)
                #Mask_deformed.append(Mask_shift)
                
                dvfLoop = sitk.Cast(dvf_field_shift, sitk.sitkVectorFloat32)  
                dvfLoop.CopyInformation(self.dvf_field)     
            
                try:
                    self.dvf_field = self.dvf_field + dvf_field_shift
                except:
                    self.dvf_field = self.dvf_field + sitk.Cast(dvfLoop,sitk.sitkVectorFloat64) 




def generate_field_rotation(
    reference_image,
    body_mask,
    reference_point,
    axis_of_rotation=[0, 0, -1],
    angle=0.1,
    mask_bend_from_reference_point=("z", "inf"),
    gaussian_smooth=5,
):
    """
    Generates a synthetic field characterised by specified rotation
    Typically, this field would be used to simulate a moving head and so masking is important.
    Args:
        reference_image ([SimpleITK.Image]): The image to be deformed.
        body_mask ([SimpleITK.Image]): A binary mask in which the deformation field will be defined
        reference_point ([tuple]): The point (z,y,x) about which the rotation field is defined.
        axis_of_rotation (tuple, optional): The axis of rotation (z,y,x). Defaults to [0, 0, -1].
        angle (double, optional): The deformation vector length at each point will equal scale multiplied by the distance to that point from reference_point. Defaults to 1.
        mask_bend_from_reference_point (tuple, optional): The dimension (z=axial, y=coronal, x=sagittal) and limit (inf/sup, post/ant, left/right) for masking the vector field, relative to the reference point. Defaults to ("z", "inf").
        gaussian_smooth (int | list, optional): Scale of a Gaussian kernel used to smooth the deformation vector field. Defaults to 5.
    Returns:
        [SimpleITK.Image]: The binary mask following the expansion.
        [SimpleITK.DisplacementFieldTransform]: The transform representing the expansion.
        [SimpleITK.Image]: The displacement vector field representing the expansion.
    """
    body_mask_arr = sitk.GetArrayFromImage(body_mask)

    pt_arr = np.array(np.where(body_mask_arr))
    vector_ref_to_pt = pt_arr - np.array(reference_point)[:, None]
    
    vector_ref_to_pt=vector_ref_to_pt[::-1].T;
    axis_of_rotation = np.array(axis_of_rotation[::-1])
    axis_of_rotation = axis_of_rotation / np.linalg.norm(axis_of_rotation)
    
    # initialise scipy rotation instance
    rotation = Rotation.from_rotvec(-1*angle * axis_of_rotation)
    #ector_ref_to_pt = np.ndarray.transpose(vector_ref_to_pt)
    rotated_vector_ref_to_pt = rotation.apply(vector_ref_to_pt)
    deformation_vectors = rotated_vector_ref_to_pt - vector_ref_to_pt;


    dvf_template = sitk.Image(reference_image.GetSize(), sitk.sitkVectorFloat64, 3)
    dvf_template_arr = sitk.GetArrayFromImage(dvf_template)
    
    dvf_template_arr[np.where(body_mask_arr)] = deformation_vectors;
#     if scale is not False:
#         dvf_template_arr[np.where(body_mask_arr)] = deformation_vectors * scale

    dvf_template = sitk.GetImageFromArray(dvf_template_arr)
    dvf_template.CopyInformation(reference_image)

    # smooth
    if np.any(gaussian_smooth):

        if not hasattr(gaussian_smooth, "__iter__"):
            gaussian_smooth = (gaussian_smooth,) * 3

        dvf_template = sitk.SmoothingRecursiveGaussian(dvf_template, gaussian_smooth)

    dvf_tfm = sitk.DisplacementFieldTransform(
        sitk.Cast(dvf_template, sitk.sitkVectorFloat64)
    )

    reference_image_bend = apply_transform(
        reference_image,
        transform=dvf_tfm,
        default_value=int(sitk.GetArrayViewFromImage(reference_image).min()),
        interpolator=2,
    )
    return reference_image_bend, dvf_tfm, dvf_template, rotation

def PrepareRegistration(image_ct,image_ct_deformed,TempDir,paramFilePath):
    """
    Prepare the files and do the rigid/non-rigid registration with files stored in a temp directory

    Parameters
    ----------
    image_ct : SimpleITK.Image
        Original undeformed ct image.
    image_ct_deformed : SimpleITK.Image
        Deformed ct image.
    TempDir : Path
        Path where the temporarily files will be stored.
    paramFilePath : str
        FileName of the registration parameter.

    Returns
    -------
    dvf_New : SimpleITK.Image
        DVF output of the registration.

    """
    
    #Prepare data for rigid/non-rigid registration
    #Normalise and write initial and deformed CT vols
    image_ct_norm = sitk.Normalize(image_ct)
    sitk.WriteImage(image_ct_norm,str(TempDir) + '/CTNorm.nii.gz')
    
    image_ct_deformed_norm = sitk.Normalize(image_ct_deformed)
    sitk.WriteImage(image_ct_deformed_norm,str(TempDir) + '/CTWarpedNorm.nii.gz')
    
    #Create Bone Masks
    BoneMaskInit = get_bone_mask(image_ct)
    BoneMaskWarped = get_bone_mask(image_ct_deformed)
    BoneMaskInitNorm = sitk.Normalize(BoneMaskInit)
    BoneMaskWarpedNorm = sitk.Normalize(BoneMaskWarped)
    sitk.WriteImage(BoneMaskInitNorm,str(TempDir) + '/BoneMaskInit.nii.gz')
    sitk.WriteImage(BoneMaskWarpedNorm,str(TempDir) + '/BoneMaskWarped.nii.gz')
    
    #Do registration
    FixedImage = str(TempDir) +  '/CTWarpedNorm.nii.gz'
    MovingImage = str(TempDir) +  '/CTNorm.nii.gz'
    #parameterFilePath = intermediate_dir + '/Elastix_BSpline_OpenCL_RigidPenalty.txt'

    outputPath = str(TempDir)    

    ParamFileFinal = ModifyElastixParameterFile(paramFilePath,TempDir)
    
    os.system('elastix -f "{}" -m "{}" -p "{}" -out "{}"'.format(FixedImage,MovingImage,ParamFileFinal,outputPath))
    
    ParamFile = outputPath + '/TransformParameters.0.txt'
    
    os.system('transformix -def all -tp "{}" -out "{}"'.format(ParamFile, outputPath))

    dvf_New = sitk.ReadImage(outputPath + '/deformationField.mha')    
    
    return dvf_New

def ModifyElastixParameterFile(paramFilePath,TempDir):
    """
    Modify the elastix parameter file so include the recently create bone mask file

    Parameters
    ----------
    paramFilePath : str
        Name of the input elastix parameter file.
    TempDir : Path
        Path where the temporarily files will be stored.

    Returns
    -------
    paramFileOutput: str
        File name of the parameter file to be used for the registration with the correct (hopefully) bonemask file

    """
    
    with open(paramFilePath) as f:
        lines = f.readlines()
    
    for i,line in enumerate(lines):
        if 'MovingRigidityImageName' in line:
            line = '(MovingRigidityImageName "' + str(TempDir) + '/BoneMaskInit.nii.gz' +'")'
            lines[i] = line
            
    paramFileOutput = str(TempDir) + '/ModifiedElastixParameter.txt'
    
    with open(paramFileOutput, 'w') as f:
        for line in lines:
            f.write(line)
            #f.write('\n') 
    
    return paramFileOutput