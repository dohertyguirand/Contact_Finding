import nltk
nltk.download('punkt')
import io
import pandas as pd
from mining import ContactFinder
nltk.download('punkt')
import PyPDF2, requests


class Driver():
        
    def getData(pdf_list, primes_file, job_titles_file,use_tables,metadata_csv_name,output_csv_name):
        #takes out the hypens in the pdf names
        updatedlist = []
        for i in range(0, len(pdf_list)):
            p1 = pdf_list[i][:2]
            p2 = pdf_list[i][3:6]
            p3 = pdf_list[i][7:10]
            pdfname = p1+p2+p3
            updatedlist.append(pdfname)

        #fills empty cells with the word "empty
        df = pd.read_csv(metadata_csv_name)
        newdf = df.fillna("Empty")

        anc = []
        personala = []
        bibtype = []
        date = []
        descr = []
        geo = []
        docid = []
        title = []
        file = []
        instaut = []
        instspon = []
        instpub = []
        link = []
        primelist = []
        partnerlist = []
        stakelist = []
        staff_list = []
        name_list = []
        pagenum = []

        for i in range(0,len(pdf_list)):
            
            df1 = newdf[newdf['Document ID'].str.contains(pdf_list[i])] #pulls the row with the corresponding pdf
            list = df1.values.tolist() #converts the row in the dataframe into a list
            if df1.empty: #if the pdf isn't in the csv file
                list = [['Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV','Not Found in CSV']]
            list = list[0]
            pdfname = pdf_list[i]
            p1 = pdfname[:2]
            p2 = pdfname[3:6]
            p3 = pdfname[7:10]
            url = "https://konektid-dec-resources.s3.amazonaws.com/" + p1 + p2 + p3 + ".pdf" #creates a url into the Konektid S3 bucket for the pdf
            anc.append(list[0])
            personala.append(list[1])
            bibtype.append(list[2])
            date.append(list[3])
            descr.append(list[4])
            geo.append(list[5])
            docid.append(list[6])
            title.append(list[7])
            file.append(list[8])
            instaut.append(list[9])
            instspon.append(list[10])
            instpub.append(list[11])
            link.append(url)
            response = requests.get(url)
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            num_pages = pdf_reader.numPages
            pagenum.append(num_pages)
            potentialprime = str(instaut[i][9:])
            cf = ContactFinder(updatedlist[i],num_pages,potentialprime,primes_file,job_titles_file)
            primelist.append(cf.get_tag_list("PRIME"))
            partnerlist.append(cf.get_tag_list("PARTNERS"))
            stakelist.append(cf.get_tag_list("STAKEHOLDER"))
            name_list.append(cf.get_tag_list("PER"))
            staff_list.append(cf.get_tag_list("STAFF"))

            

        metadata = pd.DataFrame ({
            'Ancillary Data': anc,
            'Personal Author': personala,
            'Bibtype Name': bibtype,
            'Date of Publication Freeforrm': date,
            'Descriptions from Thesaurus': descr,
            'Descriptors Geographic': geo,
            'Document ID': docid,
            'Document Title': title,
            'File': file,
            'Institution or USAID Bureau Author': instaut,
            'Institution or USAID Sponsor': instspon,
            'Institution or USAID Publisher': instpub,
            'Link to PDF': link,
            'Number of Pages': pagenum,
            'Prime': primelist,
            'Partners': partnerlist,
            'Stakeholders': stakelist,
            'All Staff' : staff_list,
            'All Names' : name_list
        })
        metadata.to_csv(output_csv_name) 
if __name__ == "__main__":
    result = Driver.getData(['PD-ACT-298'],'primes.txt','job-titles.txt',False)
    
    