import json
from helper import FileHelper
from ta import TextAnalyzer, TextMedicalAnalyzer, TextTranslater
from trp import *
import pandas as pd
from mining import ContactFinding as cf
import re
import csv
import itertools
class OutputGenerator:
    def __init__(self, response, fileName, forms, tables):
        self.response = response
        self.fileName = fileName
        self.forms = forms
        self.tables = tables
        self.text = ""
        self.document = Document(self.response)

    def _outputWords(self, page, p):
        pass
        '''csvData = []
        for line in page.lines:
            for word in line.words:
                csvItem  = []
                csvItem.append(word.id)
                if(word.text):
                    csvItem.append(word.text)
                else:
                    csvItem.append("")
                csvData.append(csvItem)
        csvFieldNames = ['Word-Id', 'Word-Text']
        FileHelper.writeCSV("{}-words.csv".format(self.fileName), csvFieldNames, csvData)'''

    def _outputText(self, page, p):
        text = page.text
        FileHelper.writeToFile("{}-text.txt".format(self.fileName), text)

        '''textInReadingOrder = page.getTextInReadingOrder()
        FileHelper.writeToFile("{}-text-inreadingorder.txt".format(self.fileName), textInReadingOrder)'''

    def _outputForm(self, page, p):
        pass
        '''csvData = []
        for field in page.form.fields:
            csvItem  = []
            if(field.key):
                csvItem.append(field.key.text)
                csvItem.append(field.key.confidence)
            else:
                csvItem.append("")
                csvItem.append("")
            if(field.value):
                csvItem.append(field.value.text)
                csvItem.append(field.value.confidence)
            else:
                csvItem.append("")
                csvItem.append("")
            csvData.append(csvItem)
        csvFieldNames = ['Key', 'KeyConfidence', 'Value', 'ValueConfidence']
        FileHelper.writeCSV("{}-forms.csv".format(self.fileName), csvFieldNames, csvData)'''

    def _outputTable(self, page, p):
        print('adding table')
        person_pattern = re.compile(r'Person|Name|Contact')
        organization_pattern = re.compile(r'Organization|')
        title_pattern = re.compile(r'Position|Title')
        csvData = []
        for table in page.tables:
            csvRow = []
            #csvRow.append("Table")
            #csvData.append(csvRow)
            for row in table.rows:
                csvRow  = []
                for cell in row.cells:
                    csvRow.append(cell.text)
                csvData.append(csvRow)
            #csvData.append([])
            #csvData.append([])
        if len(csvData) > 0: 
            df = pd.DataFrame(csvData)
            people_found, people_col_num = cf.look_for_name_column(df)
            titles_found, title_col_num = cf.look_for_titles_column(df)
            if people_found:
                    print("people found : " + str(p))
                    people_data = pd.DataFrame()
                    for col in table_df.columns:
                        if re.search(person_pattern,col) or col == people_col_num:
                            people_data['Name'] = table_df[col].tolist()
                        if re.search(title_pattern, col) or col == title_col_num:
                            people_data['Title'] = table_df[col].tolist()
                        if re.search(organization_pattern, col):
                            people_data['Organization'] = table_df[col].tolist()
                
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
                            row_df = pd.DataFrame([[i] * len(matches) if not isinstance(i,list) else i for i in row_dic.values()],index=row_dic.keys()).T
                        else:
                            row_df = pd.DataFrame(row_dic,index=[0])
                        new_df = new_df.append(row_df)

                    people_df = pd.concat([people_df, new_df])
                    file_name = "{}-page-{}-tables.csv".format(self.fileName, p)
                    print('saving')
                    people_df.to_csv(file_name)
        

                #FileHelper.writeCSVRaw("{}-page-{}-tables.csv".format(self.fileName, p), csvData)

    def run(self):

        if(not self.document.pages):
            return

        #FileHelper.writeToFile("{}-response.json".format(self.fileName), json.dumps(self.response))

        print("Total Pages in Document: {}".format(len(self.document.pages)))

        p = 1
        for page in self.document.pages:

            #FileHelper.writeToFile("{}-page-{}-response.json".format(self.fileName, p), json.dumps(page.blocks))

            self._outputWords(page, p)

            self._outputText(page, p)

            if(self.forms):
                self._outputForm(page, p)

            if(self.tables):
                self._outputTable(page, p)

            p = p + 1

    def _insights(self, start, subText, sentiment, syntax, entities, keyPhrases, ta):
        # Sentiment
        dsentiment = ta.getSentiment(subText)
        dsentimentRow = []
        dsentimentRow.append(dsentiment["Sentiment"])
        sentiment.append(dsentimentRow)

        # Syntax
        dsyntax = ta.getSyntax(subText)
        for dst in dsyntax['SyntaxTokens']:
            dsyntaxRow = []
            dsyntaxRow.append(dst["PartOfSpeech"]["Tag"])
            dsyntaxRow.append(dst["PartOfSpeech"]["Score"])
            dsyntaxRow.append(dst["Text"])
            dsyntaxRow.append(int(dst["BeginOffset"])+start)
            dsyntaxRow.append(int(dst["EndOffset"])+start)
            syntax.append(dsyntaxRow)

        # Entities
        dentities = ta.getEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = []
            dentitiesRow.append(dent["Type"])
            dentitiesRow.append(dent["Text"])
            dentitiesRow.append(dent["Score"])
            dentitiesRow.append(int(dent["BeginOffset"])+start)
            dentitiesRow.append(int(dent["EndOffset"])+start)
            entities.append(dentitiesRow)

        # Key Phrases
        dkeyPhrases = ta.getKeyPhrases(subText)
        for dkphrase in dkeyPhrases['KeyPhrases']:
            dkeyPhrasesRow = []
            dkeyPhrasesRow.append(dkphrase["Text"])
            dkeyPhrasesRow.append(dkphrase["Score"])
            dkeyPhrasesRow.append(int(dkphrase["BeginOffset"])+start)
            dkeyPhrasesRow.append(int(dkphrase["EndOffset"])+start)
            keyPhrases.append(dkeyPhrasesRow)

    def _medicalInsights(self, start, subText, medicalEntities, phi, tma):
        # Entities
        dentities = tma.getMedicalEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = []
            dentitiesRow.append(dent["Text"])
            dentitiesRow.append(dent["Type"])
            dentitiesRow.append(dent["Category"])
            dentitiesRow.append(dent["Score"])
            dentitiesRow.append(int(dent["BeginOffset"])+start)
            dentitiesRow.append(int(dent["EndOffset"])+start)
            medicalEntities.append(dentitiesRow)


        phi.extend(tma.getPhi(subText))

    def _generateInsightsPerDocument(self, page, p, insights, medicalInsights, translate, ta, tma, tt):

        maxLen = 2000

        text = page.text

        start = 0
        sl = len(text)

        sentiment = []
        syntax = []
        entities = []
        keyPhrases = []
        medicalEntities = []
        phi = []
        translation = ""

        while(start < sl):
            end = start + maxLen
            if(end > sl):
                end = sl

            subText = text[start:end]

            if(insights):
                self._insights(start, text, sentiment, syntax, entities, keyPhrases, ta)

            if(medicalInsights):
                self._medicalInsights(start, text, medicalEntities, phi, tma)

            if(translate):
                translation = translation + tt.getTranslation(subText) + "\n"

            start = end

        if(insights):
            FileHelper.writeCSV("{}-insights-sentiment.csv".format(self.fileName),
                            ["Sentiment"], sentiment)
            FileHelper.writeCSV("{}-insights-entities.csv".format(self.fileName),
                            ["Type", "Text", "Score", "BeginOffset", "EndOffset"], entities)
            FileHelper.writeCSV("{}-insights-syntax.csv".format(self.fileName),
                            ["PartOfSpeech-Tag", "PartOfSpeech-Score", "Text", "BeginOffset", "EndOffset"], syntax)
            FileHelper.writeCSV("{}-insights-keyPhrases.csv".format(self.fileName),
                            ["Text", "Score", "BeginOffset", "EndOffset"], keyPhrases)

        if(medicalInsights):
            FileHelper.writeCSV("{}-medical-insights-entities.csv".format(self.fileName),
                            ["Text", "Type", "Category", "Score", "BeginOffset", "EndOffset"], medicalEntities)

            FileHelper.writeToFile("{}-medical-insights-phi.json".format(self.fileName), json.dumps(phi))

        if(translate):
            FileHelper.writeToFile("{}-text-translation.txt".format(self.fileName), translation)

    def generateInsights(self, insights, medicalInsights, translate, awsRegion):

        print("Generating insights...")

        if(not self.document.pages):
            return

        ta = TextAnalyzer('en', awsRegion)
        tma = TextMedicalAnalyzer(awsRegion)

        tt = None
        if(translate):
            tt = TextTranslater('en', translate, awsRegion)

        p = 1
        for page in self.document.pages:
            self._generateInsightsPerDocument(page, p, insights, medicalInsights, translate, ta, tma, tt)
            p = p + 1
