# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 20:30:21 2021

@author: Andres

https://stackoverflow.com/questions/53248099/keras-image-segmentation-using-grayscale-masks-and-imagedatagenerator-class

"""

import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from tensorflow.keras import Input,layers, models
from tensorflow.keras.layers import Conv2DTranspose,Dropout,Conv2D,BatchNormalization, Activation,MaxPooling2D
from tensorflow.keras import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler

import math
import albumentations as A
import matplotlib.pyplot as plt

#%%

#input_dir = "C:/Users/Andres/Desktop/imexhs/Lung/Prueba/CT/"
#mask_dir = "C:/Users/Andres/Desktop/imexhs/Lung/Prueba/mask/"

input_dir = 'C:/Users/Andres/Desktop/CTClassif/train/'
mask_dir = 'C:/Users/Andres/Desktop/CTClassif/mask/'


#%%
#image_datagen = ImageDataGenerator(rotation_range=90,)
#mask_datagen = ImageDataGenerator(rotation_range=90,)
image_datagen = ImageDataGenerator(rescale=1./255)
mask_datagen = ImageDataGenerator(rescale=1./255)

target_size=(512//16, 512//16)

image_generator = image_datagen.flow_from_directory(
    input_dir,
    class_mode=None, target_size=target_size,
    seed=1)

mask_generator = mask_datagen.flow_from_directory(
    mask_dir,
    class_mode=None, target_size=target_size,
    seed=1)

steps = image_generator.n//image_generator.batch_size
steps_validation = mask_generator.n//mask_generator.batch_size


train_generator = zip(image_generator, mask_generator)
validation_generator = zip(image_generator, mask_generator)



# combine generators into one which yields image and masks


#%%

for _ in range(5):
    img = image_generator.next()
    mask = mask_generator.next()
    
    print(img.shape)
    plt.figure(1)
    plt.subplot(1,2,1)
    plt.axis('off')
    plt.imshow(img[0])
    plt.subplot(1,2,2)
    plt.imshow(mask[0])
    plt.axis('off')
    plt.show()



#%%

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


def Unet(img_height, img_width, nclasses=2, filters=64):
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
    conv5 = Dropout(0.5)(conv5)
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

#%%

model = Unet(512//16, 512//16, nclasses=1, filters=8)

model.summary()

#%%

#lr = 1e-3
es = EarlyStopping(patience=100,mode='min', verbose=1)
checkpoint_path ='C:/Users/Andres/Desktop/imexhs/Lung/' + 'exp.h5'

mc = ModelCheckpoint(checkpoint_path, monitor='val_loss', verbose=1 , save_best_only=True, mode='min')


#%%
model.compile(optimizer='adam',
              loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
              metrics=['accuracy'])


#model.fit_generator(train_generator,steps_per_epoch=steps,epochs=5)

#%%
##Este sirve
# history = model.fit(train_generator,
#                     steps_per_epoch=steps,
#                     epochs=5,
#                     verbose=1,
#                     #
#                     callbacks=[es,mc])

#%%
history = model.fit(train_generator,
                    steps_per_epoch=steps,
                    validation_data=validation_generator,
                    validation_steps=steps_validation,
                    epochs=5,
                    verbose=1,
                    #
                    callbacks=[es,mc])





