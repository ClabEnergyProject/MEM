# -*- coding: utf-8 -*-

"""

Save_Basic_Results.py

save basic results for the simple energy model
    
"""

# -----------------------------------------------------------------------------


import os
import copy
import numpy as np
import csv
import datetime
import contextlib
import pickle
import utilities
import cvxpy
import pandas as pd

       
#%%
# save scalar results for all cases
def save_basic_results(case_dic, tech_list, constraints,prob_dic,capacity_dic,dispatch_dic):
    
    """
    Save scalar information to csv/excel file, one column per technology, one field per row
    -- Begin with case dependent information duplicated for each row.
    -- Include values from tech_list where values are scalars, take means where values are vectors
    -- Include values from capacity_dic, dispatch_dic, and prob, taking means where values are vectors.
    
    Save vector information to csv/excel file, one column per field, one row per time step.
    -- question regarding how best to format headers.
    
    """
    
    #--------------------------------------------------------------------------
    
    # generate scalar outputs per case
    case_output_dic = {} # one scalar item per element per case
    
    for key in case_dic:
        case_output_dic[key] = case_dic[key]
        
    temp_dic = flatten_dic(meanify(prob_dic))
    for key in temp_dic:
        case_output_dic[key] = temp_dic[key]
   
    #--------------------------------------------------------------------------
    
    tech_output_dic_list = list(map(meanify,tech_list))
    
    for i in range(len(tech_output_dic_list)):
        dic_sub = tech_output_dic_list[i]
        tech_name = dic_sub['tech_name']
        if 'series' in dic_sub:
            dic_sub[tech_name + ' series'] = np.average(dic_sub['series'])
        if dic_sub['tech_name'] in capacity_dic:
            dic_sub[tech_name + ' capacity'] = capacity_dic[dic_sub['tech_name']]
        if dic_sub['tech_name'] in dispatch_dic:
            dic_sub[tech_name + ' dispatch'] = np.average(dispatch_dic[dic_sub['tech_name']])
        tech_output_dic_list[i] = dic_sub
            
  
    #--------------------------------------------------------------------------
    
    num_time_periods = case_dic['num_time_periods']
    time_output_dic = {} # one time vector per keyword
    time_output_dic['time_index'] = np.array(range(num_time_periods))
    for item in tech_list:
        tech_name = item['tech_name']
        if 'series' in item:
            time_output_dic[tech_name + ' series'] = item['series']
    node_price_dic = prob_dic['node_price']
    for node in node_price_dic:
        time_output_dic[node+' price'] = node_price_dic[node]
    for item in dispatch_dic:
        time_output_dic[item] = dispatch_dic[item]

    #--------------------------------------------------------------------------
    
    case_df = pd.DataFrame(list(case_output_dic.items()))
    tech_df = pd.DataFrame(tech_output_dic_list)
    time_df = pd.DataFrame(time_output_dic)
    
    output_path = case_dic['output_path']
    case_name = case_dic['case_name']
    output_folder = output_path + "/" + case_name
    today = datetime.datetime.now()
    todayString = str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2) + '-' + \
        str(today.hour).zfill(2) + str(today.minute).zfill(2) + str(today.second).zfill(2)
    
    output_file_name = case_name + '_vector_' + todayString
    output_file_path_name = output_folder + "/" + output_file_name + '.xlsx'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    writer = pd.ExcelWriter(output_file_path_name, engine = 'xlsxwriter')
    case_df.to_excel(writer, sheet_name = 'case')  
    tech_df.to_excel(writer, sheet_name = 'tech')
    time_df.to_excel(writer, sheet_name = 'time') 
    writer.save()
    
    verbose = case_dic['verbose']       
    if verbose: 
        print ( 'file written: ' + output_file_path_name )
    
    return case_output_dic,tech_output_dic_list,time_output_dic

    
#%%    
    
def temp():
    output_path = case_dic['output_path']
    case_name = case_dic['case_name']
    output_folder = output_path + "/" + case_name
    today = datetime.datetime.now()
    todayString = str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2) + '-' + \
        str(today.hour).zfill(2) + str(today.minute).zfill(2) + str(today.second).zfill(2)
    
    output_file_name = case_name + '_scalar_' + todayString
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    with contextlib.closing(open(output_folder + "/" + output_file_name + '.csv', 'w',newline='')) as output_file:
        writer = csv.writer(output_file)
        writer.writerows(output_scalar_array)
        output_file.close()
        
 
    if verbose: 
        print ( 'file written: ' + output_file_name + '.csv')
        

        
    #%% output vector information
     
    output_path = case_dic['output_path']
    case_name = case_dic['case_name']
    output_folder = output_path + "/" + case_name
    today = datetime.datetime.now()
    todayString = str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2) + '-' + \
        str(today.hour).zfill(2) + str(today.minute).zfill(2) + str(today.second).zfill(2)
    
    output_file_name = case_name + '_vector_' + todayString
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    with contextlib.closing(open(output_folder + "/" + output_file_name + '.csv', 'w',newline='')) as output_file:
        writer = csv.writer(output_file)
        writer.writerows(output_vector_array)
        output_file.close()
        
    if verbose: 
        print ( 'file written: ' + output_file_name + '.csv')

