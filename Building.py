import tkinter as tk
from tkinter import ttk
from tkinter import *
import glob
import pandas as pd
import pm4py
import datetime

#wilgy: Event log filtering modules
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter

#wilgy: Visualisation modules
from pm4py.visualization.graphs import visualizer as graphs_visualizer

#wilgy: Statistical modules
from pm4py.statistics.traces.generic.log import case_statistics, case_arrival

#*****************************************************************************
#wilgy: This section builds a user interactive window to select percentage thresholds
#*****************************************************************************

#wilgy: build variants percentage window for user interaction. Includes slider for selection. 
variants_percentage_selection = tk.Tk()
current_value = tk.DoubleVar()
variants_percentage_selection.geometry('500x250')
variants_percentage_selection.resizable(False, False)
variants_percentage_selection.title('Percentage Selector')

#wilgy: configure grid settings for window
variants_percentage_selection.columnconfigure(0, weight=1)
variants_percentage_selection.columnconfigure(1, weight=3)

#wilgy: function to format the percentage selection.
def get_current_value():
    return '{: .0f} percent'.format(current_value.get()*100)

#wilgy: function listens for slider move and changes value label accordingly.
def slider_changed(event):
    value_label.configure(text=get_current_value())

#wilgy: function to close the window and return the selected percentage.
def closeWindow():
    selected_value = current_value.get()
    selected_value = round(selected_value, 2)
    current_value.set(selected_value)
    print("Selected threshold: {}".format(selected_value))
    variants_percentage_selection.destroy()
    return selected_value

#wilgy: label for the slider
slider_label = ttk.Label(variants_percentage_selection, text='The percentage setting determines the minimum \n'
    + 'occurrences of a process to be considered. \nUse the slider to make your selection:',padding=20)
slider_label.grid(column=0, row=0, sticky='w')

#wilgy: sets the scale for the slider widget, i.e., 0.1 is 10 percent.
slider = ttk.Scale(variants_percentage_selection, from_=0.0, to=0.1, orient='horizontal', 
    command=slider_changed, variable=current_value)
slider.grid(column=1, row=0, ipadx=20)

# current value label
current_value_label = ttk.Label(variants_percentage_selection, text='Current Value:')
current_value_label.grid(row=1, columnspan=2, sticky='n', ipadx=10, ipady=10)

# value label
value_label = ttk.Label(variants_percentage_selection, text=get_current_value())
value_label.grid(row=2, columnspan=2, sticky='n')

#wilgy:clicking OK button will close the window
button = Button(variants_percentage_selection, text="Ok", fg='blue', command=closeWindow) 
button.place(relx=0.5, rely = 0.75, anchor=CENTER)
variants_percentage_selection.mainloop()

#*****************************************************************************
#End of window
#*****************************************************************************

#*****************************************************************************
#wilgy: This section builds a user interactive window to select what type of
#       algorithm to use for process mining.
#*****************************************************************************


miner_window=Tk()
miner_selection=IntVar()
#wilgy: function returning the value of miner selection
def minerValue():
    value = miner_selection.get()
    print("Selected miner: {}".format(value))
    return value

#wilgy: function to close miner threshold selection window. If no algorithm selected, default to 1 (DFG).
def closeMinerWindow():
    value = miner_selection.get()
    if value == 0:
        miner_selection.set(1)
    miner_window.destroy()

#wilgy: New window to select which miner to utilise
Label(miner_window, text='Select which process mining algorithm to utilise:').pack(pady=20)
Radiobutton(miner_window, text="Directly Follows Graph",variable=miner_selection, value=1, command=minerValue).pack()
Radiobutton(miner_window, text="Heuristics Miner",variable=miner_selection, value=2, command=minerValue).pack()
Radiobutton(miner_window, text="Petri Net",variable=miner_selection, value=3, command=minerValue).pack()
Radiobutton(miner_window, text="Inductive Miner",variable=miner_selection, value=4, command=minerValue).pack()
Button(miner_window, text="Ok", fg='blue', command=closeMinerWindow).pack(pady=20) #wilgy:clicking OK button will close the window

#wilgy: Setting parameters of the GUI           
miner_window.title('PM Algorithm selection')
miner_window.geometry("400x300+10+10")
miner_window.mainloop()

#*****************************************************************************
#End of window
#*****************************************************************************

#wilgy: function returns the full file path of the target filename
#(useful if users have saved file path in varying locations)
def find_files(filename, path):
    file=[f for f in glob.glob(path + '**/' + filename, recursive=True)]
    for f in file:
        return(f)

