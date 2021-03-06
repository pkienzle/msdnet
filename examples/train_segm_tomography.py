#-----------------------------------------------------------------------
#Copyright 2019 Centrum Wiskunde & Informatica, Amsterdam
#
#Author: Daniel M. Pelt
#Contact: D.M.Pelt@cwi.nl
#Website: http://dmpelt.github.io/msdnet/
#License: MIT
#
#This file is part of MSDNet, a Python implementation of the
#Mixed-Scale Dense Convolutional Neural Network.
#-----------------------------------------------------------------------

"""
Example 07: Train a network for segmentation (tomography)
=========================================================

This script trains a MS-D network for segmentation (i.e. labeling)
Run generatedata.py first to generate required training data.
"""

# Import code
import msdnet
from pathlib import Path

# Define dilations in [1,10] as in paper.
dilations = msdnet.dilations.IncrementDilations(10)

# Create main network object for segmentation, with 100 layers,
# [1,10] dilations, 5 input channels (5 slices), 4 output channels (one for each label), 
# using the GPU (set gpu=False to use CPU)
n = msdnet.network.SegmentationMSDNet(100, dilations, 5, 4, gpu=True)

# Initialize network parameters
n.initialize()

# Define training data
# First, create lists of input files (low quality) and target files (labels)
flsin = sorted((Path('tomo_train') / 'lowqual').glob('*.tiff'))
flstg = sorted((Path('tomo_train') / 'label').glob('*.tiff'))
# Create list of datapoints (i.e. input/target pairs)
dats = []
for i in range(len(flsin)):
    # Create datapoint with file names
    d = msdnet.data.ImageFileDataPoint(str(flsin[i]),str(flstg[i]))
    # Convert datapoint to one-hot, using labels 0, 1, 2, and 3,
    # which are the labels given in each label TIFF file.
    d_oh = msdnet.data.OneHotDataPoint(d, [0,1,2,3])
    # Add datapoint to list
    dats.append(d_oh)
# Note: The above can also be achieved using a utility function for such 'simple' cases:
# dats = msdnet.utils.load_simple_data('tomo_train/lowqual/*.tiff', 'tomo_train/label/*.tiff', augment=False, labels=[0,1,2,3])

# Convert input slices to input slabs (i.e. multiple slices as input)
dats = msdnet.data.convert_to_slabs(dats, 2, flip=True)
# Augment data by rotating and flipping
dats_augm = [msdnet.data.RotateAndFlipDataPoint(d) for d in dats]
    
# Normalize input and output of network to zero mean and unit variance using
# training data images
n.normalizeinout(dats)

# Use image batches of a single image
bprov = msdnet.data.BatchProvider(dats,1)

# Define validation data (not using augmentation)
flsin = sorted((Path('tomo_val') / 'lowqual').glob('*.tiff'))
flstg = sorted((Path('tomo_val') / 'label').glob('*.tiff'))
datsv = []
for i in range(len(flsin)):
    d = msdnet.data.ImageFileDataPoint(str(flsin[i]),str(flstg[i]))
    d_oh = msdnet.data.OneHotDataPoint(d, [0,1,2,3])
    datsv.append(d_oh)
# Note: The above can also be achieved using a utility function for such 'simple' cases:
# datsv = msdnet.utils.load_simple_data('tomo_val/lowqual/*.tiff', 'tomo_val/label/*.tiff', augment=False, labels=[0,1,2,3])

# Convert input slices to input slabs (i.e. multiple slices as input)
datsv = msdnet.data.convert_to_slabs(datsv, 2, flip=False)

# Validate with Mean-Squared Error
val = msdnet.validate.MSEValidation(datsv)

# Use ADAM training algorithms
t = msdnet.train.AdamAlgorithm(n)

# Log error metrics to console
consolelog = msdnet.loggers.ConsoleLogger()
# Log error metrics to file
filelog = msdnet.loggers.FileLogger('log_tomo_segm.txt')
# Log typical, worst, and best images to image files
imagelog = msdnet.loggers.ImageLabelLogger('log_tomo_segm', chan_in=2, onlyifbetter=True)
# Log typical, worst, and best images to image files
# Output probability map for a single channel (in this case, channel 3)
singlechannellog = msdnet.loggers.ImageLogger('log_tomo_segm_singlechannel', chan_in=2, chan_out=3, onlyifbetter=True)

# Train network until program is stopped manually
# Network parameters are saved in segm_params.h5
# Validation is run after every len(datsv) (=256)
# training steps.
msdnet.train.train(n, t, val, bprov, 'tomo_segm_params.h5',loggers=[consolelog,filelog,imagelog,singlechannellog], val_every=len(datsv))
