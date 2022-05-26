import tkinter as tk
from tkinter import ttk
from tkinter import *
import glob
import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
import warnings
# sdhiraj: file transport
import os
 
# sdhiraj:
import re
from tkinter import END
 
# sdhiraj: miner algorithms
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.conversion.process_tree import converter as pt_converter
 
# wilgy: Event log filtering modules
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
 
# wilgy: Visualisation modules
# sdhiraj
from pm4py.visualization.graphs import visualizer as graphs_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
 
# wilgy: Statistical modules
from pm4py.statistics.traces.generic.log import case_statistics, case_arrival
from pm4py.statistics.traces.generic.pandas import case_statistics, case_arrival
 
# *****************************************************************************
# wilgy: This section builds a user interactive window to select percentage thresholds
# *****************************************************************************
 
# wilgy: build variants percentage window for user interaction. Includes slider for selection.
variants_percentage_selection = tk.Tk()
current_value = tk.DoubleVar()
variants_percentage_selection.geometry('500x250')
variants_percentage_selection.resizable(False, False)
variants_percentage_selection.title('Percentage Selector')
 
# wilgy: configure grid settings for window
variants_percentage_selection.columnconfigure(0, weight=1)
variants_percentage_selection.columnconfigure(1, weight=3)
 
 
# wilgy: function to format the percentage selection.
def get_current_value():
    return '{: .0f} percent'.format(current_value.get() * 100)
 
 
# wilgy: function listens for slider move and changes value label accordingly.
def slider_changed(event):
    value_label.configure(text=get_current_value())
 
 
# wilgy: function to close the window and return the selected percentage.
def closeWindow():
    selected_value = current_value.get()
    selected_value = round(selected_value, 2)
    current_value.set(selected_value)
    print("Selected threshold: {}".format(selected_value))
    variants_percentage_selection.destroy()
    return selected_value
 
 
# wilgy: label for the slider
slider_label = ttk.Label(variants_percentage_selection, text='The percentage setting determines the minimum \n'
                                                             + 'occurrences of a process to be considered. \nUse the slider to make your selection:',
                         padding=20)
slider_label.grid(column=0, row=0, sticky='w')
 
# wilgy: sets the scale for the slider widget, i.e., 0.1 is 10 percent.
slider = ttk.Scale(variants_percentage_selection, from_=0.0, to=0.1, orient='horizontal',
                   command=slider_changed, variable=current_value)
slider.grid(column=1, row=0, ipadx=20)
 
# current value label
current_value_label = ttk.Label(variants_percentage_selection, text='Current Value:')
current_value_label.grid(row=1, columnspan=2, sticky='n', ipadx=10, ipady=10)
 
# value label
value_label = ttk.Label(variants_percentage_selection, text=get_current_value())
value_label.grid(row=2, columnspan=2, sticky='n')
 
# wilgy:clicking OK button will close the window
button = Button(variants_percentage_selection, text="Ok", fg='blue', command=closeWindow)
button.place(relx=0.5, rely=0.75, anchor=CENTER)
variants_percentage_selection.mainloop()
 
# *****************************************************************************
# End of window
# *****************************************************************************
 
# *****************************************************************************
# wilgy: This section builds a user interactive window to select what type of
#       algorithm to use for process mining.
# *****************************************************************************
 
 
miner_window = Tk()
miner_selection = IntVar()
 
 
# wilgy: function returning the value of miner selection
def minerValue():
    value = miner_selection.get()
    print("Selected miner: {}".format(value))
    return value
 
 
# wilgy: function to close miner threshold selection window. If no algorithm selected, default to 1 (DFG).
def closeMinerWindow():
    value = miner_selection.get()
    if value == 0:
        miner_selection.set(1)
    miner_window.destroy()
 
 