#wilgy: function converts csv to event log format, with relevant variables selected as keys.
#Also filters the eventlog to determine start activities and corresponding count of each start activity.
def import_pm4py(event_log):
    event_log = pm4py.format_dataframe(event_log, case_id='EpisodeNo', activity_key='Activity'
        , timestamp_key='EndTime',start_timestamp_key='EventTime')
    start_activities = pm4py.get_start_activities(event_log)
    print("Number of unique start activities: {}".format(len(set(start_activities))))
    return event_log

#wilgy: function utilises pandas to import the csv and display the count of events and total cases.
def import_csv(file_path):
    event_log = pd.read_csv(file_path, sep=',')
    num_events = len(event_log)
    num_cases = len(event_log.EpisodeNo.unique())
    print("Number of events: {}\nNumber of cases: {}".format(num_events, num_cases))
    return event_log

#wilgy: function to discover and view directly follows graph (DFG). Output as PDF.
def pm_dfg(event_log):
    dfg, start_activities, end_actvities = pm4py.discover_dfg(event_log)
    pm4py.view_dfg(dfg, start_activities, end_actvities, 'pdf')

#wilgy: from GGrossman.
def pm_heuristics(df):
    print("Discover heuristics net ...")
    # https://pm4py.fit.fraunhofer.de/static/assets/api/2.2.18/pm4py.html?highlight=discover_heuristics_net#pm4py.discovery.discover_heuristics_net
    map = pm4py.discovery.discover_heuristics_net(df,current_value.get())
    # The map object is a HeuristicsNet
    print("Class name of variable map: " + map.__class__.__name__)
    print("Visualizing heuristics net ...")
    pm4py.view_heuristics_net(map,"pdf")

#MAIN
df = import_pm4py(import_csv(find_files('log_dataset.csv', 'C:')))
#Convert DataFrame object into an EventLog object (which is required for querying variants):
event_log = pm4py.convert_to_event_log(df)
#wilgy: filter variants experimenting
filter = pm4py.filter_variants_percentage(event_log, current_value.get())

""" #wilgy: Statistics - find the median case duration of the filtered log
median_case_duration = case_statistics.get_median_case_duration(filter, parameters={case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
print("Median case duration (days): {}".format(round(median_case_duration/86400,2)))"""

#wilgy: Statistics - display graph of event distribution, binned by Month.
"""x, y = attributes_filter.get_kde_date_attribute(filter, attribute="time:timestamp")
gviz = graphs_visualizer.apply_plot(x, y, variant=graphs_visualizer.Variants.DATES)
graphs_visualizer.view(gviz)"""

pm4py.view_events_distribution_graph(filter, distr_type="months", format="pdf")


#wilgy: Call the selected method to produce respective process mining output. 
pmSelector = miner_selection.get()
print('pmSelector: {}'.format(pmSelector))
if pmSelector == 1:
    pm_dfg(filter)
if pmSelector == 2:
    pm_heuristics(filter)
#TODO Add last two algorithm methods
else:
    print("end of prog")
 

#wilgy: Explore details of a single EpisodeID:
episodeID = input("Enter the EpisodeID #: ")
print("EpisodeID selection: {}".format(episodeID))


#create new data frame, containing only the selected EpisodeID
df2 = df.loc[df["case:concept:name"] == episodeID]

while len(df2) == 0:
    print("Selected EpisodeID does not exist. Please try again")
    episodeID = input("Enter the EpisodeID #: ")
    df2 = df.loc[df["case:concept:name"] == episodeID]

else:
    episode_event_log = pm4py.convert_to_event_log(df2)
    #using median case duration for single episodeID to return int, rather than get all case durations which returns list.
    case_duration = case_statistics.get_median_case_duration(episode_event_log, parameters={case_statistics.Parameters.TIMESTAMP_KEY:'time:timestamp'})
    case_duration = round(case_duration/86400, 2)
    #pm4py.view_events_distribution_graph(episode_event_log, distr_type="months", format="pdf")
    print(df2)
    print("EpisodeID {} contains {} events. The total case duration is {} days".format(episodeID, len(df2), case_duration))

    case_duration = case_statistics.get_cases_description(episode_event_log)
    print("New case duration: {}".format(case_duration))
    print(round(case_duration[episodeID]['caseDuration']/86400, 2))

    #case_events = case_statistics.get_events(episode_event_log, episodeID)
    #print(case_events)

    start_time = datetime.datetime.now()
    print(start_time)
    #df_start_time = df2["EventTime"][0]
    print(df2["EventTime"][0])
    print(df2["time:timestamp"][len(df2) -1])
    print("My duration:")
    print((df2["time:timestamp"][len(df2) -1]) - (df2["time:timestamp"][0])) 


    










