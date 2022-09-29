# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 15:15:50 2022

@author: mgar5380
"""
import SimpleITK as sitk
import numpy as np

def CombineDVFs(DVFUnSmoothedImg,DVFSmoothedImg,coordinates_cutoff,RotationPt):
    """
    Combines the smoothed and unsmoothed DVFs. Points above the line between 
    the rotation point and cutoff point are smoothed and points below the line 
    are the unsmoothed DVF
    
    Parameters
    ----------
    DVFUnSmoothedImg : SimpleITK Image
        DESCRIPTION.
    DVFSmoothedImg : SimpleITK Image
        DESCRIPTION.
    coordinates_cutoff : numpy array
        DESCRIPTION.
    RotationPt : numpy array
        DESCRIPTION.

    Returns
    -------
    DVFNew : SimpleITK Image
        DESCRIPTION.

    """
    
    DVFUnSmoothed = sitk.GetArrayFromImage(DVFUnSmoothedImg)
    DVFSmoothed = sitk.GetArrayFromImage(DVFSmoothedImg)
    #ImageCTArray = sitk.GetArrayFromImage(image_ct)
    ImageMask = np.zeros(DVFSmoothed.shape)
    
    m1 = (RotationPt[-1][0] - coordinates_cutoff[0][0])/(RotationPt[-1][1] - coordinates_cutoff[0][1])
    m2 = (RotationPt[-1][0] - coordinates_cutoff[1][0])/(RotationPt[-1][1] - coordinates_cutoff[1][1])
    m3 = (coordinates_cutoff[0][0] - coordinates_cutoff[1][0])/(coordinates_cutoff[0][1] - coordinates_cutoff[1][1])
    
    b1 = coordinates_cutoff[0][0] - m1*coordinates_cutoff[0][1]
    b2 = coordinates_cutoff[1][0] - m2*coordinates_cutoff[1][1]
    b3 = coordinates_cutoff[1][0] - m3*coordinates_cutoff[1][1]    
    
    for i in range(0,ImageMask.shape[0]):
        for j in range(0,ImageMask.shape[1]):
            if i < m1*j + b1 and i < m2*j + b2: #and i > m3*j + b3:
                ImageMask[i,j,:,:] = DVFSmoothed[i,j,:,:]
            else:
                ImageMask[i,j,:,:] = DVFUnSmoothed[i,j,:,:]   

    DVFNew = sitk.GetImageFromArray(ImageMask)    
    DVFNew.CopyInformation(DVFSmoothedImg)
    return DVFNew

def RotateAroundPoint(RTform,RotationPt,RotationOrigin):
    """
    

    Parameters
    ----------
    RTform : TYPE
        DESCRIPTION.
    RotationPt : TYPE
        DESCRIPTION.
    RotationOrigin : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    RotationVector = np.array(RotationPt) - np.array(RotationOrigin)
    NewPts = RTform.apply(RotationVector) + RotationOrigin
    return NewPts.tolist()
    pass

def get_head_mask(body_mask,list_coordinates, reference_image):
    """
    Generates a binary mask of the patient head contour using the given list of coordinates as the cutoff. Assumes x value is the same for all coordinates in the list for interpolation of z-cutoffs. 
    Args:
        body_mask ([SimpleITK.Image]): A binary mask of the patient external contour.
        list_coordinates (list): 2-D list of coordinates to interpolate boundary for head mask
    Returns:
        [SimpleITK.Image]: The binary mask from cropping using input coordinates.
    """    
    
    body_mask_arr = sitk.GetArrayFromImage(body_mask)
    
    #y and z coordinates 
    y_val = []
    z_val = []
    for coordinate in list_coordinates:
        #print(coordinate)
        y_val.append(coordinate[1])
        z_val.append(coordinate[0])
    y_val = np.array(y_val)
    z_val = np.array(z_val)
    #sort so that y is ascending
    sort_index = np.argsort(y_val)
    y_val = y_val[sort_index]
    ycoord = list(range(0,np.shape(body_mask_arr)[1]))
    
    #use linear interp to obtain z-coord
    zinterp = np.interp(ycoord, y_val, z_val)
    
    #round to integer value 
    zinterp = np.around(zinterp).astype(int)
    
    #set values in binary mask to 0 below the head
    for i in ycoord:
        # np.shape(body_mask_arr)[1]-1-i
        body_mask_arr[: zinterp[i], np.shape(body_mask_arr)[1]-1-i, :] = 0 #filtering points up to reference from above to be excluded
    
    body_mask_new = sitk.GetImageFromArray(body_mask_arr)
    body_mask_new.CopyInformation(body_mask)
    
    return body_mask_new