# -*- codiNatgas: utf-8 -*-
'''
This code reads a file called 'case_input.csv' which is assumed to exist in the directory in which the code is running.

It generates a result containing <case_dic> and <case_dic_list>

<case_dic> is a dictionary of values applied to cases
    
<case_dic> contains:
    
    
<case_dic_list> is a list of dictionaries. Each element in that list corresponds to a different case to be run.

    'data_path' -- PATH TO DATA FILES
    'output_path' -- STRING CONTAINING NAME OF OUTPUT DIRECTORY


'''

import csv
import numpy as np
import utilities
import datetime


                                               
#%% 

def preprocess_input(case_input_path_filename):
    # This is the highest level function that reads in the case input file
    # and generated <case_dic_list> from this input.
        
    # -----------------------------------------------------------------------------
    # Recognized keywords in case_input.csv file
    
    keywords_logical = ['verbose']
    
    keywords_str = ['case_name','data_path','output_path',
                    'tech_name','tech_type','node_to','node_from',
                    'series_file',
                    'time_start','time_end','notes']

    keywords_int = ['year_start','month_start','day_start','hour_start',
                    'year_end','month_end','day_end','hour_end']
    
    keywords_real = ['numerics_scaling','fixed_cost','var_cost','charging_time'
                     'efficiency','decay_rate']
            
    tech_keywords = {}
    tech_keywords['demand'] = ['tech_name','tech_type','node_from','series_file']
    tech_keywords['curtailment'] = ['tech_name','tech_type','node_from','var_cost']
    tech_keywords['lost_load'] = ['tech_name','tech_type','node_to','var_cost']
    tech_keywords['generator'] = ['tech_name','tech_type','node_to','series_file','fixed_cost','var_cost']
    tech_keywords['fixed_generator'] = ['tech_name','tech_type','node_to','series_file','fixed_cost']
    tech_keywords['transfer'] = ['tech_name','tech_type','node_to','node_from','fixed_cost','var_cost','efficiency']
    tech_keywords['transmission'] = ['tech_name','tech_type','node_to','node_from','fixed_cost','var_cost','efficiency']
    tech_keywords['storage'] = ['tech_name','tech_type','node_to','node_from','fixed_cost','var_cost','efficiency','charging_time','decay_rate']
    
                                              
#%% 
    # Read in case data
    
    # <import_case_input> reads in the file from the csv file, but does not parse
    # this data.
    case_data,tech_data = import_case_input(case_input_path_filename)

    # -----------------------------------------------------------------------------
    # the basic logic here is that if a keyword appears in the 'global'
    # section, then it is used for all cases if it is used in the 'case' section
    # then it applies to that particular case.
        
    # Parse global data
    case_dic = {}
    
    #------convert file input to dictionary of global data ---------
    for list_item in case_data:
        input_key = list_item[0].lower()
        input_value = list_item[1]
        if input_key in keywords_str:
            case_dic[input_key] = input_value
        elif input_key in keywords_int:
            case_dic[input_key] = int(input_value)
        elif input_key in keywords_real:
            case_dic[input_key] = float(input_value)
        elif input_key in keywords_logical:
            case_dic[input_key] = literal_to_boolean(input_value)
    
    # set defaults
    if not 'verbose' in case_dic:
        case_dic['verbose'] = True
    if not 'numerics_scaling' in case_dic:
        case_dic['numerics_scaling'] = 1.
        
    verbose = case_dic['verbose']     
    
    start_time = datetime.datetime.now()    # timer starts
    if case_dic['verbose']:
        print ('    start time = ',start_time)
    
    num_time_periods = (
            24 * (
            datetime.date(case_dic['year_end'],case_dic['month_end'],case_dic['day_end'])-
            datetime.date(case_dic['year_start'],case_dic['month_start'],case_dic['day_start'])
            ).days +
            (case_dic['hour_end'] - case_dic['hour_start'] ) + 1
            ) 
    case_dic['num_time_periods'] = num_time_periods
    
    # -----------------------------------------------------------------------------
    # -----------------------------------------------------------------------------
    # Read in tech data

    tech_keys = tech_data[0] # list of keywords for this case
    idx_tech_type = tech_keys.index('tech_type')
        
    # Now each element of case_transpose is the potential keyword followed by data
    tech_list = []
    
    # now add global variables to case_dic
    for data_row in tech_data[1::]:
        tech_dic = {}
        
        tech_type = data_row[idx_tech_type]
    
        for keyword in tech_keywords[tech_type]:
            if keyword in tech_keys:
                idx_key = tech_keys.index(keyword)
                if len(data_row[idx_key].strip()) > 0: # do not add null strings
                    if keyword in keywords_str:
                            tech_dic[keyword] = data_row[idx_key]
                    elif keyword in keywords_int:
                        tech_dic[keyword] = int(data_row[idx_key])
                    elif keyword in keywords_real:
                        tech_dic[keyword] = float(data_row[idx_key])
                    elif keyword in keywords_logical:
                        tech_dic[keyword] = literal_to_boolean(data_row[idx_key])
            
        tech_list.append(tech_dic)

    #%% 
    # Now add the time series to tech_list
    
    for tech_dic in tech_list:
        if 'series_file' in tech_dic:
            
            series = read_csv_dated_data_file(
                    case_dic['year_start'],
                    case_dic['month_start'],
                    case_dic['day_start'],
                    case_dic['hour_start'],
                    case_dic['year_end'],
                    case_dic['month_end'],
                    case_dic['day_end'],
                    case_dic['hour_end'],
                    case_dic['data_path'],
                    tech_dic['series_file']
                    )

            tech_dic['series'] = series

    #%%
        
    end_time = datetime.datetime.now()    # timer starts
    if case_dic['verbose']:
        print ('    end time = ',end_time)
        print ('    elapsed time = ',end_time - start_time)

    return case_dic,tech_list