# wilgy: New window to select which miner to utilise
# sdhiraj
Label(miner_window, text='Select which process mining algorithm to utilise:').pack(pady=20)
Radiobutton(miner_window, text="Directly Follows Graph", variable=miner_selection, value=1, command=minerValue).pack()
Radiobutton(miner_window, text="Heuristics Miner", variable=miner_selection, value=2, command=minerValue).pack()
Radiobutton(miner_window, text="Alpha Miner", variable=miner_selection, value=3, command=minerValue).pack()
Radiobutton(miner_window, text="Inductive Miner", variable=miner_selection, value=4, command=minerValue).pack()
Button(miner_window, text="Ok", fg='blue', command=closeMinerWindow).pack(
    pady=20)  # wilgy:clicking OK button will close the window
 
# wilgy: Setting parameters of the GUI
miner_window.title('PM Algorithm selection')
miner_window.geometry("400x300+10+10")
miner_window.mainloop()
 
 
# *****************************************************************************
# End of window
# *****************************************************************************
 
# wilgy: function returns the full file path of the target filename
# (useful if users have saved file path in varying locations)
def find_files(filename, path):
    file = [f for f in glob.glob(path + '**/' + filename, recursive=True)]
    for f in file:
        return (f)
 
 
# wilgy: function converts csv to event log format, with relevant variables selected as keys.
# Also filters the eventlog to determine start activities and corresponding count of each start activity.
def import_pm4py(event_log):
    event_log = pm4py.format_dataframe(event_log, case_id='EpisodeNo', activity_key='Activity'
                                       , timestamp_key='EndTime', start_timestamp_key='EventTime')
    start_activities = pm4py.get_start_activities(event_log)
    end_activities = pm4py.get_end_activities(event_log)
    print("Number of unique start activities: {}".format(len(set(start_activities))))
    print("Number of unique end activities: {}".format(len(set(end_activities))))
    return event_log
 
 
# wilgy: function utilises pandas to import the csv and display the count of events and total cases.
def import_csv(file_path):
    event_log = pd.read_csv(file_path, sep=',')
    num_events = len(event_log)
    num_cases = len(event_log.EpisodeNo.unique())
    print("Number of events: {}\nNumber of cases: {}".format(num_events, num_cases))
    # wilgy: convert timeformats for PM4PY
    event_log = dataframe_utils.convert_timestamp_columns_in_df(event_log)
    return event_log
 
 
# wilgy: function to discover and view directly follows graph (DFG). Output as PDF.
def pm_dfg(event_log):
    dfg, start_activities, end_actvities = pm4py.discover_dfg(event_log)
    pm4py.view_dfg(dfg, start_activities, end_actvities, 'pdf')
    # sdhiraj:  converts to png and calls file_to_Algorithm_Outputs method
    pm4py.vis.save_vis_dfg(dfg, start_activities, end_actvities, 'dfg.png')
    file_to_Algorithm_Outputs('dfg.png')

#wilgy: from GGrossmann.
def pm_heuristics(df):
    print("Discover heuristics net ...")
    # https://pm4py.fit.fraunhofer.de/static/assets/api/2.2.18/pm4py.html?highlight=discover_heuristics_net#pm4py.discovery.discover_heuristics_net
    map = pm4py.discovery.discover_heuristics_net(df, current_value.get())
    # The map object is a HeuristicsNet
    print("Class name of variable map: " + map.__class__.__name__)
    print("Visualizing heuristics net ...")
    pm4py.view_heuristics_net(map, "pdf")
    # sdhiraj:  converts to png and calls file_to_Algorithm_Outputs method
    pm4py.vis.save_vis_heuristics_net(map, 'heuristics.png')
    #file_to_Algorithm_Outputs('heuristics.png')
 
 