#%%
# flatten dictionary of dictionaries to dictionary (1 level)
def flatten_dic(dic_in):
    dic_out = {}
    for item in dic_in:
        if dict != type(dic_in[item]):
            dic_out[item] = dic_in[item]
        else: # type is dict
            for sub_item in dic_in[item]:
                dic_out[item + ' ' + sub_item ] = dic_in[item][sub_item]
    return dic_out
    

#%%
# take mean if vector else return value
        
def meanify(dic_in):
    dic_out = copy.deepcopy(dic_in)
    for item in dic_out:
        if np.ndarray == type(dic_out[item]):
            dic_out[item] = np.average(dic_out[item])
        elif dict == type(dic_out[item]):
            dic_out[item] = meanify(dic_out[item])
    return dic_out

#%%
def robust_dic(dic, key):
    if key in dic:
        res = dic[key]
    else:
        res = ""  # Default value if missing key
    return res


#%%
def pickle_raw_results( case_dic, result_dic ):
    
    output_path = case_dic['OUTPUT_PATH']
    case_name = case_dic['case_name']
    
    output_folder = output_path + '/' + case_name
    
    output_file_name = case_name + '-' + case_name + '.pickle'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    with open(output_folder + "/" + output_file_name, 'wb') as db:
        pickle.dump([case_dic,result_dic], db, protocol=pickle.HIGHEST_PROTOCOL)

#%%
def read_pickle_raw_results( case_dic ):
    
    output_path = case_dic['OUTPUT_PATH']
    case_name = case_dic['case_name']
    
    output_folder = output_path + '/' + case_name
    
    output_file_name = case_name + '-' + case_name + '.pickle'
    
    with open(output_folder + "/" + output_file_name, 'rb') as db:
        [case_dic,case_dic,result_dic] = pickle.load( db )
    
    return result_dic

#%%
def pickle_raw_results_list( case_dic, case_dic_list, result_dic_list ):
    
    output_path = case_dic['OUTPUT_PATH']
    case_name = case_dic['case_name']
    output_folder = output_path + '/' + case_name
    output_file_name = case_name + '.pickle'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    with open(output_folder + "/" + output_file_name, 'wb') as db:
        pickle.dump([case_dic,case_dic_list,result_dic_list], db, protocol=pickle.HIGHEST_PROTOCOL)

#%%
def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

#%%
# save results by case
def save_list_of_vector_results_as_csv( case_dic, case_dic_list, result_dic_list ):
    
    for idx in range(len(result_dic_list)):
        
        case_dic = case_dic_list[idx]
        result_dic = result_dic_list[idx]
        save_vector_results_as_csv( case_dic, case_dic, result_dic )
        

