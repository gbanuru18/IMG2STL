import os
import urllib.request
from flask import Flask, flash, request, redirect, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import random
import string
import cv2
import shutil
from collections import defaultdict
from image_splicer import SpliceColorsToImages, SpliceImagetoSTL

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG'] 

UPLOAD_FOLDER = 'static/uploads'
MODIFIED_FOLDER = 'static/modified'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def emptyFolder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/action', methods=['POST'])
def upload_file():
    global imgFile
    emptyFolder(UPLOAD_FOLDER)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        #print("RQ", request.files)
        file = request.files['file']

        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imgFile = filename

            return extract_info(filename)
        else:
            flash('Allowed file types are png, jpg, jpeg')
            return render_template('upload.html')


@app.route('/action2', methods=['POST'])
def getSplitImages():
    emptyFolder(MODIFIED_FOLDER)
    if request.method == 'POST':
        threshold = int(request.form["thresh"])
        print(threshold)
        print(request.form)
        colorList = parseColors(request.form)

        colorDict = defaultdict(str)

        for color in colorList:
            colorDict[color[1]] = str(color[0]).strip('(').strip(')').replace(" ", "")

        print("colorList: ", colorList)
        print("colorDict: ", colorDict)

        # WORK MUST BE DONE HERE
        imagePath = getImgPath()
        imageDimensions = getImgDimensions(imagePath)

        print('imagepath', imagePath)
        outputPathList, percentCaptured = startMainProcess(imagePath, colorList, threshold=threshold)
        print("outputPathList", outputPathList)

        return render_template('splice.html', length=len(outputPathList), spliceList=outputPathList,
                               percent=percentCaptured, colorMap = colorDict, sliderVal=threshold,
                               upload=UPLOAD_FOLDER, filename=imagePath, fileDim=imageDimensions)

@app.route('/action3', methods=['POST'])
def getSplitImage():
    print("action3")
    print(request.form)
    finalImgPath = None
    for imagePath in request.form:
        print(imagePath)
        finalImgPath = addGreyBorderToImage(imagePath, updateFilenameTail(imagePath, "border"))
        print(f"F: {finalImgPath}")
    try:
        return send_file(f'{finalImgPath}', attachment_filename='pic.jpg', as_attachment=True)
    except Exception as e:
        return str(e)

@app.route('/action4', methods=['POST'])
def getSTL():
    for imgPath in request.form:
        print(imgPath)
        stlPath = SpliceImagetoSTL(imgPath)
    try:
        return send_file(f'{stlPath}', attachment_filename='pic.stl', as_attachment=True)
    except Exception as e:
        return str(e)

def getImgDimensions(imagePath):
    image = cv2.imread(imagePath)
    height, width, _ = image.shape
    print("IMAGE SHAPE", image.shape)
    return (height, width)


def addGreyBorderToImage(imagePath, newImagePath):
    output = cv2.imread(imagePath)
    top, bottom, left, right = [5] * 4
    bordercolor = [127, 127, 127]  # grey
    output = cv2.copyMakeBorder(output, top, bottom, left, right, cv2.BORDER_CONSTANT, value=bordercolor)

    cv2.imwrite(newImagePath, output)
    return newImagePath

def updateFilenameTail(imagePath, name):
    imagePathHead = imagePath.split(".")[0]
    imagePathTail = imagePath.split(".")[-1]
    finalImgPath = f"{imagePathHead}_{name}.{imagePathTail}"
    return finalImgPath

def startMainProcess(imagePath, colorList, threshold=50, uploadPath=MODIFIED_FOLDER):
    imagePath, percentCaptured = SpliceColorsToImages(imagePath, colorList, uploadPath, thresh=int(threshold), save=True, debug=False, type='selva')
    return (imagePath, percentCaptured)

def parseColors(colordict):
    colorRGBList = []
    colorNameList = []

    for color in colordict:
        print(f"{str(color)}: {colordict[color]}")
        if allowedRGB(colordict[color]):
            colorRGBList.append(cleanRGB(colordict[color]))
            colorNameList.append(str(color))

    #print("Good Colors", colorRGBList)
    #print("Good Names", colorNameList)

    colorList = [list(a) for a in zip(colorRGBList, colorNameList)]
    print(f"Color List: {colorList}")

    return colorList

def cleanRGB(string):
    R, G, B = string.split(",")
    return tuple([int(R), int(G), int(B)])

def allowedRGB(string):
    items = string.split(",")
    if len(items) != 3:
        return False

    for item in items:
        if not item.isdigit() or not int(item) >= 0 or not int(item) <= 255:
            return False

    return True

def downloadFromdb(userid, filename):
    data = f"Hi {userid} {filename}"
    return data


def upload2db(logdata):
    # userid = randomStringDigits()
    userid = 111111
    print("Try to Insert")
    db.logs.insert_one({'id': userid, 'log': logdata})
    print("Inserted into DB")

    return userid


def run_aws(filename):
    data = f"AWS {filename}"

    # place dynamic analysis here

    with open("output.txt", "r") as file:
        data = file.read()  # .replace('\n','<br>')
    return data

def putImgPath(filename, folder):
    with open("output.txt", "w") as file:
        file.write(f"{folder}/{filename}")  # .replace('\n','<br>')
        file.close()

def getImgPath():
    with open("output.txt", "r") as file:
        data = file.read()  # .replace('\n','<br>')
        file.close()
    return data

def extract_info(filename):
    colorDict = defaultdict(str)
    data = filename
    try:
        putImgPath(filename, UPLOAD_FOLDER)
        imagePath = getImgPath()
        imageDimensions = getImgDimensions(imagePath)

    except Exception as e:
        data = f"Error Occured: {e}"
        return render_template("results.html", data=data, filename=imagePath, colorMap=colorDict, sliderVal=10, fileDim=imageDimensions)

    return render_template("results.html", data=data, filename=imagePath, colorMap=colorDict, sliderVal=10, fileDim=imageDimensions)

@app.route('/colorCanvas')
def colorCanvas():
    return render_template('colorCanvas.html', upload=UPLOAD_FOLDER, filename=getImgPath(), fileDim=getImgDimensions(getImgPath()))

@app.route("/results")
def results():
    return render_template("results.html")


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/home')
def home():
    return render_template('upload.html')



if __name__ == "__main__":
    app.run()
