#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 11:10:00 2020

@author: dohertyguirand
"""

import pandas as pd


def make_list_from_file(file):
    fin = open(file,'r')
    data = fin.read()
    fin.close()
    data = data.splitlines()
    return data

def split_lines(text):
    lines = []
    for line in text.splitlines():
        if (not line.isspace()) and( not line == ""):
            lines.append(line)
    return lines

def find_title_matches(titleDictionary = {}):
    titles = make_list_from_file('job-titles.txt')
    text = open('PA00WPHQ-pdf-text.txt','r').read()
    lines = split_lines(text)
    #chunks = ContactFinding.splitIntoChunks(text)
    for title in titles:
        for i in range(0, len(lines)):
            if title in lines[i]:
                threeLines = lines[i]
                if i > 0 and i < (len(lines) - 2):
                    threeLines = lines[i-1] +" "+ lines[i] +" " +lines[i+1]
                if i == 0 and len(lines) > 2 :
                    threeLines = lines[i] +" "+lines[i+1]
                if i == (len(lines) - 1) and len(lines) > 2:
                    threeLines = lines[i-1] + " " + lines[i]
                if len(lines) == 2:
                    threeLines = lines[0] + " " + lines[1]
                    
                if title in titleDictionary.keys():
                    titleDictionary[title].append(threeLines)
                else:
                    lines_list = []
                    lines_list.append(threeLines)
                    titleDictionary[title] = lines_list
    df = pd.DataFrame(list(titleDictionary.items()), columns = ['Title', 'Line'])
    return df,titleDictionary

print(find_title_matches())


