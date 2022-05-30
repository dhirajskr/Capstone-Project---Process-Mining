from owlready2 import *
from owlready2.pymedtermino2 import *
from owlready2.pymedtermino2.umls import *
import glob
import pandas as pd
import string, time
from tqdm import tqdm

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
            if tag in ('NNP', 'NN') : # If the word is a noun
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

df = pd.read_csv(find_files('ed13reduced.csv', 'C:'))

#wilgy: convert column to type string. 
df['presenting_problem'] = df['presenting_problem'].astype(str)
#wilgy: create list of unique activities
activity_list = df.presenting_problem.unique()

#wilgy: strip punctuation (and replace with a space) from the list (required to complete search of metathesaurus) and append to new activity_list_stripped
activity_list_stripped = []
trans = str.maketrans(dict.fromkeys(string.punctuation, " "))
for i in activity_list:
    i = i.translate(trans)
    activity_list_stripped.append(i)

#wilgy: compare length of each list to ensure no activities were omitted while stripping. 
print('Count of unique activities (activity_list): {}'.format(len(activity_list)))
print('Count of unique activities (activity_list_stripped): {}'.format(len(activity_list_stripped)))

# wilgy: search SNOMED terminology for any matches, tracking the count of matches to determine overall matching 
# success rate. If matches found, display the results for the first 5 phrases, and the first 3 corresponding matches to that phrase.  
count_success = 0
for i in tqdm(range(len(activity_list_stripped)), desc = "Conducting search of SNOMED..."):
    sno_result = SNOMEDCT.search(activity_list_stripped[i].lower()) #convert string to lowercase due to pyMedTermino2 query function utilisation of keyword 'NOT' and 'OR'.
    if len(sno_result) > 0:
        count_success += 1
        if count_success <= 5:
            print("Potential SNOMED matches for '" + str(activity_list_stripped[i]) + "'" + ": \n{}".format(sno_result[:3]))      
success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had potential matches. Therefore the success rate is %{}".format(len(activity_list),count_success, round(success_rate, 2)))
print("***Finished SNOMED***\n")


# wilgy: search UMLS terminology for any matches, tracking the count of matches to determine overall matching 
# success rate. If matches found, display the results for the first 5 phrases, and the first 3 corresponding matches to that phrase.  
count_success = 0
for i in tqdm(range(len(activity_list_stripped)), desc = "Conducting search of UMLS..."):
    umls_result = CUI.search(activity_list_stripped[i].lower()) #convert string to lowercase due to pyMedTermino2 query function utilisation of keyword 'NOT' and 'OR'.
    if len(umls_result) > 0:
        count_success += 1
        if count_success <= 5:
            print("Potential SNOMED matches for '" + str(activity_list_stripped[i]) + "'" + ": \n{}".format(umls_result[:3]))      
success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had potential matches. Therefore the success rate is %{}".format(len(activity_list),count_success, round(success_rate, 2)))
print("***Finished UMLS***\n")

print('++++++++++++++++++++++++++++++++++++++++++++++++++')

#wilgy: Extract list of nouns from the provided data.
nouns_list = []
print("Extracting nouns...")
for i in activity_list_stripped: 
    nouns_in_phrase = []
    if len(ProperNounExtractor(i))>0:
        nouns_in_phrase = ProperNounExtractor(i)
        for i in nouns_in_phrase:
            #print(i)
            nouns_list.append(i)

#wilgy: convert list to a set to extract unique entries.
nouns_set = set(nouns_list)
#wilgy: convert back to a list. 
nouns_list = list(nouns_set)
print("Found {} unique nouns".format(len(nouns_list)))

print('++++++++++++++++++++++++++++++++++++++++++++++++++\n')

#wilgy: Search SNOMED for matches against the list of nouns. 
print("Check nouns in SNOMED...")

noun_count=0
parent_count = 0
children_count = 0

for i in tqdm(range (len(nouns_list)), desc="Loading..."):
    sno_result = SNOMEDCT.search(nouns_list[i].lower())
    if len(sno_result) > 0:
        noun_count += 1
        #print("Potential matches for '" + str(i) + "' " + ":")
        #for i in sno_result: #determine how many parents and childrend the concept has. 
        #    parent_count = len(SNOMEDCT[i.name].parents) 
        #    children_count = len(SNOMEDCT[i.name].children)
        #    concept_label = i.label[0]
            
            #print(concept_label + ' (has {} parent/s and {} children.)\n'.format(parent_count, children_count))
                
        #else:
            #print("No matches found for '" + str(i) + "'\n")
print('Out of {} nouns, {} had matches.'.format(len(nouns_list), noun_count))
print("***Finished SNOMED***\n")

#wilgy: Display code runtime
print("Program runtime --- {} seconds --- (-- {} minutes --)".format((round((time.time() - start_time), 2)), (round(((time.time() - start_time)/60), 2) )))