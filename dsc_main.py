import os
import numpy as np
from init_pps_params import *
from enc_main import dsc_encoder
from PIL import Image
from PPS_readnwrite import write_pps, parse_pps
from matplotlib import pyplot as plt
from dsc_enc_buf import DSCBuffer ,write_dsc_data
from init_enc_params import initDefines, initFlatVariables, initDscConstants, initIchVariables, \
    initPredVariables, initRcVariables, initVlcVariables, PicPosition

IMAGE_DEBUG_OPT = False
dsc_path = "w1.dsc"
# full_picture = get_XXXX()
###### Get picture  #######
image_path = "w1.jpeg"
im = Image.open(image_path)
###### Make Y Co Cg #######
if (im.mode) == 'RGB':
    im = im.convert("YCbCr")
elif (im.mode) == 'YCbCr':
    pass
else:
    raise ValueError("Input Image MUST RGB or YCbCr format!!")

##################################################################################
############################ORIGINAL PIXEL DATA###################################
##################################################################################
orig_pixel = np.array(im) # (pic_width, pic_height, num_component) shape ndarray
orig_pixel = orig_pixel.transpose([1, 0, 2])

output_pic = np.zeros(orig_pixel.shape, dtype = np.int32)
##################################################################################

################ configuration constants ################
user_options = {}
user_options['dsc_version_major'] = 1
user_options['dsc_version_minor'] = 2
user_options['pps_identifier'] =  0
user_options['bits_per_component'] = 8 # BEFORE applying 4 bit fraction
user_options['line_buf_depth'] = 0  ## 0 means 16 bit depth
user_options['block_pred_enable'] = 1
user_options['convert_rgb'] = 1 # RGB_INPUT? 1 : 0
user_options['simple_422'] = 0
user_options['native_420'] = 0
user_options['native_422'] = 0
user_options['vbr_enable'] = 0
user_options['bits_per_pixel'] = 8 << 4  # 4-bits Fractional
user_options["pic_width"] = im.width
user_options["pic_height"] = im.height
user_options["slice_width"] = 1920 # 480 default
user_options["slice_height"] = 4 # 108 default

##################################################################################
pps = initPps()
pps.cal_params_enc(user_options)
pic_val = PicPosition()

# defines = initDefines(pps)
# dsc_const = initDscConstants(pps, defines)
# ich_var = initIchVariables(defines)
# pred_var = initPredVariables(defines)
# flat_var = initFlatVariables(defines)
# enc_var = initVlcVariables(defines)
# rc_var = initRcVariables()

slices_per_line = int((pps.pic_width + pps.slice_width - 1) / pps.slice_width)
encoded_buf_size = pps.chunk_size * pps.slice_height
encoded_buf = np.zeros([slices_per_line, encoded_buf_size], dtype = np.int32)
buf = DSCBuffer(pps)

## write Magic Number and PPS datas...
write_pps(dsc_path, pps)

for ys in range(0, pps.pic_height, pps.slice_height):
    #print(ys)

    # One sliced line
    for xs in range(0, pps.pic_width, pps.slice_width):
        print("CURRENT PIC POSITION : [%d] [%d]" %(xs, ys))
        ##### Store current position in this loop for debuging...
        pic_val.set_pos(xs, ys)
        ####### Slicing the picture #######
        slice_picture = orig_pixel[xs : xs + pps.slice_width, ys : ys + pps.slice_height, :]

        if IMAGE_DEBUG_OPT:
            print("xs : [%d %d], ys : [%d %d]" % (xs, xs + pps.slice_width, ys, ys + pps.slice_height))
            print(slice_picture.shape)
            img = Image.fromarray(slice_picture, 'YCbCr')
            img.show()

        dsc_encoder(pps, orig_pixel, output_pic, buf, pic_val)
        buf.slice_index += 1 # Increase Slice index after one slice processed...

    ####### Write encoded dsc data to output file #######
    write_dsc_data(dsc_path, buf, pps)
    buf.buf_reset() # reset buf to use it again lext ys loop
