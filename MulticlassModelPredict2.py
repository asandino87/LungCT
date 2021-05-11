# -*- coding: utf-8 -*-
"""
@author: Andres Sandino

https://stackoverflow.com/questions/53248099/keras-image-segmentation-using-grayscale-masks-and-imagedatagenerator-class

"""

import tensorflow as tf
import tensorflow.keras as keras

from tensorflow.keras import Input,layers, models
from tensorflow.keras.layers import Conv2DTranspose,Dropout,Conv2D,BatchNormalization, Activation,MaxPooling2D
from tensorflow.keras import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler

import math
import albumentations as A
import matplotlib.pyplot as plt
import numpy as np
import os
import cv2

import timeit as timeit
from timeit import timeit

    
#%% Model

scale = 4
filters= 32
nclasses= 3
    
def conv_block(tensor, nfilters, size=3, padding='same', initializer="he_normal"):
    x = Conv2D(filters=nfilters, kernel_size=(size, size), padding=padding, kernel_initializer=initializer)(tensor)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)
    x = Conv2D(filters=nfilters, kernel_size=(size, size), padding=padding, kernel_initializer=initializer)(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)
    return x


def deconv_block(tensor, residual, nfilters, size=3, padding='same', strides=(2, 2)):
    y = Conv2DTranspose(nfilters, kernel_size=(size, size), strides=strides, padding=padding)(tensor)
    y = tf.concat([y, residual], axis=3)
    y = conv_block(y, nfilters)
    return y


def Unet(img_height, img_width, nclasses, filters):
# down
    input_layer = Input(shape=(img_height, img_width, 3), name='image_input')
    conv1 = conv_block(input_layer, nfilters=filters)
    conv1_out = MaxPooling2D(pool_size=(2, 2))(conv1)
    conv2 = conv_block(conv1_out, nfilters=filters*2)
    conv2_out = MaxPooling2D(pool_size=(2, 2))(conv2)
    conv3 = conv_block(conv2_out, nfilters=filters*4)
    conv3_out = MaxPooling2D(pool_size=(2, 2))(conv3)
    conv4 = conv_block(conv3_out, nfilters=filters*8)
    conv4_out = MaxPooling2D(pool_size=(2, 2))(conv4)
    conv4_out = Dropout(0.5)(conv4_out)
    conv5 = conv_block(conv4_out, nfilters=filters*16)
    conv5 = Dropout(0.5,name='BOTTLENECK')(conv5)
# up
    deconv6 = deconv_block(conv5, residual=conv4, nfilters=filters*8)
    deconv6 = Dropout(0.5)(deconv6)
    deconv7 = deconv_block(deconv6, residual=conv3, nfilters=filters*4)
    deconv7 = Dropout(0.5)(deconv7) 
    deconv8 = deconv_block(deconv7, residual=conv2, nfilters=filters*2)
    deconv9 = deconv_block(deconv8, residual=conv1, nfilters=filters)
# output
    output_layer = Conv2D(filters=1, kernel_size=(1, 1))(deconv9)
    output_layer = BatchNormalization()(output_layer)
    output_layer = Activation('sigmoid')(output_layer)

    model = Model(inputs=input_layer, outputs=output_layer, name='Unet')
    return model



