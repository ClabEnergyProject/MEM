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
from utilities import list_of_dicts_to_dict_of_lists, unique_list_of_lists
import cvxpy

       
#%%
# save scalar results for all cases
def save_basic_results(case_dic, tech_list, constraints,prob,capacity_dic,dispatch_dic):
    
    verbose = case_dic['verbose']
    
    # conert everything to numpy arrays
    
    case_scalar_output_dic = copy.deepcopy(capacity_dic)
    case_vector_output_dic = copy.deepcopy(dispatch_dic)
    
    scalar_header_list = []
    scalar_values_list = []
        
    vector_header_list = []
    vector_values_list = []
    
    for item in capacity_dic:
        val = case_scalar_output_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            case_scalar_output_dic[item] = [case_scalar_output_dic[item].value]
    
    for item in case_dic:
        scalar_header_list += [item]
        scalar_values_list += [case_dic[item]]
    
    for item in tech_list:
        scalar_header_list += [item]
        for key in item:
            scalar_header_list += [item['node'] + '-' + key]
            if key == 'series':
                scalar_values_list += [np.average(item['series'])]
                vector_header_list += [item['tech_name']+'-'+key]
                vector_values_list += [item[key]]
            else:
                scalar_values_list += [item[key]]
   
    for item in case_vector_output_dic:
        val = case_vector_output_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            case_scalar_output_dic[item] = [np.average(case_vector_output_dic[item].value)]
    
    for item in case_scalar_output_dic:
        scalar_header_list += [item]
        scalar_values_list += [case_scalar_output_dic[item]]

    
    for item in case_vector_output_dic:
        vector_header_list += [item]
        vector_values_list += [case_vector_output_dic[item]]        
    
    for item in case_vector_output_dic:
        val = case_vector_output_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            case_vector_output_dic[item] = case_vector_output_dic[item].value
            if type(case_vector_output_dic[item])== cvxpy.expressions.variable.Variable:
                case_scalar_output_dic[item] = np.average(case_vector_output_dic[item].value)
            else:
                case_scalar_output_dic[item] = np.average(case_vector_output_dic[item])
    output_scalar_array = np.array(scalar_values_list).T.tolist()
    output_scalar_array.insert(0,scalar_header_list)    
    output_scalar_array = np.array(output_scalar_array).T.tolist()
    
    print (output_scalar_array)
    
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
    case_vector_output_dic = copy.deepcopy(dispatch_dic)
        
    vector_header_list = []
    vector_values_list = []
    
    for item in case_vector_output_dic:
        vector_header_list += item
        vector_values_list += [case_vector_output_dic[item] ]       
    
    for item in case_vector_output_dic:
        val = case_vector_output_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            case_vector_output_dic[item] = case_vector_output_dic[item].value
            case_scalar_output_dic[item] = np.average(case_vector_output_dic[item])
   
    
    output_vector_array = np.array(vector_values_list).T.tolist()
    output_vector_array.insert(0,vector_header_list)    
    output_vector_array = np.array(output_vector_array).T.tolist()
    
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
 
