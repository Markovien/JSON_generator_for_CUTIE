#! /usr/bin/python
# -*- coding: utf-8 -*-

# author: @Markovien
# based on code written by Ha Thi Hien
# description: 
#   - Runs tesseract OCR and
#   - Output json file for CUTIE
# date: 02/13/2021

from PIL import Image
import pytesseract
import numpy as np
import sys, os, cv2, json
from os.path import split, splitext

BASE_PATH = os.getcwd()
INPUT_FOLDER = os.path.join(BASE_PATH, "data/img/")
TMP_FOLDER = os.path.join(BASE_PATH, "data/img_processed/")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "data/json/")

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
        out_path = OUTPUT_FOLDER + image.split(".")[0] + ".json"    

        if i != 1: print()
        print(ORANGE + '~: ' + RESET + 'Process image (' + ORANGE + str(i) + '/' + str(
            len(images)) + RESET + ') : ' + input_path + RESET)

        with Image.open(input_path) as img:
            doc = pytesseract.image_to_data(img, lang='eng', config='--psm 11')#custom_config
            
            doc = readTSV(doc)
            
            new_doc = {}
            new_doc.update({'text_boxes':doc})
    
            classes = ['TOTAL', 'TOTAL_DUE', 'DUE', 'TTC', 'TOTAL_AMOUNT']
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
