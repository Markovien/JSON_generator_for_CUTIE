#! /usr/bin/python
# -*- coding: utf-8 -*-

# author: @Markovien
# based on code written by Ha Thi Hien
# description: 
#   - Processes receipts,
#   - Runs tesseract OCR and
#   - Output json file for CUTIE
# date: 02/13/2020

from PIL import Image
import pytesseract
import numpy as np
import sys, os, cv2, json
from os.path import split, splitext

BASE_PATH = os.getcwd()
INPUT_FOLDER = os.path.join(BASE_PATH, "data/img/") #folder where are stored images
TMP_FOLDER = os.path.join(BASE_PATH, "data/img_processed/") #folder where to store processed images
OUTPUT_FOLDER = os.path.join(BASE_PATH, "data/json/") #folder where to store json files

#these are for coloring printing texts
ORANGE = '\033[33m'
RESET = '\033[0m'

def readTSV(data):
    rows = data.split('\n')
    nlen = len(rows)
    if nlen == 0:
        return
    doc = []
    # get columns
    c = dict() # column
    #level	page_num	block_num	par_num	line_num	word_num	left	top	width	height	conf	text
    header = rows[0].split('\t')    

    npage = None # page#
    nbl = None
    nline = None
    for i in range(1, nlen):
        r = rows[i].split('\t')
        word = dict()
        word['id'] = i
        if (len(r)>=9):        
            word['bbox'] = tuple([int(r[6]), int(r[7]), int(r[6])+ int(r[8]), int(r[7])+ int(r[9])])
        if len(r) < 12:
            #sys.stderr.write('not full fields')            
            word['text'] = ""
        else:
            word['text'] = r[11]
        if word['text']:            
            doc.append(word)
    return doc

def prepare_folders():
    """
    :return: void
        Creates necessary folders
    """

    for folder in [
        INPUT_FOLDER, TMP_FOLDER, OUTPUT_FOLDER
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def find_images(folder):
    """
    :param folder: str
        Path to folder to search
    :return: generator of str
        List of images in folder
    """

    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        if os.path.isfile(full_path):
            try:
                _ = Image.open(full_path)  # if constructor succeeds
                yield file
            except:
                pass


def process_receipt(filename):
    input_path = INPUT_FOLDER + filename
    output_path = OUTPUT_FOLDER + filename.split(".")[0] + "_processed.json"

    print(ORANGE + '~: ' + RESET + 'Process image: ' + ORANGE + input_path + RESET)
    prepare_folders()

    try:
        #cv2.imshow(input_path)
        img = cv2.imread(input_path,0)
        ret,thresh1 = cv2.threshold(img, 95, 255, cv2.THRESH_BINARY)
        #img = process_image(input_path)
        tmp_path = os.path.join(TMP_FOLDER, filename)

        print(ORANGE + '~: ' + RESET + 'Temporary store image at: ' + ORANGE + tmp_path + RESET)

        cv2.imwrite(tmp_path, thresh1)

        print(ORANGE + '~: ' + RESET + 'Store parsed text at: ' + ORANGE + output_path + RESET)
        #raw = open(output_path, 'r').readlines()

        return tmp_path
    
    except FileNotFoundError:
        return "Error while loading file"


def main():
    
    prepare_folders()
    dir_path = os.getcwd()

    images = list(find_images(INPUT_FOLDER))
    print(ORANGE + '~: ' + RESET + 'Found: ' + ORANGE + str(len(images)),
          RESET + ' images in: ' + ORANGE + INPUT_FOLDER + RESET)

    i = 1
    for image in images:
        input_path = os.path.join(INPUT_FOLDER, image)
        tmp_path = os.path.join(TMP_FOLDER, image)
        out_path = OUTPUT_FOLDER + image.split(".")[0] + "_processed.json"
        #out_path = os.path.join(OUTPUT_FOLDER, image + ".json")    

        if i != 1: print()
        print(ORANGE + '~: ' + RESET + 'Process image (' + ORANGE + str(i) + '/' + str(
            len(images)) + RESET + ') : ' + input_path + RESET)

        file_to_data = process_receipt(image)
        with Image.open(file_to_data) as img:
            # width, height = img.size
            doc = pytesseract.image_to_data(img, lang='eng', config='--psm 11')#custom_config
            
            doc = readTSV(doc)
            
            new_doc = {}
            new_doc.update({'text_boxes':doc})
    
            classes = ['O', 'DATE_SALE', 'ADDRESS_SELLER', 'DOC_NR', 'DATE_CREATION', 'ADDRESS_CONTRACTOR', 'VAT_ID_CONTRACTOR', 'PAYMENT_METHOD', 'VAT_ID_SELLER', 'PAYMENT_BANK_NR', 'TOTAL_PAY', 'TOTAL_CURRENCY', 'TOTAL_TAX', 'TOTAL_WITH_TAX', 'TOTAL_WITHOUT_TAX', 'DATE_PAYMENT', 'NAME_SELLER', 'NAME_CONTRACTOR']
            fields = []
            for cl in classes:
                new_field = {"field_name": cl, "value_id": [], "value_text":[], "key_id":[], "key_text":[]}
                fields.append(new_field)
            new_doc.update({'fileds': fields})
    
            new_doc.update({"global_attributes":{"file_id": image}})        
            
            json_obj = json.dumps(new_doc, indent = 4, ensure_ascii=False)
    
            out = open(out_path, "wb")
            out.write(json_obj.encode(encoding='UTF-8'))
            out.close()
        i = i + 1

if __name__ == "__main__":
    main()