model = Unet(512//scale, 512//scale, nclasses, filters)

model.summary()

#%%

# Loading model weights

model.load_weights('C:/Users/Andres/Desktop/CTClassif/ExpLungInf1_cropped.h5')


#%%

def imoverlay(img,predimg,coloredge):
    
    
    #predictedrgb=np.zeros((512,512,3))
    
    # Upsample image to 512x512
    predmask = cv2.resize(predimg,(512,512), interpolation = cv2.INTER_AREA)
    predmask = predmask*255
    
    # Upsample image to 512x512    
    img = cv2.resize(img,(512,512), interpolation = cv2.INTER_AREA)
    
    overlayimg = img.copy()
    overlayimg[predmask == 255] = coloredge
    
    return overlayimg

#%% Visualizacion de resultados (No es necesario correr esta sección)


path = 'C:/Users/Andres/Desktop/CovidImages/Testing/CT2/CT/'
pathmask = 'C:/Users/Andres/Desktop/CovidImages/Testing/Mask/Mask/'


#destpath = 'C:/Users/Andres/Desktop/CovidImages/Testing/CT2/CT/'
listfiles = os.listdir(path)
listfilesmask = os.listdir(pathmask)

#%%

#start_time = time()
colormat=np.zeros([512,512])

#colormask=np.zeros([512,512,3])
#grtrcolormask=np.zeros([512,512,3])

grtr_mask=[] #Groundtruth mask
classes = 4

for i in range(39,40):
    
    # List of files
    im_name = listfiles[i]
    im_namemask = listfilesmask[i]
    
    # Graylevel image (array)
    im_or=cv2.imread(path+im_name)
    im_array=im_or
    
    # Read ground truth Mask image (array)
    grtr_mask=cv2.imread(pathmask+im_namemask)
    
    # Convert RGB mask to Grayscale
    grtr_mask=grtr_mask[:,:,0] 
    
    # Un-normalizing mask [Classes=0,1,2,3]
    grtr_mask=np.round(grtr_mask/255*classes)
    
    scale = 4
    input_img_mdl = getprepareimg(im_array,scale)
    
    # Generate image prediction
    pred_mask = model.predict(input_img_mdl)
    
    # Image mask as (NxMx1) array
    pred_mask = pred_mask[0,:,:,0]

    pred_maskmulti=np.round(pred_mask*classes)
    pred_maskmulti=pred_maskmulti-1 #Classes: 0,1,2,3

    # Resize predicted mask
    pred_mask = cv2.resize(pred_maskmulti,(512,512), 
                          interpolation = cv2.INTER_AREA)
    
    # Convert gray mask to color mask    
    predcolormask = getcolormask(pred_mask)
    grtrcolormask = getcolormask(grtr_mask)

    

    
    plt.figure()
    plt.subplot(1,3,1)
    plt.imshow(im_array,cmap='gray')
    plt.axis('off')
    plt.title('Gray Level')
    
    plt.subplot(1,3,2)
    plt.imshow(grtrcolormask,cmap='gray')
    plt.axis('off')  
    plt.title('Groundtruth')
    
    
    plt.subplot(1,3,3)    
    plt.imshow(predcolormask,cmap='gray')
    plt.axis('off')
    plt.title('Predicted')
    plt.show()

    
    # plt.imshow(pred)
    # plt.title('Predicted mask')
    # plt.axis('off')     
    # plt.show()
    # plt.close()

#displayresults()

#elapsed_time = time() - start_time



#%%


def getprepareimg(im_array,scale):
    
    # Resize image (Input array to segmentation model)
    im_array=cv2.resize(im_array,(512//scale,512//scale), 
                        interpolation = cv2.INTER_AREA)
    
    # Image gray level normalization
    im_array=im_array/np.max(im_array)
    
    # Adding one dimension to array
    im_array_out = np.expand_dims(im_array,axis=[0])
    
    return im_array_out

def getcolormask(graymask):
    
    [w,l] = np.shape(graymask)
    colormask = np.zeros([w,l,3])
    
    colormask[graymask==0]=[0,0,0]
    colormask[graymask==1]=[255,0,0]
    colormask[graymask==2]=[0,255,0]
    colormask[graymask==3]=[0,0,255]
    
    colormask=np.int16(colormask)
    
    
    return colormask
    


#%%


#for i in range(len(listfiles)):ç
timeit()
from time import time
start_time = time()

for i in range(10000):
    print(i)
    
    

# Take the original function's return value.

# Calculate the elapsed time.
elapsed_time = time() - start_time 