# sdhiraj alpha miner algorithm containing petri net object and visualisation
def pm_alpha(event_log):
    print("Discover petri net ...")
    net, start_activities, end_activities = alpha_miner.apply(event_log)  # sdhiraj: The map object is a PetriNet
    print("Visualizing petri net ...")
    # https://pm4py.fit.fraunhofer.de/static/assets/api/2.2.10/pm4py.visualization.petri_net.html
    petri_net_viz = pm4py.visualization.petri_net.visualizer.apply(net, start_activities, end_activities)
    pm4py.visualization.petri_net.visualizer.view(petri_net_viz)
    # sdhiraj:  converts to png and calls file_to_Algorithm_Outputs method
    pm4py.vis.save_vis_petri_net(net, start_activities, end_activities, 'alpha.png')
    #dirname = os.path.dirname("alpha.png")
    #filename = os.path.join(dirname, 'Algorithm_Outputs')
 
# file_to_Algorithm_Outputs('alpha.png')
 
# sdhiraj: inductive miner algorithm and visualisation that depicts tree and calls pm_inductive_petri method
def pm_inductive(event_log):
    print("Discover inductive...")
    tree = inductive_miner.apply_tree(event_log)
    print("Visualizing inductive ...")
    inductive_viz = pt_visualizer.apply(tree)
    # tree visualisation
    pt_visualizer.view(inductive_viz)
    # sdhiraj:  converts to png and calls file_to_Algorithm_Outputs method
    pm4py.vis.save_vis_process_tree(tree, 'inductive_tree.png')
    #file_to_Algorithm_Outputs('inductive_tree.png')
 
    net, initial_marking, final_marking = pt_converter.apply(tree)
    parameters = {pm4py.visualization.petri_net.visualizer.Variants.FREQUENCY.value.Parameters.FORMAT: "png"}
    petri_net_viz = pm4py.visualization.petri_net.visualizer.apply(net, initial_marking, final_marking,
                                                                   parameters=parameters,
                                                                   variant=pm4py.visualization.petri_net.visualizer.Variants.FREQUENCY,
                                                                   log=event_log)
    # petrinet visualisation
    pm4py.visualization.petri_net.visualizer.view(petri_net_viz)
    # sdhiraj:  converts to png and calls file_to_Algorithm_Outputs method
    pm4py.vis.save_vis_petri_net(net, initial_marking, final_marking, 'inductive_petri_net.png')
    #file_to_Algorithm_Outputs('inductive_petri_net.png')
 
 
# sdhiraj:moves png file to Algorithm_Outputs folder
def file_to_Algorithm_Outputs(file_name):
    '''
    shutil.move(file_name, "Algorithm_Outputs")'''
 
 
 
# MAIN
df = import_pm4py(import_csv(find_files('log_dataset.csv', 'C:')))
 
#sdhiraj: Use for Episode Window User Interaction
episode_list = df["case:concept:name"].unique()
 
# Convert DataFrame object into an EventLog object (which is required for querying variants):
event_log = pm4py.convert_to_event_log(df)
# event_log = log_converter.apply(df)
# wilgy: filter variants experimenting
filter = pm4py.filter_variants_percentage(event_log, current_value.get())
 
