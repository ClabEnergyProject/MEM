# -*- codiNatgas: utf-8 -*-
'''
  Top level function for the Simple Energy Model Ver 1.
  
  The main thing a user needs to do to be able to run this code from a download
  from github is to make sure that <case_input_path_filename> points to the 
  appropriate case input file.
  
  The format of this file is documented in the file called <case_input.csv>.
  
  If you are in Spyder, under the Run menu you can select 'configuration per File' Fn+Ctrl+F6
  and enter the file name of your input .csv file, e.g., Check 'command line options'
  and enter ./case_input_base_190716.csv
  
'''

from Preprocess_Input import preprocess_input

from Core_Model import core_model
from Extract_Cvxpy_Output import extract_cvxpy_output
from Save_Basic_Results import save_basic_results
import sys

from shutil import copy2
import os
 
# directory = 'D:/M/WORK/'
#root_directory = '/Users/kcaldeira/Google Drive/simple energy system model/Kens version/'
#whoami = subprocess.check_output('whoami')
#if whoami == 'kcaldeira-carbo\\kcaldeira\r\n':
#    case_input_path_filename = '/Users/kcaldeira/Google Drive/git/SEM-1/case_input.csv'
if len(sys.argv) == 1:
    #case_input_path_filename = './case_input.csv'
    case_input_path_filename = './case_input_example.csv'
else:
    case_input_path_filename = sys.argv[1]

# -----------------------------------------------------------------------------
# =============================================================================

print ('Macro_Energy_Model: Pre-processing input')
case_dic,tech_list = preprocess_input(case_input_path_filename)

# -----------------------------------------------------------------------------

# copy the input data file to the output folder

output_folder = case_dic['output_path'] + '/' + case_dic['case_name']

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    
try:
    copy2(case_input_path_filename, output_folder)
except:
    print ('case input file '+case_input_path_filename+' not copied. Perhaps it does not exist. Perhaps it is open and cannot be overwritten.')

# -----------------------------------------------------------------------------

print ('Macro_Energy_Model: Executing core model')
#global_results_dic, decision_dic_list = core_model (case_dic, tech_list)
constraint_list,cvxpy_constraints,cvxpy_prob,cvxpy_capacity_dic,cvxpy_dispatch_dic    = core_model (case_dic, tech_list)

# constraints,prob,capacity_dic,dispatch_dic = extract_cvxpy_output(cvxpy_constraints,cvxpy_prob,cvxpy_capacity_dic,cvxpy_dispatch_dic )
prob_dic,capacity_dic,dispatch_dic = extract_cvxpy_output(case_dic,tech_list,constraint_list,
                cvxpy_constraints,cvxpy_prob,cvxpy_capacity_dic,cvxpy_dispatch_dic )

print ('Simple_Energy_Model: Saving basic results')
# Note that results for individual cases are output from core_model_loop
save_basic_results(case_dic, tech_list, constraints,prob_dic,capacity_dic,dispatch_dic)

 