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
            if tag in ('NNP', 'NN'): # If the word is a proper noun
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

df = pd.read_csv(find_files('log_dataset.csv', 'C:'))

#wilgy: create list of unique activities
activity_list = df.Activity.unique()

#wilgy: strip punctuation from the list (required to complete search of metathesaurus) and append to new list
activity_list_stripped = []
trans = str.maketrans(dict.fromkeys(string.punctuation, " "))
for i in activity_list:
    i = i.translate(trans)
    activity_list_stripped.append(i)

#wilgy: compare length of each list to ensure no activities were omitted while stripping. 
print('Count of unique activities (activity_list): {}'.format(len(activity_list)))
print('Count of unique activities (activity_list_stripped): {}'.format(len(activity_list_stripped)))

# wilgy: search SNOMED terminology for any matches, tracking the count of matches to determine overall matching 
# success rate. If matches found, display the results for the phrase, and the corresponding matches to that phrase. 
count_success = 0
for i in activity_list_stripped:
    sno_result = SNOMEDCT.search(i)
    if len(sno_result) != 0:
        count_success += 1
        print("Potential SNOMED matches for '" + str(i) + "'" + ": \n{}".format(sno_result))

success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had matches. Therefore the success rate is %{}".format(len(activity_list_stripped),count_success, round(success_rate, 2)))
print("***Finished SNOMED***\n")

# wilgy: search UMLS terminology for any matches, tracking the count of matches to determine overall matching 
# success rate. If matches found, display the results for the phrase, and the corresponding matches to that phrase. 
count_success = 0
for i in activity_list_stripped:
    umls_result = CUI.search(i)
    if len(umls_result) != 0:
        count_success += 1
        print("Potential UMLS matches for '" + str(i) + "'" + ": \n{}".format(umls_result))

success_rate = (count_success/len(activity_list)) * 100
print("Out of {} activities, {} had matches. Therefore the success rate is %{}".format(len(activity_list_stripped),count_success, round(success_rate, 2)))


print("***Finished UMLS***\n")

#wilgy: create new list with test set data from data dictionary:
print("Searching with test set list...")
test_set_list = ['Referred request for NIPT', 'Local request for NIPT'
    , 'NIPT plain reporting test coversheet'
    , 'Troubleshooting request data sent back for the referring lab to action'
    , 'Troubleshooting request data for SNP to action', 'NIPT redraw request recollect', 'Venus PDF reporting test']


sno_list = []
for i in test_set_list:
    sno_result = SNOMEDCT.search(i)
    if len(sno_result) != 0:
        sno_list.append(len(sno_result))
        print("Potential SNOMED matches for '" + str(i) + "'" + ": \n{}".format(sno_result))
    else:
        print("No matches for '" + str(i) + "'.")
print("***Finished SNOMED***")

#wilgy: Extract list of nouns from the test_set_list.
nouns_list = []

print('++++++++++++++++++++++++++++++++++++++++++++++++++')

for i in test_set_list:
    print('Phrase: ' + i)
    
    this_list = []
    if len(ProperNounExtractor(i))>0:
        print('Nouns in phrase: ')
        this_list = ProperNounExtractor(i)
        for i in this_list:
            print(i)
            nouns_list.append(i)
        print("")
    else:
        print('No nouns found\n')
    
    

print('++++++++++++++++++++++++++++++++++++++++++++++++++')


#wilgy: convert list to a set to extract unique entries.
nouns_set = set(nouns_list)
#wilgy: convert back to a list. 
nouns_list = list(nouns_set)
print('Nouns list:')
print(nouns_list)

#wilgy: Search SNOMED for matches against the list of nouns. 
print("Check nouns in SNOMED...")

noun_count=0
parent_count = 0
children_count = 0

for i in nouns_list:
    sno_result = SNOMEDCT.search(i)
    if len(sno_result) > 0:
        noun_count += 1
        print("'" + str(i) + "' has {} potential matches. The first 3 matches are:".format(len(sno_result)))
        for i in sno_result[:3]: #determine how many parents and children the concept has. 
            parent_count = len(SNOMEDCT[i.name].parents) 
            children_count = len(SNOMEDCT[i.name].children)
            concept_label = i.label[0]
            
            print(concept_label + ' (has {} parent/s and {} children.)'.format(parent_count, children_count))
        print("\n*****\n")      
    else:
        print("No matches found for '" + str(i) + "'\n\n*****\n")
print('Out of {} nouns, {} had matches.'.format(len(nouns_list), noun_count))
print("***Finished SNOMED***\n")

#wilgy: Display code runtime
print("Program runtime --- {} seconds --- (-- {} minutes --)".format((round((time.time() - start_time), 2)), (round(((time.time() - start_time)/60), 2) )))



