#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 14:17:06 2020

@author: dohertyguirand
"""
import nltk
nltk.download('punkt')

from bert import Ner
# from pdfminer3.layout import LAParams, LTTextBox
# from pdfminer3.pdfpage import PDFPage
# from pdfminer3.pdfinterp import PDFResourceManager
# from pdfminer3.pdfinterp import PDFPageInterpreter
# from pdfminer3.converter import PDFPageAggregator
# from pdfminer3.converter import TextConverter
import io
import urllib.request
import re
from collections import Counter
import pandas as pd
import math
import sys
import timeit
import os
import random
import numpy as np
import itertools
import csv


class ContactFinder():

    def __init__(self,pdf_name,num_pages,potenital_prime,primes_file,job_titles_file,use_tables = False):
        self.pdf_name = pdf_name
        self.use_tables = use_tables
        self.primes_list = self.make_list_from_file(primes_file)
        self.titles_list = self.make_list_from_file(job_titles_file)

        self.person_pattern = re.compile(r'Person|Name|Contact')
        self.organization_pattern = re.compile(r'Organization|')
        self.title_pattern = re.compile(r'Position|Title')
        self.people_df = pd.DataFrame()
        self.text = open("{}-text.txt".format(pdf_name+"-pdf"), 'r').read()
        self.ner_output = self.runNER(self.text)
        self.org_list = self.findTag(self.ner_output,'ORG')
        self.people_list = self.findTag(self.ner_output,'PER')
        self.staff_list = self.make_staff_list()
        self.prime, self.stakeholders,self.partners = self.organize_orgs(potenital_prime)

    def get_tag_list(self,tag):
        if tag == "PER":
            return self.people_list
        if tag == "ORG":
            return self.org_list
        if tag == "STAFF":
            return self.staff_list
        if tag == "PRIME":
            return self.prime
        if tag == "STAKEHOLDER":
            return self.stakeholders
        if tag == "PARTNERS":
            return self.partners
        return []


    #pdfname WITHOUT .pdf
    #columns have no labels
    #first item in each column is the title of the column

    #updates people if uses tables

    def flat_list(self,csv):
        with open(csv, newline='') as f:
            reader = f.reader(csv)
            data = list(reader) 
        flat_list = []
        for sublist in data:
            for item in sublist:
                flat_list.append(item)
        return flat_list

    def organize_orgs(self,potential_prime):
        orgs = self.org_list
        orgs_dict = Counter(orgs)
        for i in range(0, len(self.primes_list)):
            if potential_prime.lower() in self.primes_list[i].lower():
                prime = potential_prime
                if not prime:
                    prime = [primes for primes in orgs if primes in self.primes_list]
        keywords = ['Government', 'Agency', 'Department']
        stakeholders = {key: orgs_dict[key] for key in orgs_dict for i in range(0, len(keywords)) if keywords[i] in key.split()}
        stakeholders = [*dict.fromkeys(stakeholders)]
        partners = [x for x in orgs if x not in prime]
        partners = [y for y in partners if y not in stakeholders]
        return prime,stakeholders,partners

    def make_list_from_file(self,file):
        fin = open(file,'r')
        data = fin.read()
        fin.close()
        data = data.splitlines()
        return data

    def make_staff_list(self):
        staff_df,title_dict = self.find_title_matches()
        staff_df = self.find_name_with_title(staff_df)
        if self.use_tables:
            people_from_tables = self.find_in_tables(self.pdfname,self.people_list, self.numpages)
            self.people_list = self.people_list + people_from_tables['Name'].to_list()
            frames = [people_from_tables,staff_df]
            staff_df = pd.concat(frames, keys = ['table', 'text'])
            staff_df.drop_duplicates(subset ="Title", keep = 'first', inplace = True)
        staff_dict = {}
        for row in staff_df.itertuples():
            title = str(row.Title)
            name = str(row.Name)
            staff_dict[title] = name
        return [staff_dict]


    def find_in_tables(self,pdfname,people_dict,numpages):
        person_pattern = re.compile(r'Person|Name')
        organization_pattern = re.compile(r'Organization')
        title_pattern = re.compile(r'Position|Title')
        for i in range(1,numpages):
            try:
                table_file_path = '{}-pdf-page-{}-tables.csv'.format(pdfname, i)
                if os.stat(table_file_path).st_size != 0:
                    table_df = pd.read_csv(table_file_path, header = 1)
                    name_column, name_col_num = self.g.look_for_name_column(table_df,people_dict)
                    title_column, title_col_num = self.look_for_titles_column(self.titles_list, table_df)
                    col_names = self.check_col_names(table_df)
                    #word_length, name_column = ContactFinding.check_item_length(table_df)
                    if col_names or name_column:
                        people_data = pd.DataFrame()
                        for col in table_df.columns:
                            if re.search(person_pattern,col) or col == name_col_num:
                                people_data['Name'] = table_df[col].tolist()
                            if re.search(title_pattern, col) or col == title_col_num:
                                people_data['Title'] = table_df[col].tolist()
                            if re.search(organization_pattern, col):
                                people_data['Organization'] = table_df[col].tolist()
                        #explode each row if needed
                        list_of_row_dics = people_data.to_dict('records')
                        new_df = pd.DataFrame()
                        for row_dic in list_of_row_dics:
                            num_list_pattern = re.compile(r"((\d+|[MDCLXVI]+)(\.|\))\s.([a-zA-Z]+\s?)+)")
                            
                            found_list = False
                            for key in row_dic.keys():
                                if re.search(num_list_pattern,str(row_dic[key])):
                                    matches = re.findall(num_list_pattern, str(row_dic[key]))
                                    found_list = True
                                    row_dic[key] = [a_tuple[0].replace(a_tuple[1]+a_tuple[2],'').strip() for a_tuple in matches]
                            
                            if found_list:
                                row_df = pd.DataFrame([[i] * len(matches) if not isinstance(i,type(list)) else i for i in row_dic.values()],index=row_dic.keys()).T
                            else:
                                row_df = pd.DataFrame(row_dic,index=[0])
                            new_df = new_df.append(row_df)
    
                        people_data = pd.concat([people_data, new_df])
            except pd.errors.ParserError:
                continue
        return people_data



    def look_for_name_column(self,table_df,people_dict):
        count = 0
        for col in table_df.columns:
            for item in table_df[col].tolist():
                if item in people_dict.keys(): count += 1
            percent_names = count/len(table_df[col].tolist()) * 100
            if percent_names > 75:
                return True, col
        return False, None

    def look_for_titles_column(self,titles,table_df):
        count = 0
        for col in table_df.columns:
            for item in table_df[col].tolist():
                if item in titles:
                    count +=1
            percent_titles = count/len(table_df[col].tolist()) * 100
            if percent_titles > 50:
                return True, col
        return False, None



    def check_item_length(self,table_df):
        num_words_list = []
        for col in table_df.columns:
            for item in table_df[col].tolist():
                num_words_list.append(len(str(item).split()))
            mean = sum(num_words_list)/len(num_words_list)
            percent_off = np.mean(np.abs((mean - 2) / mean)) * 100
            if percent_off < 3:
                return True, col
        return False, None
            
    def check_col_names(self,table_df):
        people_found = False
        title_found = False
        organization_found = False
        person_pattern = re.compile(r'Person|Name')
        organization_pattern = re.compile(r'Organization')
        title_pattern = re.compile(r'Position|Title')
        for col in table_df.columns:
            if re.search(person_pattern, col):
                people_found = True
            if re.search(title_pattern, col):
                title_found = True
            if re.search(organization_pattern, col):
                organization_found = True
        return people_found
   
    def categorize_titles(df):
        usaid_dic,project_dic, evaluation_dic, other_dic = {}, {} , {}, {}
        project_regex = re.compile(r'([A-Z][a-z]*\s?)*Chief\sof\sParty|([A-Z][a-z]*\s?)*Lead|([A-Z][a-z]*\s?)*Specialist|([A-Z][a-z]*\s?)*Expert|([A-Z][a-z]*\s?)*Advisor')
        usaid_regex = re.compile(r'\bMission(\s[A-Z][a-z]*)*|\bAOR\b|\bAdministrative(\s[A-Z][a-z]*)*|\bCOR\b|\bCO\b|([A-Z][a-z]*\s?)*Officer|([A-Z][a-z]*\s?)*Representative')
        evaluation_regex = re.compile(r'([A-Z][a-z]*\s?)*Evaluation(\s[A-Z][a-z]*)*|MEL')
        for row in df.itertuples():
            title = str(row.Title)
            name = str(row.Name)
            if(re.search(project_regex, title)):
                project_dic[title] = name
            if(re.search(usaid_regex, title)):
                usaid_dic[title] = name
            if(re.search(evaluation_regex, title)):
                evaluation_dic[title] = name
            else:
                other_dic[title] = name
        return [usaid_dic],[project_dic], [evaluation_dic], [other_dic]  

    # def getTextFromPDF(url):
    #     open = urllib.request.urlopen(url).read()
    #     memoryFile = io.BytesIO(open)
        
    #     resource_manager = PDFResourceManager()
    #     fake_file_handle = io.StringIO()
    #     converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    #     page_interpreter = PDFPageInterpreter(resource_manager, converter)
        
        
    #     with memoryFile as fh:
        
    #         for page in PDFPage.get_pages(fh,
    #                                       caching=True,
    #                                       check_extractable=True):
    #             page_interpreter.process_page(page)
        
    #         text = fake_file_handle.getvalue()
        
    #     # close open handles
    #     converter.close()
    #     fake_file_handle.close()
    #     return text
        
    def split_lines(self,text):
        lines = []
        for line in text.splitlines():
            if (not line.isspace()) and( not line == ""):
                lines.append(line)
        return lines
    
    def find_title_matches(self,titleDictionary = {}):
        titles = self.titles_list
        lines = self.split_lines(self.text)
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
    
    def findTitles(self,text):
            titles = re.compile(r'\bMission(\s[A-Z][a-z]*)+|\bAOR\b|\bAdministrative(\s[A-Z][a-z]*)*|\bCOR\b|\bCO\b|([A-Z][a-z]*\s?)+Officer|([A-Z][a-z]*\s?)+Representative|([A-Z][a-z]*\s?)*Chief\sof\sParty|([A-Z][a-z]*\s?)+Lead|([A-Z][a-z]*\s?)+Specialist|([A-Z][a-z]*\s?)*Expert|([A-Z][a-z]*\s?)+Advisor|([A-Z][a-z]*\s?)+Manager|([A-Z][a-z]*\s?)+Assistant')
            titleList = []
            if re.search(titles,text):
                for titleFound in re.finditer(titles, text):
                    titleFound = titleFound.group()
                    titleList.append(titleFound)
            return titleList
    
    def find_name_with_title(self, df):
        names = []

        for row in df.itertuples():
            lines = row.Line
            name_dict = {}
            for line in lines:
                for person in self.people_list:
                    pattern = re.compile(person)
                    if re.search(pattern,line):
                        if person in name_dict.keys():
                            num = name_dict[person]
                            num +=1 
                            name_dict[person] = num
                        else:
                            name_dict[person] = 1
                #nameProxNumList = []

                #for name in name_dict.keys():
                    #proximity = ContactFinding.findProximity(name, title, line)
                    #nameProxNumList.append({ 'Name':name ,'Proximity':proximity,'Count':name_dict[name]})
            #print(title + ": " + str(name_dict.keys()))
            if len(name_dict.keys()) > 0:
              nameList = [*name_dict] 
            else:
              nameList = []
            names.append(nameList)
        #df['NameProximityCount'] = nameProxNumList
        df['Name'] = names
        return df

    def remove_empty_titles(self,df):
        df = df[len(df.name) != 0]
        for row in df.itertuples():
            names = row.Name
            if len(names) == 0:
                df = df.drop(row, axis=0)
        return df
        
    
    def removeIgnoredOrgs(self,orgs):
        returnOrgs = []
        orgsToIgnore = []
        for org in orgs:
            if org not in orgsToIgnore:
                returnOrgs.append(org)
        return returnOrgs
        
    
    def findTag(self,nerOutput, tag):
        line = ""
        foundWithTag = []
        for i in nerOutput:
            if(i['tag'][0:1] != "I") and (line != ""):
                foundWithTag.append(line.lstrip())
                line = ""
            if tag in i['tag']:
                line += " " + i['word']
        if(line != ""): foundWithTag.append(line.lstrip())
        if len(foundWithTag) == 0: return []
        tag_dict = Counter(foundWithTag)
        tag_dict = {key: tag_dict[key] for key in tag_dict if len(key.split())!=1}
        tag_list = [*tag_dict]
        return tag_list


    #does not do anything yet

    def sortByProximity(self,list):
        sortedList = sorted(list, key = lambda i : (i['Proximity'], i['Count']))
        return sortedList
            
        
    #todo fix so that it can actually split into sentances 
    def splitIntoChunks(self,text):
        textSplit = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",text)
        chunks = []
        chunk = ""
        finalchunks = []
        
        for sent in textSplit:
            if (len(chunk) +1+ len(sent)) < 500:
                chunk += " " + sent
            else:
                chunks.append(chunk)
                chunk = sent
        chunks.append(chunk)
        for i in chunks:
            if len(i) < 500:
                finalchunks.append(i)
            else:
                split = [i[l:l+500] for l in range(0,len(text), 500)]
                for sp in split:
                    finalchunks.append(sp)
        finalchunks = self.removeEmptyIndcies(finalchunks)
        return finalchunks
    
    def splitSent(self,text):
        textSplit = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",text)
        return textSplit
    
    def merge(self,dict1, dict2): 
        res = {**dict1, **dict2} 
        return res
    
    def findProximity(self,name, title, line):
        namePattern = re.compile(name)
        titlePattern = re.compile(title)
        nameStartingIndecies = [m.start() for m in re.finditer(namePattern, line)]
        titleStartingIndecies = [m.start() for m in re.finditer(titlePattern, line)]
        nameEndingIndecies = [m.end() for m in re.finditer(namePattern, line)]
        titleEndingIndecies = [m.end() for m in re.finditer(titlePattern, line)]
        result = sys.maxsize
        if len(nameStartingIndecies) >= 1 and len(nameEndingIndecies) >=1 and len(titleStartingIndecies) >=1 and len(titleEndingIndecies) >=1:
            titleIndex = 0
            nameIndex = 0
            
            if nameStartingIndecies[0] < titleStartingIndecies[0]:
                nameIndex = nameEndingIndecies[0]
                titleIndex = titleStartingIndecies[0]
            elif nameStartingIndecies[0] > titleStartingIndecies[0]:
                nameIndex = nameStartingIndecies[0]
                titleIndex = titleEndingIndecies[0]
            result = abs(nameIndex - titleIndex)
        return result
    
    def removeEmptyIndcies(self,list):
        cleanList = []
        for i in list:
            if i != '':
                cleanList.append(i)
        return cleanList
                
    
    def runNER(self,text):
        model = Ner("out_large/")
        chunks = self.splitIntoChunks(text)
        output = model.predict(chunks[0])
        for i in range(1, len(chunks)):
            output = output + (model.predict(chunks[i]))
        return output

    def categorize_orgs(self,orgs):
        finalPrime = []
        finalPartners = []
        finalStakeholders = []
        with open('primes1.csv', newline='') as f:
            reader = csv.reader(f)
            data = list(reader) 
        flat_list = []
        for sublist in data:
            for item in sublist:
                flat_list.append(item)
        orgs = {key: orgs[key] for key in orgs if len(key.split())!=1}
        orglist = list(dict.fromkeys(orgs))
        prime = [primes for primes in orglist if primes in flat_list] 
        finalPrime.append(prime)
        keywords = ['Government', 'Agency', 'Department']
        stakeholders = {key: orgs[key] for key in orgs for i in range(0, len(keywords)) if keywords[i] in key.split()}
        stakeholders = list(dict.fromkeys(stakeholders))
        finalStakeholders.append(stakeholders)
        partners = [x for x in orglist if x not in prime]
        partners = [y for y in partners if y not in stakeholders]
        finalPartners.append(partners)
        return finalPrime, finalPartners, finalStakeholders

    
    
#if __name__ == '__main__':
        '''def get_text_and_tables_textractor(pdfname):
       pdfurl = "s3://decevals/{}".format(pdfname)
       list_of_args = ['--documents', pdfurl,'--text', '--tables']
       textractor.Textractor(list_of_args)
       print(list_of_args)
       text_file_name = "{}-text.txt".format(pdfname)
       tables_file_name = "{}-tables.csv".format(pdfname)
       text = open(text_file_name, 'r').read()
       tables = open(tables_file_name,'r').read()
       return text,tables'''