#%%
# save results by case
def save_vector_results_as_csv( case_dic,  result_dic ):
    
    output_path = case_dic['OUTPUT_PATH']
    case_name = case_dic['case_name']
    output_folder = output_path + '/' + case_name

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
             
    if len(case_dic['WIND_SERIES']) == 0:
        case_dic['WIND_SERIES'] = ( 0.*np.array(case_dic['DEMAND_SERIES'])).tolist()
    if len(case_dic['SOLAR_SERIES']) == 0:
        case_dic['SOLAR_SERIES'] = ( 0.*np.array(case_dic['DEMAND_SERIES'])).tolist()
             
    if len(case_dic['WIND2_SERIES']) == 0:
        case_dic['WIND2_SERIES'] = ( 0.*np.array(case_dic['DEMAND_SERIES'])).tolist()
    if len(case_dic['SOLAR2_SERIES']) == 0:
        case_dic['SOLAR2_SERIES'] = ( 0.*np.array(case_dic['DEMAND_SERIES'])).tolist()
    
    if len(case_dic['CSP_SERIES']) == 0:
        case_dic['CSP_SERIES'] = ( 0.*np.array(case_dic['DEMAND_SERIES'])).tolist()
    
    header_list = []
    vector_values_list = []
    
    header_list += ['time (hr)']
    vector_values_list.append( np.arange(len(case_dic['DEMAND_SERIES'])))
    
    header_list += ['demand (kW)']
    vector_values_list.append( case_dic['DEMAND_SERIES'] )
    
    header_list += ['solar capacity factor (-)']
    vector_values_list.append( np.array(case_dic['SOLAR_SERIES']))    
    
    header_list += ['wind capacity factor (-)']
    vector_values_list.append( np.array(case_dic['WIND_SERIES']))

    header_list += ['solar2 capacity factor (-)']
    vector_values_list.append( np.array(case_dic['SOLAR2_SERIES']))    
    
    header_list += ['wind2 capacity factor (-)']
    vector_values_list.append( np.array(case_dic['WIND2_SERIES']))

    header_list += ['dispatch natgas (kW)']
    vector_values_list.append( result_dic['DISPATCH_NATGAS'].flatten() )
    
    header_list += ['dispatch natgas ccs (kW)']
    vector_values_list.append( result_dic['DISPATCH_NATGAS_CCS'].flatten() )
    
    header_list += ['dispatch solar (kW)']
    vector_values_list.append( result_dic['DISPATCH_SOLAR'].flatten() ) 
    
    header_list += ['dispatch wind (kW)']
    vector_values_list.append( result_dic['DISPATCH_WIND'].flatten() )
    
    header_list += ['dispatch solar2 (kW)']
    vector_values_list.append( result_dic['DISPATCH_SOLAR2'].flatten() ) 
    
    header_list += ['dispatch wind2 (kW)']
    vector_values_list.append( result_dic['DISPATCH_WIND2'].flatten() )
    
    header_list += ['dispatch nuclear (kW)']
    vector_values_list.append( result_dic['DISPATCH_NUCLEAR'].flatten() )
    
    header_list += ['dispatch to storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_TO_STORAGE'].flatten() )
    
    header_list += ['dispatch from storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_FROM_STORAGE'].flatten() )  # THere is no FROM in dispatch results

    header_list += ['energy storage (kWh)']
    vector_values_list.append( result_dic['ENERGY_STORAGE'].flatten() )
    
    header_list += ['dispatch to storage2 (kW)']
    vector_values_list.append( result_dic['DISPATCH_TO_STORAGE2'].flatten() )
    
    header_list += ['dispatch from storage2 (kW)']
    vector_values_list.append( result_dic['DISPATCH_FROM_STORAGE2'].flatten() )  # THere is no FROM in dispatch results

    header_list += ['energy storage2 (kWh)']
    vector_values_list.append( result_dic['ENERGY_STORAGE2'].flatten() )
    
    header_list += ['dispatch to pgp storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_TO_PGP_STORAGE'].flatten() )
    
    header_list += ['dispatch pgp storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_FROM_PGP_STORAGE'].flatten() )

    header_list += ['energy pgp storage (kWh)']
    vector_values_list.append( result_dic['ENERGY_PGP_STORAGE'].flatten() )
    
    header_list += ['dispatch to csp storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_TO_CSP_STORAGE'].flatten() )  # THere is no FROM in dispatch results
    
    header_list += ['dispatch from csp storage (kW)']
    vector_values_list.append( result_dic['DISPATCH_FROM_CSP'].flatten() )  # THere is no FROM in dispatch results

    header_list += ['energy csp storage (kWh)']
    vector_values_list.append( result_dic['ENERGY_CSP_STORAGE'].flatten() )
    
    header_list += ['dispatch unmet demand (kW)']
    vector_values_list.append( result_dic['DISPATCH_UNMET_DEMAND'].flatten() )
    
    header_list += ['cutailment solar (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_SOLAR'].flatten() )
    
    header_list += ['cutailment wind (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_WIND'].flatten() )
    
    header_list += ['cutailment solar2 (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_SOLAR2'].flatten() )
    
    header_list += ['cutailment wind2 (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_WIND2'].flatten() )
    
    header_list += ['cutailment csp (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_CSP'].flatten() )
    
    header_list += ['cutailment nuclear (kW)']
    vector_values_list.append( result_dic['CURTAILMENT_NUCLEAR'].flatten() )
    
    header_list += ['price ($/kWh)']
    vector_values_list.append( result_dic['PRICE'].flatten() )
     
    output_file_name = case_dic['case_name']+'-'+case_dic['CASE_NAME']
    
    with contextlib.closing(open(output_folder + "/" + output_file_name + '.csv', 'w',newline='')) as output_file:
        writer = csv.writer(output_file)
        writer.writerow(header_list)
        writer.writerows((np.asarray(vector_values_list)).transpose())
        output_file.close()
 
