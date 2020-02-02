# import the necessary packages
import scipy.spatial as sp
import matplotlib.pyplot as plt
import cv2
import numpy as np
import string
import random

#used to natively tranform images to STLs without Selva3D
from stl_tools import numpy2stl

import matplotlib
from matplotlib import colors
matplotlib.rcParams['figure.figsize'] = (6.0, 6.0)

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

#%matplotlib inline

################################ 

def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

# matches a pixel to its closest perceived sibling in a rgbList of pixels
def matchColor(pixel: tuple, rgbList: list):  # returns matching color
    """
    :param pixel: (tuple) RGB tuple
    :param rgbList: (list) list of RBG tuples to match pixel to
    :return: (tuple) color from rgbList that matches closest to pixel
    """
    minDiff = 1000
    pick = []

    # Convert from RGB to Lab Color Space
    pixel_rgb = sRGBColor(pixel[0], pixel[1], pixel[2]);
    pixel_lab = convert_color(pixel_rgb, LabColor);

    for color in rgbList:
        color_rgb = sRGBColor(color[0], color[1], color[2]);
        # Convert from RGB to Lab Color Space
        color_lab = convert_color(color_rgb, LabColor);
        # Find the color difference
        delta_e = delta_e_cie2000(pixel_lab, color_lab);

        # print("The difference between the 2 colors = " , delta_e)
        if delta_e < minDiff:
            minDiff = delta_e
            pick = color

    return pick


# converts rgb img to black and white image where values are either 0 or 255
def rgb2BandW(rgb):
    """
    :param rgb: (numpy array) RGB image as a numpy array
    :return: (numpy array) binary image with three channels
    """
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    gray[gray >= 1] = 255
    rgb[:, :, 0] = gray
    rgb[:, :, 1] = gray
    rgb[:, :, 2] = gray
    return rgb

#################################

# converts image to only use colors in main_colors list
def simplifyImage(imgName, simpleImgName, main_colors, debug=True):
    """
    :param imgName: (string) file path of image to condense to specific colors
    :param simpleImgName: (string) file path to save final image
    :param main_colors: (list) list of RBG tuples of colors to condense image to
    :param debug: set to True for debugging output
    :return: None
    """
    # Stored all RGB values of main colors in a array
    image = cv2.imread(imgName)
    # convert BGR to RGB image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w, bpp = np.shape(image)

    # Change colors of each pixel
    # reference :https://stackoverflow.com/a/48884514/9799700
    for py in range(0, h):
        for px in range(0, w):
            ########################
            # Used this part to find nearest color
            # reference : https://stackoverflow.com/a/22478139/9799700
            input_color = (image[py][px][0], image[py][px][1], image[py][px][2])
            tree = sp.KDTree(main_colors)
            ditsance, result = tree.query(input_color)
            nearest_color = main_colors[result]
            ###################

            image[py][px][0] = nearest_color[0]
            image[py][px][1] = nearest_color[1]
            image[py][px][2] = nearest_color[2]

    # show image
    if debug:
        plt.figure(); plt.axis("off"); plt.title("Simple Image"); plt.imshow(image); plt.show()

    # NOTE: change simpleImg to simpleImg[:,:,::-1] if color channels mixed
    cv2.imwrite(simpleImgName, image)


