How it works:
1) pip install -r requirements.txt
2) Set up aws textract and input credentials  https://docs.aws.amazon.com/textract/latest/dg/api-async-roles.html (make sure to configure crendentials)
3) Download out_large and add to repo: https://1drv.ms/u/s!Auc3VRul9wo5hgr8jwhFD8iPCYp1?e=UsJJ2V
4)	Run textract on pdfs
python3 textractor.py --documents s3://[bucketname]/[pdfname].pdf –-text –tables
For example:
python3 textractor.py --documents s3://konektid-dec-resources/PDACT298.pdf -–text
 **this only runs the text detection part of textract. If we wanted to use table detection add –-tables to the end. 
For example:
python3 textractor.py --documents s3://konektid-dec-resources/PDACT298.pdf –-text --tables

5)	Run driver.py
a.	Parameters: a list of all of the pdf ids, a Boolean indicating whether to use tables or not, list of primes file name, list of job titles file name, evaluations spreadsheet file name, name of results csv file.
b.	Result = Driver.getData([pdf ids], [use tables], [primes file name], [job titles file name], [evaluations spread sheet file name], [desired results csv file name])
 
Stats
1)	Accuracy : 66.5%
2)	Recall : 70.4%
3)	Precision : 63.3%
4)	False-negative Rate : 29.6%

How to improve
1)	Improve the algorithm used to match names with their job title. We are currently, looking through a large list of job titles and looking for names around each job title found in the document. There is no sorting or formal way to decipher a person’s job title. 
2)	Have a way to sort each person by their organization. 

Code Structure
1)	Driver is the main class. It deals with getting all of the information and organizing it into a cvs file. It gets the metadata from the online server. All of the contact information comes from the ContactFinder object from the class Mining. 
2)	Mining is the meat of the program. It has an object called ContactFinder. When a ContactFinder object is created, it finds the names and organizations listed in the evaluations given in one of its parameters. Driver creates this object and then gets all of the information using the get_tag_list method. 