# wilgy: Statistics - find the median case duration of the whole log
median_case_duration = pm4py.statistics.traces.generic.log.case_statistics.get_median_case_duration(event_log,
                                                                                                    parameters={
                                                                                                        pm4py.statistics.traces.generic.log.case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
print("Median case duration of the entire data set(days): {}".format(round(median_case_duration / 86400, 2)))
 
# wilgy: Statistics - find the median case duration of the filtered log
filtered_median_case_duration = pm4py.statistics.traces.generic.log.case_statistics.get_median_case_duration(filter,
                                                                                                             parameters={
                                                                                                                 pm4py.statistics.traces.generic.log.case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
print("Median case duration of the filtered data set(days): {}".format(round(filtered_median_case_duration / 86400, 2)))
 
#wilgy: save distribution graph for filtered dataset

pm4py.save_vis_events_distribution_graph(filter, 'distribution_graph.pdf', distr_type="months")
 
# wilgy: Call the selected method to produce respective process mining output.
# sdhiraj: added call for inductive and alpha miner
pmSelector = miner_selection.get()
print('pmSelector: {}'.format(pmSelector))
if pmSelector == 1:
    pm_dfg(filter)
if pmSelector == 2:
    pm_heuristics(filter)
if pmSelector == 3:
    pm_alpha(filter)
if pmSelector == 4:
    pm_inductive(filter)
 
# wilgy: Explore details of a single EpisodeID:
episodeID = input("Enter the EpisodeID #: ")
print("EpisodeID selection: {}".format(episodeID))
print()
 
# wilgy: create new data frame, containing only the selected EpisodeID
df2 = df.loc[df["case:concept:name"] == episodeID]
 
while len(df2) == 0:
    print("Selected EpisodeID does not exist. Please try again")
    episodeID = input("Enter the EpisodeID #: ")
    df2 = df.loc[df["case:concept:name"] == episodeID]
 
else:
    episode_event_log = pm4py.convert_to_event_log(df2)
    # wilgy: using median case duration for single episodeID to return int, rather than get all case durations which returns list.
    case_duration = pm4py.statistics.traces.generic.log.case_statistics.get_median_case_duration(episode_event_log,
            parameters={
                pm4py.statistics.traces.generic.log.case_statistics.Parameters.TIMESTAMP_KEY: 'time:timestamp'})
    # wilgy: formula to change result to day instead of seconds, rounding to 2 decimal places.
    case_duration = round(case_duration / 86400, 2)
    # print(df2)
    print("EpisodeNo {} contains {} events. The total case duration is {} days".format(episodeID, len(df2),
                                                                                       case_duration))
    
    #wilgy: save distribution graph for selected episodeNo, with file name including the specified episodeNo.
    pm4py.save_vis_events_distribution_graph(episode_event_log, 'distribution_graph_{}.pdf'.format(episodeID), distr_type="months")
 
#shiraj: Get dataframe with case duration and episode numbers
variant_df = case_statistics.get_variants_df_with_case_duration(df)
 
#sdhiraj: Determine episodeNo that has minimum case time from start to finish and duration
min_case_duration_info = variant_df.loc[variant_df['caseDuration'].idxmin()]
min_case_duration_episode = variant_df['caseDuration'].idxmin()
min_case_duration = variant_df['caseDuration'].min()
print(
    "EpisodeNo {} has the minimum case duration (case time from start to finish). The case time is {} or {} days.".format(
        min_case_duration_episode, min_case_duration, round(min_case_duration / 86400, 2)))
 
#sdhiraj: Determine episodeNo that has maximum case time from start to finish and duration
max_case_duration_info = variant_df.loc[variant_df['caseDuration'].idxmax()]
max_case_duration_episode = variant_df['caseDuration'].idxmax()
max_case_duration = variant_df['caseDuration'].max()
print(
    "EpisodeNo {} has the maximum case duration (case time from start to finish). The case time is {} or {} days.".format(
        max_case_duration_episode, max_case_duration, round(max_case_duration / 86400, 2)))
 
 
# ---------------------------------------------------------------------------------------------------------------------
# sdhiraj: This section builds a user interactive window to select percentage thresholds
# ---------------------------------------------------------------------------------------------------------------------
 
#sdhiraj: populate the drop down with matching episodes
def get_episodes(*args):
    search_str = episode_entry.get()  # user entered episode
    episode_listbox.delete(0, tk.END)  # Delete listbox episodes
    for element in episode_list:
        if (re.match(search_str, element, re.IGNORECASE)):
            episode_listbox.insert(tk.END, element)  # insert matching episodes to listbox
 
#sdhiraj: switch between entry and listbox for selection
def drop_down(epi_window):  # down arrow is clicked
    episode_listbox.focus()  # once down arrow is clicked, the focus moves to listbox
    episode_listbox.selection_set(0)  # defaults selection to first option after shifting focus
 
#sdhiraj: for listbox selection, once value is selected, the entry box will be updated
def update_window(epi_window):
    ind = int(epi_window.widget.curselection()[0])  # listbox selection position
    val = epi_window.widget.get(ind)
    entry_str.set(val)  # set value for entry string
    #print(entry_str.get())
    episode_listbox.delete(0, tk.END)  # Delete listbox elements
 
# Function for printing the
# selected listbox value(s)
def episodeInfoWindow():
    value = entry_str.get()
    value2 = episode_entry.get()
    #print(value)
    #print(value2)
    counter = 0
    #episode_df = pd.DataFrame (episode_list, columns = ['episode_no'])
    #episode_df['episode_no'] = episode_df['episode_no'].astype(str)
    for element in episode_list:
        if re.match(value, element, re.IGNORECASE) or re.match(value2, element, re.IGNORECASE): #if episode number matches episode in list
            #episode_window.destroy()
            episode_info_win= Toplevel(episode_window)
            episode_info_win.geometry("700x200")
            episode_info_win.title("Episode Information")
            df_2 = df.loc[df["case:concept:name"] == element]
            episode_event_log_2 = pm4py.convert_to_event_log(df_2)
            case_duration_2 = pm4py.statistics.traces.generic.log.case_statistics.get_median_case_duration(episode_event_log_2,
                                                                                                         parameters={
                                                                                                             pm4py.statistics.traces.generic.log.case_statistics.Parameters.TIMESTAMP_KEY: 'time:timestamp'})
            case_duration_2 = round(case_duration_2 / 86400, 2)
            # print(df2)
            string = "EpisodeID {} contains {} events. The case duration is {} days".format(episodeID, len(df_2),
                                                                                                         case_duration_2)
            Label(episode_info_win, text= string).pack()
            top_bu = tk.Button(episode_info_win, text="Finish", command=closeAll)
            #bu.grid(row=6, column=3)
            top_bu.pack()
            counter = 1
 
    if counter ==0:
        tk.messagebox.showerror("error", "try again")
    '''
    if counter == 0:
        title_l = tk.Label(text='Invalid Episode Number.Please try again.')  #Window Title
        title_l.grid(row=6, column=1)
        episode_listbox.delete(0, tk.END)
        episode_entry.delete(0, tk.END)
        title_l.config(text="")'''
 
    # if episodeNo matches list, then destroy window and open pop up with relevant info, else make a label that says that invalid episode number was inputted so try again
    #return value
 
#closes episode windows once "Finish" is clicked
def closeAll():
    episode_window.destroy()
 
 
# sdhiraj: Creating episode window for interaction with users.
episode_window = tk.Tk()
 
#sdhiraj: Customizing Episode Window and Title
episode_window.geometry("200x350")  # Window Size
episode_window.title("Episode No Info")  # Adding a window label
title_label = tk.Label(text='Episode No Info')  #Window Title
title_label.grid(row=1, column=2)
 
#sdhiraj: Listbox for Episode No which acts as a drop down list for Episode No
episode_listbox = tk.Listbox(episode_window, height=15, relief='flat', bg='SystemButtonFace', highlightcolor='SystemButtonFace')
episode_listbox.grid(row=4, column=2)
 
#sdhiraj: Textbox for Episode No so user can type Episode No
entry_str = tk.StringVar()
episode_entry = tk.Entry(episode_window, textvariable=entry_str)  # textbox for episode entry.
episode_entry.grid(row=3, column=2)
 
#sdhiraj: binding functions to input fields based on type of user interaction
episode_entry.bind('<Down>', drop_down)  # down arrow key is pressed
episode_listbox.bind('<Return>', update_window)  # return key is pressed
episode_listbox.bind('<Double-1>', update_window)
entry_str.trace('w', get_episodes)  
 
#sdhiraj: Button once Episode No is selected. This will call function to open up another pop up with more Episode Info
bu = tk.Button(episode_window, text="Submit", command=episodeInfoWindow)
bu.grid(row=5, column=2)
 
#sdhiraj: Keeps episode window open
episode_window.mainloop()
 
# ----------------------------------------------------------------------------------------------------------------------
# sdhiraj: End of Episode Selection window
# ---------------------------------------------------------------------------------------------------------------------