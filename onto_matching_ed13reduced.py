from owlready2 import *
from owlready2.pymedtermino2 import *
from owlready2.pymedtermino2.umls import *
import glob
import pandas as pd
import string, time

start_time = time.time()

#wilgy: packages to tokenize sentences and extract nouns
import nltk 
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize, sent_tokenize

#wilgy: function returns the full file path of the target filename
#(useful if users have saved file path in varying locations)
def find_files(filename, path):
    file=[f for f in glob.glob(path + '**/' + filename, recursive=True)]
    for f in file:
        return(f)

#wilgy: function tokenizes the natural language passed in and extracts and returns nouns identified within the string. 
#https://pypi.org/project/nltk/
def ProperNounExtractor(text):
    """ProperNounExtractor tokenizes natural language and extracts and returns nouns identified within the string.

    Args:
        text (string): a string

    Returns:
        list: list of nouns
    """
    sentences = nltk.sent_tokenize(text)
    nouns = []
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        words = [word for word in words if word not in set(stopwords.words('english'))]
        tagged = nltk.pos_tag(words)
        for (word, tag) in tagged:
            if tag == 'NNP': # If the word is a proper noun
                nouns.append(word)
    return nouns


#wilgy: import the terminoloies from NLM metathesuarus:
#https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html?_gl=1*1o8wtvz*_ga*MTY1OTkyNDg0OS4xNjUwNDAxMjg2*_ga_7147EPK006*MTY1MTEyNzkyNy4xNC4wLjE2NTExMjc5MjcuMA..*_ga_P1FPTH9PL4*MTY1MTEyNzkyNy4xNC4wLjE2NTExMjc5MjcuMA..
#import takes approx 10 mins. Once initial import completed, it is not necessary to import every time the program is run, hence the following lines have been
#commented out. If new import is required, simply uncomment the lines below.    
""" default_world.set_backend(filename = "pym.sqlite3")
print('Importing terminologies...')
import_umls(find_files("umls-2021AB-metathesaurus.zip", 'C:'), terminologies = ["SNOMEDCT", "CUI"])
print('Imported') """

#wilgy: set backend for pyMedTermino2 to query and create relvant variables. 
default_world.set_backend(filename="pym.sqlite3")
PYM = get_ontology("http://PYM/").load()
SNOMEDCT = PYM["SNOMEDCT_US"]
CUI = PYM["CUI"] #UMLS




#TODO add user input search function
""" search_result = SNOMEDCT_US.search("Sendaway bag taken")
print("There are {} potential matches:".format(len(search_result)))
print(search_result) """

df = pd.read_csv(find_files('ed13reduced.csv', 'C:'))

#wilgy: convert column to type string. 
df['presenting_problem'] = df['presenting_problem'].astype(str)
#wilgy: create list of unique activities
activity_list = df.presenting_problem.unique()

#wilgy: strip punctuation from the list (required to complete search of metathesaurus) and append to new list
activity_list_stripped = []
for char in activity_list:
    char = char.translate({ord(i): None for i in string.punctuation})
    activity_list_stripped.append(char)

#wilgy: compare length of each list to ensure no activities were omitted while stripping. 
print('Count of unique activities (activity_list): {}'.format(len(activity_list)))
print('Count of unique activities (activity_list_stripped): {}'.format(len(activity_list_stripped)))

print("\nConducting Search of SNOMED...")
#Wilgy: Create list of potential matches for all unique activities. 
sno_list = []
count_success = 0
for i in activity_list_stripped:
    sno_result = SNOMEDCT.search(i.lower()) #convert string to lowercase due to pyMedTermino2 query function utilisation of keyword 'NOT'.
    if len(sno_result) > 0:
        count_success += 1
        sno_list.append(len(sno_result))
        #print("Potential SNOMED matches for '" + str(i) + "'" + ": \n{}".format(sno_result))
success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had matches. Therefore the success rate is %{}".format(len(activity_list),count_success, round(success_rate, 2)))
print("***Finished SNOMED***\n")

#UMLS
print("\nConducting Search of UMLS...")
umls_list = []
count_success = 0
for i in activity_list_stripped:
    umls_result = CUI.search(i.lower())
    if len(umls_result) != 0:
        count_success += 1
        umls_list.append(len(umls_result))
        #print("Potential UMLS matches for '" + str(i) + "'" + ": \n{}".format(umls_result))
success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had matches. Therefore the success rate is %{}".format(len(activity_list),count_success, round(success_rate, 2)))

print("***Finished UMLS***\n")

#wilgy: Display code runtime
print("Program runtime --- %s seconds ---" % round((time.time() - start_time), 2))