#%%

def import_case_input(case_input_path_filename):
    # Import case_input.csv file from local directory.
    # return 2 objects: param_list, and case_list
    # <param_list> contains datarmation that is true for all cases in the set of runs
    # <case_list> contains datarmation that is true for a particular case
    
    # first open the file and define the reader
    f = open(case_input_path_filename)
    rdr = csv.reader(f)
    
    #Throw away all lines up to and include the line that has 'CASE' in the first cell of the line
    while True:
        line = next(rdr)
        if line[0] == 'CASE_DATA':
            break
    
    # Now take all non-blank lines until 'TECH_DATA'
    case_data = []
    while True:
        line = next(rdr)
        if line[0] == 'TECH_DATA':
            break
        if line[0] != '':
            case_data.append(line[0:2])
            
    # Now take all non-blank lines until 'END_DATA'
    tech_data = []
    while True:
        line = next(rdr)
        if line[0] == 'END_CASE_DATA':
            break
        if line[0] != '':
            tech_data.append(line)
            
    return case_data,tech_data


#%% 

def read_csv_dated_data_file(start_year,start_month,start_day,start_hour,
                             end_year,end_month,end_day,end_hour,
                             data_path, data_filename):
    
    # turn dates into yyyymmddhh format for comparison.
    # Assumes all datasets are on the same time step and are not missing any data.
    start_hour = start_hour + 100 * (start_day + 100 * (start_month + 100* start_year)) 
    end_hour = end_hour + 100 * (end_day + 100 * (end_month + 100* end_year)) 
      
    path_filename = data_path + '/' + data_filename
    
    data = []
    with open(path_filename) as fin:
        # read to keyword 'BEGIN_DATA' and then one more line (header line)
        data_reader = csv.reader(fin)
        
        #Throw away all lines up to and include the line that has 'BEGIN_GLOBAL_DATA' in the first cell of the line
        while True:
            line = next(data_reader)
            if line[0] == 'BEGIN_DATA':
                break
        # Now take the header row
        line = next(data_reader)
        
        # Now take all non-blank lines
        data = []
        while True:
            try:
                line = next(data_reader)
                if any(field.strip() for field in line):
                    data.append([int(line[0]),int(line[1]),int(line[2]),int(line[3]),float(line[4])])
                    # the above if clause was from: https://stackoverflow.com/questions/4521426/delete-blank-rows-from-csv
            except:
                break
            
    data_array = np.array(data) # make into a numpy object
    
    hour_num = data_array[:,3] + 100 * (data_array[:,2] + 100 * (data_array[:,1] + 100* data_array[:,0]))   
    

    series = [item[1] for item in zip(hour_num,data_array[:,4]) if item[0]>= start_hour and item[0] <= end_hour]
    
    return np.array(series).flatten() # return flatten series

                                               
#%% 

def literal_to_boolean(text):
    if len(text.strip()) > 0:
        if (text.strip())[0]=='T' or (text.strip())[0]=='t':  # if first non-space character is T or t, then True, else False
            answer = True
        else:
            answer = False
    else:
        answer = True # Missing value is taken to be true
    return answer