# creates new B&W image for each color in image
def SpliceColorsToImages(imageName, colorList, uploadPath='', thresh=10, save=True, debug=True, type='stl_tools'):
    """
    :param imageName: (string) file path of image to splice
    :param colorList: (list) list of colors to splice in the image in format [((R,G,B),"Color1"), ((R,G,B),"Color2")]
    :param thresh: (int) threshold for classifying pixels into certain colors. recommended thresh = 10
    :param save: (bool) set to True (Recommended) if you want B&W images of each color saved.
    :param debug: (bool) prints artifacts used for debugging
    :param type: (string) set to 'stl_tools' if you want native STLs as output. 'save' must be True
                          set to 'selva' if you want B&W images saved w/ border for use in Selva3D. 'save' must be True
                          set to '' if you want B&W images saved w/o border for whatever reason. 'save' must be True
    :return: (list) list of file path names of the B&W images created
    """
    baseName = imageName.split(".")[0].split("/")[-1]

    newImageNameList = []
    image = cv2.imread(imageName)

    if debug:
        plt.imshow(image); plt.title("Image to Splice"); plt.show()

    # used to check image percentage retained
    imagemasked = np.ones(image.shape, dtype=np.int8)

    count = 0
    for color in colorList:
        count += 1
        # create NumPy arrays from the boundaries
        lower = np.array([x - thresh if x - thresh >= 0 else x for x in color[0]])
        upper = np.array([y + thresh if y + thresh >= 0 else y for y in color[0]])

        # find the colors within the specified boundaries and apply the mask
        mask = cv2.inRange(image, lower, upper)
        # first mask application
        output = cv2.bitwise_and(image, image, mask=mask)
        # invert mask colors
        output = np.where(output == 0, 255, 0)
        # refine output to values 0 or 255
        output = rgb2BandW(output)

        # median blur to remove salt and pepper noise
        output = cv2.medianBlur(np.float32(output), ksize=5)
        output = np.int64(output)

        # evaluate imagemasked
        imagemasked *= np.int8(output)

        # put border on image, comment lines if using not using Selva3D
        # not needed, function in main.py
        #if type == 'selva':
        #    top, bottom, left, right = [5] * 4
        #    bordercolor = [127, 127, 127]  # grey
        #    output = cv2.copyMakeBorder(output, top, bottom, left, right, cv2.BORDER_CONSTANT, value=bordercolor)

        # show the images
        if debug:
            plt.imshow(output); plt.title(f"{color[1]} Image"); plt.show()

        # save created images
        if save:
            randomCode = randomStringDigits(6)
            substring = imageName.split(".")
            newImageName = f'{uploadPath}/{baseName}({count}of{len(colorList)}_{color[1]}_{randomCode}).{substring[1]}'
            newImageNameList.append(newImageName)

            cv2.imwrite(f'{newImageName}', output)

    if save:
        cv2.imwrite(f"{uploadPath}/Compounded_Images.png", imagemasked)

    unique, counts = np.unique(imagemasked, return_counts=True)
    smoothing_test = dict(zip(unique, counts))

    if sum(smoothing_test.values()) != 0 and len(smoothing_test) >= 2:
        percentCaptured = round((smoothing_test[0] / sum(smoothing_test.values())) * 100, 2)
    else:
        percentCaptured = 0

    if debug:
        print(f"Pixel distribution in smooth mask: {dict(zip(unique, counts))}")
    print(f"Retained {percentCaptured}% of image after smoothing")

    if type == 'stl_tools' and save:
        for stlImgPath in newImageNameList:
            SpliceImagetoSTL(stlImgPath)

    return (newImageNameList, percentCaptured)

#converts images to STLs
def SpliceImagetoSTL(imagePath):
    """
    :param imagePath: image path for each image to be converted to an STL
    :return: None
    """
    print("Creating STLs...")
    print(f"Image: {imagePath}")
    image = cv2.imread(imagePath)
    imageNameHead = imagePath.split(".")[0]
    stlPath = f'{imageNameHead}.stl'
    numpy2stl(image[:,:,0], stlPath, scale=1, solid=True)
    return stlPath

###########################################

if __name__ == "__main__":
    print("Process Started")
    #Please follow STEPS 1-6 to run the program with your RGB image.

    # STEP 1: Write the image path of image you want to use
    imgName = "images/rick_petr.jpg"

    # STEP 2: Write the image path of simplified image. Choose any name w/ a .png extension.
    simpleImgName = "images/simple_rick_petr_smooth.png"

    # STEP 3: Put RGB tuples of colors you want to use. For Black use (5,5,5) not (0,0,0).
    colorRGBList = [(5, 5, 5),        # black
                    (255, 255, 255),  # white
                    (195, 195, 195),  # grey
                    (190, 233, 252),  # blue
                    (89, 240, 30),    # green
                    (128, 128, 128),  # bg
                    (225, 225, 225)   # eyes_arms
                    ]

    # STEP 4: Put the names of colors/identities used for each color in colorRGBList in the same order.
    colorNameList = ["Black", "White", "Grey",
                     "Blue", "Green", "BG",
                     "eyes_arms"
                     ]

    assert len(colorRGBList) == len(colorNameList)
    colorList = [list(a) for a in zip(colorRGBList, colorNameList)]

    print("Simplifying image...")
    # crafts image using only colors from colorRGBList, takes 1 minute
    #simplifyImage(imgName, simpleImgName, colorRGBList, debug=False)

    print("Splicing image...")
    # STEP 5: Change the thresh, save, debug, and type to suit your needs. Check function header for details.
    #         All you really need to do is set the correct type ('stl_tools', 'selva', or '')
    imageNameList = SpliceColorsToImages(simpleImgName, colorList, thresh=10, save=True, debug=False, type='stl_tools')

    print("Process Complete")

    # STEP 6: You can now run the program!
