#!/usr/bin/env python

'''
Created on 22/01/2014

@author: malcalde
'''

import sys
import re
import csv
import os
import traceback

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
#from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage

knowledge = None
academy = None
belt = None
gender = None
category = None
weight = None
total = None
hkey = None

progress = ""

def cleanup():
    global knowledge, academy, belt, gender, category, weight, total, hkey, progress
 
    knowledge = dict()
    academy = dict()
    belt = dict()
    gender = dict()
    category = dict()
    weight = dict()

    total = 0
    hkey = ''

    progress = ''

def whoAmI():
    stack = traceback.extract_stack()
    filename, codeline, funcName, text = stack[-2]
    return funcName

def printProgressBar(page, pages, title=''):
    progress =  "[" + (page * "#") + ((pages - page) * " ") + "]" + " - Processing '" + title + "' page: " + str(page + 1)  
    print progress

def parseLTObjects(LTObjects, pageNo, lines=[]):
    
    for LTObject in LTObjects:
        if isinstance(LTObject, LTTextBox) or isinstance(LTObject, LTTextLine):
            for line in LTObject.get_text().split('\n'):
                lines.append(line.encode('ascii', 'ignore').upper().strip())
        elif isinstance(LTObject, LTFigure):
            parseLTObjects(LTObject.objs, pageNo, lines)
        else:
            print "LT Type %s\n"%(LTObject)    
    return lines

def processData(data, count=False):
    global total, hkey

    assert len(data) == 4, "Error en formato de line X/Y/W/Z"
    
    hkey = ''

    for i in range(0,len(data)):
        data[i] = data[i].strip()
        hkey += data[i] + "_" 
                               
    hkey = hkey.replace(' ', '_')
    hkey = hkey[:len(hkey)-1]
    
    #annotate results (if proceed)
    if count:
        if False == belt.has_key(data[0]): belt[data[0]] = 1
        belt[data[0]] += 1

        if False == category.has_key(data[1]): category[data[1]] = 1
        category[data[1]] += 1

        if False == gender.has_key(data[2]): gender[data[2]] = 1
        gender[data[2]] += 1

        if False == weight.has_key(data[3]): weight[data[3]] = 1
        weight[data[3]] += 1

    total += 1
        
def extractByAcademy(filename):

    if False == os.path.isfile(filename):
        print "[WARM] Missing file '%s' in '%s'\n"%(filename, whoAmI()) 
        return

    tmp = None
    club = None
    
    fp = open(filename, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)
    document.initialize(None)
    if not document.is_extractable: raise Exception()#PDFTextExtractionNotAllowed()
    
    rsrcmgr = PDFResourceManager()
    
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        pagesno = 1 + pageno
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        
        printProgressBar(pageno,pagesno, 'Academies') 
        
        interpreter.process_page(page)
        layout = device.get_result() 
        lines = parseLTObjects(layout,pageno)

        for line in lines:
            if line.count('/') == 3:
                if club is None: club = tmp 
                data = line.split('/')

                processData(data, True)
            
                if False == knowledge.has_key(club): knowledge[club] = dict()

                if knowledge[club].has_key(hkey):
                    knowledge[club][hkey][4] += 1
                else:
                    knowledge[club][hkey] = data
                    knowledge[club][hkey].append(1)
                    
                    knowledge[club][hkey].append(0) #gold medals
                    knowledge[club][hkey].append(0) #silver medals
                    knowledge[club][hkey].append(0) #bronze medals
                #print "{%s-%s}Processing line %s - %i\n"%(club,hkey,line, knowledge[club][hkey][4])
            elif line.startswith('TOTAL'):
                academy[club] = [int(line.replace('TOTAL:','').strip()),0,0,0]
                club = None
            else:
                tmp = line.strip()
            
        del lines[:]
            
def extractByCategory(filename):
    
    if False == os.path.isfile(filename):
        print "[WARM] Missing file '%s' in '%s'\n"%(filename, whoAmI()) 
        return
    
    data = None
    isClub = False
     
    fp = open(filename, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)
    document.initialize(None)
    
    if not document.is_extractable: raise Exception()#PDFTextExtractionNotAllowed()
    
    pageno = 0	 
    rsrcmgr = PDFResourceManager()
    
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        pagesno = 1 + pageno
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        
        printProgressBar(pageno,pagesno, 'Categories') 
        
        interpreter.process_page(page)
        layout = device.get_result() 
        lines = parseLTObjects(layout,pageno)

        for line in lines:
            
            if line.count('/') == 3:
                data = line.split('/')

                processData(data, True)
                
                isClub =True
            elif line.startswith('TOTAL'):
                isClub = False
                #print "Total para %s: %i\n"%(hkey,int(line.replace('TOTAL:','').strip()))
            else:
                if isClub:
                    line = line.encode('ascii', 'ignore').upper().strip()
                    if False == knowledge.has_key(line) or False == knowledge[line].has_key(hkey):
                        #assert False, "Found absurd data with missing record (%s,%s)\n"%(line,hkey)
                        print "Found absurd tupla(%s,%s)\n"%(line,hkey)
                    
                    
        del lines[:]
       
def extractFromResults(filename):
    
    if False == os.path.isfile(filename):
        print "[WARM] Missing file '%s' in '%s'\n"%(filename, whoAmI()) 
        return

    
    data = None
    category = None
    club = None
     
    fp = open(filename, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)
    document.initialize(None)
    
    if not document.is_extractable: raise Exception()#PDFTextExtractionNotAllowed()
    
    pageno = 0     
    rsrcmgr = PDFResourceManager()
    
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        pagesno = 1 + pageno
    
    for  (pageno, page) in enumerate(PDFPage.create_pages(document)):
        
        printProgressBar(pageno,pagesno, 'Results') 
        
        interpreter.process_page(page)
        layout = device.get_result() 
        lines = parseLTObjects(layout,pageno)

        for line in lines:
            
            if line.count('/') == 3:
                
                category = line.split('/')
                processData(category, True) 
                
            elif line.count(' - '):
                
                data = line.strip().upper().split(' - ')
                
                assert len(data) > 2, "Error found invalid athlete line"
                
                if data[0] not in ('FIRST','SECOND','THIRD'): continue
                if category[len(category)-1] == 'OPEN CLASS': continue
                
                club = data[len(data) - 1]
                for i in range(len(data)-2,1,-1): 
                    club = data[i] + ' - ' + club
                
                if False == knowledge.has_key(club):
                    knowledge[club] = dict()
                    print "Added new club '%s'\n"%(club)
                    
                if False == knowledge[club].has_key(hkey):
                    if category[len(category)-1] != 'OPEN CLASS':
                        print "[WARM] Is not 'Open Class record' -> Some illogical data found in line '%s-%s-%s'\n"%(club,data,category)
                    knowledge[club][hkey]=category
                    knowledge[club][hkey].append(1)
                    knowledge[club][hkey].append(0)
                    knowledge[club][hkey].append(0)
                    knowledge[club][hkey].append(0)
                    academy[club] = [1,0,0,0]
                else:
                    if category[len(category)-1] == 'OPEN CLASS':
                        knowledge[club][hkey][4] += 1
                                              
                if "FIRST" == data[0]: 
                    knowledge[club][hkey][5] += 1
                    academy[club][1] += 1
                elif "SECOND" == data[0]: 
                    knowledge[club][hkey][6] += 1
                    academy[club][2] += 1
                elif "THIRD" == data[0]: 
                    knowledge[club][hkey][7] += 1
                    academy[club][3] += 1
                else:
                    print data    
                    
        del lines[:]
 
def dumpKnowledge():
    with open('../data/data.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Academy","Belt","Category","Gender","Weight","#Athlete","#Gold","#Silver","#Bronze"])
        for c in knowledge.keys():
            for h in knowledge[c].keys():
                writer.writerow([c,knowledge[c][h][0],knowledge[c][h][1],knowledge[c][h][2],knowledge[c][h][3],knowledge[c][h][4],knowledge[c][h][5],knowledge[c][h][6],knowledge[c][h][7]])

def dumpBelts():
    with open('../data/belts.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Belt","#Athlete","% Athlete"])
        for c in belt.keys():
            writer.writerow([c,belt[c], 1.0 * belt[c]/total])

def dumpCategories():
    with open('../data/categories.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Category","#Athlete","% Athlete"])
        for c in category.keys():
            writer.writerow([c,category[c], 1.0 * category[c]/total])

def dumpGenders():
    with open('../data/genders.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Gender","#Athlete","% Athlete"])
        for c in gender.keys():
            writer.writerow([c,gender[c], 1.0 * gender[c]/total])

def dumpWeights():
    with open('../data/weights.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Weight","#Athlete","% Athlete"])
        for c in weight.keys():
            writer.writerow([c,weight[c], 1.0 * weight[c]/total])

def dumpAcademy():
    with open('../data/academies.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["Academy","#Athlete","% Athlete", "#Gold","#Silver","#Bonze","% Success"])
        for c in academy.keys():
            p = 1.0 * academy[c][0]
            s = 1.0 * (academy[c][1] + academy[c][2] + academy[c][3])
            s /= p
            p /= total
            try:
                writer.writerow([c,academy[c][0],p,academy[c][1],academy[c][2],academy[c][3],s])
            except:
                print "Error generating academy data (%s-%s-%s)\n"%(total,c,academy[c])                
if __name__ == '__main__':
    
    for root, directories, files in os.walk('../data'):
        for directory in directories:
            filename = os.path.join(root, directory)
            
            cleanup()
            
            extractByAcademy(os.path.join(filename, 'RegistrationsByAcademy.pdf'))
            #extractByCategory(os.path.join(filename, 'RegistrationsByCategoryAndAcademy.pdf'))
            extractFromResults(os.path.join(filename, 'Results.pdf'))
                                    
            dumpKnowledge()
            dumpBelts()
            dumpCategories()
            dumpGenders()
            dumpAcademy()	
            dumpWeights()                        
                            
    
