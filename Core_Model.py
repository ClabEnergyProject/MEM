# -*- coding: utf-8 -*-

#
'''

File name: Core_Model.py

Macro Energy Model ver. 2.0

This is the heart of the Macro Energy Model. 

Core computation code for the Macro Energy Model

This code takes two inputs:

1. A list of dictionaries in the form created by Process_Input.py.
2. A list of global (case independent) values to be used in solving the model.

Each dictionary in the list represents one technology (or demand etc) that 
can participate in the cost-optimal energy system.

The code uses these dictionary values to define a model for cvxpy to optimize.

Their are two basic elements in the model definition:

i. Technologies (which can also be generalized to include things like demand).
ii. Nodes (which provide inputs to or receive outputs from a technology)

Every technology can have inputs from or outputs to a node.

'Demand' would be an example of a "technology" that receives input but has no output.
'Wind' would be an example of a technology that produces output but has no input (although
the system is flexible enough that you could define the wind resource as the technology
has no input and have the wind resource going to a node, and then the wind turbines picking
up its input from that node.

Each technology creates capacity and/or dispatch decision variables.
Each node creates a constraining balancing equation requiring inputs to equal outputs.

A philosophic concept underlying this code is that it outputs primary output variables only.
Derived variables such as curtailments are computed in Process_Results.py.

Note that the naming convention for variables and functions are:
    
    lowercase with words separated by underscores as necessary to improve readability.
    https://www.python.org/dev/peps/pep-0008/
    
--------------------

Keywords in tech_dic are

tech_name (required) character string name of technology
node (optional) character string name of node
node_from (optional) character string name of node
fixed_cost (required if capacity decision) real number
var_cost (required if dispatch decision) real number

'''
#%%

import cvxpy as cvx
import time, datetime
import numpy as np


#%% Conceptual discussion of model code
"""
Taxonomies are tools, and so not right or wrong, but more useful or less useful.

For the purposes of this routine, we will use a high level taxonomy based on
the number of capacity decisions (one decision per simulation) and number of
dispatch decisions (one decision per time step).

It really doesn't matter whether someone wants to represent, for example, PGP
as three independent technologies vs one technology with multiple decisions.
The former approach will accomodate flexibility whereas the latter approach
may promote simplicity. In either case, this structure should accomodate both
approaches.



"""
#%% Define main code for Core_Model

def core_model(case_dic, tech_list):

    start_time = datetime.datetime.now()    # timer starts
    if case_dic['verbose']:
        print ('    start time = ',start_time)

    # Initialize variables to be used later
    fnc2min = 0.0
    constraints = []
    constraint_list = []
    node_balance = {} # dictionary of load balancing values; constrained to equal zero.
    # NOTE: node_names = node_balance.keys()     after this code runs.
    capacity_dic = {} # dictionary of capacity decision variables
    dispatch_dic = {} # dictionary of dispatch decision variables for inflow to tech
    
    num_time_periods = case_dic['num_time_periods']
                  
    """
    For the purposes of this routine, we will use a high level taxonomy based on
    the number of capacity decisions (one decision per simulation) and number of
    dispatch decisions (one decision per time step).
    
    <tech_type> is one of:
        'fixed_generator', 
        'generator', 
        'curtailment', 
        'lost_load', 
        'storage', or 
        'transfer' (unidirectional) or 'transmission' (bidirectional)

    """
  
    #loop through dics in tech_list
    for tech_dic in tech_list:

        tech_name = tech_dic['tech_name']
        tech_type = tech_dic['tech_type']
        
        # check the input node_to
        if 'node_to' in tech_dic:
            node_to = tech_dic['node_to']
            if not node_to in node_balance.keys():
                node_balance[node_to] = np.zeros(num_time_periods)
        
        # check the output node
        if 'node_from' in tech_dic:
            node_from = tech_dic['node_from']
            if not node_from in node_balance.keys():
                node_balance[node_from] = np.zeros(num_time_periods)

        #----------------------------------------------------------------------
        # demand (n_capacity = 0 and n_dispatch = 0 and n_dispatch = 0)
        #  Assumed to be demand, if series is available assume
        #  it is energy sink else assume energy sink of 1 kW.

        if tech_type == 'demand':
            if 'series' in tech_dic:
                dispatch = tech_dic['series']
            else:
                dispatch = np.ones(num_time_periods)
            dispatch_dic[tech_name] = dispatch
            # note that dispatch from a node is regarded as negative influence on that node
            node_balance[node_from] += - dispatch

        #----------------------------------------------------------------------
        # unmet demand 
        # (n_capacity = 0 and n_dispatch = 0 and n_dispatch = 1)
        # Assumed to be unmet demand (lost load) with variable cost
        
        elif tech_type == 'lost_load':
            dispatch = cvx.Variable(num_time_periods) 
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            dispatch_dic[tech_name] = dispatch
            node_balance[node_to] += dispatch # note that lost load is like a phantom source of pure variable capacity
            fnc2min +=  cvx.sum(dispatch * tech_dic['var_cost'])

        #----------------------------------------------------------------------
        # generic curtailment
        # (n_capacity = 0 and n_dispatch = 1 and n_dispatch = 0)
        # Assumed to be curtailment
        
        elif tech_type == 'curtailment':
            dispatch = cvx.Variable(num_time_periods) 
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            dispatch_dic[tech_name] = dispatch
            node_balance[node_from] += - dispatch
            if 'var_cost' in tech_dic: # if cost of curtailment
                fnc2min +=  cvx.sum(dispatch * tech_dic['var_cost'])
                
        #----------------------------------------------------------------------
        # non-curtailable generator 
        # (n_capacity = 1 and n_dispatch = 0 and n_dispatch = 1)
        # If time series is available, it will be assumed to be output per unit
        #  capacity.
        
        elif tech_type == 'fixed_generator':
            capacity = cvx.Variable(1)
            constraints += [ capacity >= 0 ]
            constraint_list += [tech_name + ' capacity_ge_0']
            if 'series' in tech_dic:
                dispatch = capacity * tech_dic['series']
            else:
                dispatch = capacity
                
            capacity_dic[tech_name] = capacity
            
            node_balance[node_to] += dispatch
            fnc2min += capacity * tech_dic['fixed_cost'] * num_time_periods

        #----------------------------------------------------------------------
        # curtailable generator
        # (n_capacity = 1 and n_dispatch = 0 and n_dispatch = 1)
        # Assumed to be non-curtailable generator, if time series
        # is available, it will be assumed to be output per unit capacity.
        
        elif tech_type == 'generator':
            capacity = cvx.Variable(1)
            dispatch = cvx.Variable(num_time_periods) 
            constraints += [ capacity >= 0 ]
            constraint_list += [tech_name + ' capacity_ge_0']
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            if 'series' in tech_dic:
                constraints += [ dispatch <= capacity * tech_dic['series'] ]
                constraint_list += [tech_name + ' dispatch_le_capacity_x_series']
            else:
                constraints += [ dispatch <= capacity ]
                constraint_list += [tech_name + ' dispatch_le_capacity']
                
            capacity_dic[tech_name] = capacity
            dispatch_dic[tech_name] = dispatch
            
            node_balance[node_to] += dispatch
            fnc2min +=  cvx.sum(dispatch * tech_dic['var_cost']) 
            fnc2min += capacity * tech_dic['fixed_cost'] * num_time_periods
        
        #----------------------------------------------------------------------
        # Storage
        # (n_capacity = 1 and n_dispatch = 1 and n_dispatch = 1)
        # Assumed to be storage equivalent to a battery
        # Note variable cost, if present, is applied to output only
        # Optional variables: charging_time, efficiency, decay_rate
        # Note: Charging time and decay rate is in units of number of time steps !!!
        
        elif tech_type == 'storage':
            capacity = cvx.Variable(1)
            dispatch_in = cvx.Variable(num_time_periods) 
            dispatch = cvx.Variable(num_time_periods)
            energy_stored = cvx.Variable(num_time_periods)
            constraints += [ capacity >= 0 ]
            constraint_list += [tech_name + ' capacity_ge_0']
            constraints += [ dispatch_in >= 0 ]
            constraint_list += [tech_name + ' dispatch_in_ge_0']
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            constraints += [ energy_stored >= 0 ]
            constraint_list += [tech_name + ' energy_stored_ge_0']
            constraints += [ energy_stored <= capacity ]
            constraint_list += [tech_name + ' energy_stored_le_capacity']
            if 'charging_time' in tech_dic:
                constraints += [ dispatch_in  <= capacity / tech_dic['charging_time'] ]
                constraint_list += [tech_name + ' dispatch_in_le_charging_rate']
                constraints += [ dispatch <= capacity / tech_dic['charging_time'] ]
                constraint_list += [tech_name + ' dispatch_le_discharge_rate']
            if 'decay_rate' in tech_dic:
                decay_rate = tech_dic['decay_rate']
            else:
                decay_rate = 0
            if 'efficiency' in tech_dic:
                efficiency = tech_dic['efficiency']
            else:
                efficiency = 1.0
                
            for i in range(num_time_periods):

                constraints += [
                    energy_stored[(i+1) % num_time_periods] ==
                        energy_stored[i] + efficiency * dispatch_in[i]
                        - dispatch[i] - energy_stored[i]*decay_rate
                        ]
                constraint_list += [tech_name + ' storage_balance_step_'+str(i).zfill(5)]
                        
            capacity_dic[tech_name] = capacity
            dispatch_dic[tech_name] = dispatch
            dispatch_dic[tech_name+' in'] = dispatch_in
            
            node_balance[node_to] += dispatch
            if 'node_from' in tech_dic:
                node_balance[node_from] += -dispatch_in
            else:
                node_balance[node_to ] += -dispatch_in
            if 'var_cost' in tech_dic:
                fnc2min += cvx.sum(dispatch * tech_dic['var_cost'])
            fnc2min += capacity * tech_dic['fixed_cost']  * num_time_periods
        
        #----------------------------------------------------------------------
        # Transmission  or concerion (directional)
        # (n_capacity = 1 and n_dispatch = 1)
        # Assumed to be unidirectional for simplicity !!!
        
        elif tech_type == 'transfer':
            capacity = cvx.Variable(1)
            dispatch = cvx.Variable(num_time_periods)
            constraints += [ capacity >= 0 ]
            constraint_list += [tech_name + ' capacity_ge_0']
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            constraints += [ dispatch <= capacity ]
            constraint_list += [tech_name + ' dispatch_le_capacity']
                                        
            capacity_dic[tech_name] = capacity
            dispatch_dic[tech_name] = dispatch
            
            if 'efficiency' in tech_dic:
                efficiency = tech_dic['efficiency']
            else:
                efficiency = 1.0

            node_balance[node_to] += dispatch
            node_balance[node_from] += - dispatch/efficiency # need more in than out            

            if 'var_cost' in tech_dic:
                fnc2min += cvx.sum(dispatch * tech_dic['var_cost'])
            fnc2min += capacity * tech_dic['fixed_cost'] * num_time_periods
        
        #----------------------------------------------------------------------
        # Bidirectional Transmission (directional)
        # (n_capacity = 1 and n_dispatch = 1)
        # Assumed to be unidirectional for simplicity !!!
        
        elif tech_type == 'transmission':
            capacity = cvx.Variable(1)
            dispatch = cvx.Variable(num_time_periods)
            dispatch_reverse = cvx.Variable(num_time_periods)
            constraints += [ capacity >= 0 ]
            constraint_list += [tech_name + ' capacity_ge_0']
            constraints += [ dispatch >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0']
            constraints += [ dispatch_reverse >= 0 ]
            constraint_list += [tech_name + ' dispatch_ge_0_rev']
            constraints += [ dispatch <= capacity ]
            constraint_list += [tech_name + ' dispatch_le_capacity']
            constraints += [ dispatch_reverse <= capacity ]
            constraint_list += [tech_name + ' capacity_ge_0']
                                        
            capacity_dic[tech_name] = capacity
            dispatch_dic[tech_name] = dispatch
            dispatch_dic[tech_name+' reverse'] = dispatch_reverse
            
            if 'efficiency' in tech_dic:
                efficiency = tech_dic['efficiency']
            else:
                efficiency = 1.0

            node_balance[node_to] += dispatch
            node_balance[node_from] += - dispatch/efficiency # need more in than out            
            node_balance[node_from] += dispatch_reverse
            node_balance[node_to] += -dispatch_reverse/efficiency # need more in than out            
                    
            if 'var_cost' in tech_dic:
                fnc2min += cvx.sum(dispatch * tech_dic['var_cost'])
                fnc2min += cvx.sum(dispatch_reverse * tech_dic['var_cost'])
            fnc2min += capacity * tech_dic['fixed_cost'] * num_time_periods

    # end of loop to build up minimization function and constraints 
    
    #%%======================================================================
    # Now add all of the node balances to the constraints
    
    for node in node_balance:
        constraints += [ 0 == node_balance[node] ]
        constraint_list += [node + ' balance']
        
    #%%======================================================================
    # Now solve the problem

    fnc2min_scaled = case_dic['numerics_scaling']*fnc2min
    obj = cvx.Minimize(fnc2min_scaled)
    prob = cvx.Problem(obj, constraints)
    prob.solve(solver = 'GUROBI')

#    # problem is solved
#    #======================================================================
#    # Now hand back decision variables
#    # The decision variables will be handed back in a form that is
#    # similar to <tech_list>. A list of dictionaries
#    
#    decision_dic_list = []
#    for tech_dic in tech_list:
#        decision_dic = {}
#        
#        tech_name = tech_dic['tech_name']
#        tech_type = tech_dic['tech_type']        
#        decision_dic['tech_name'] = tech_name
#        
#        if tech_type is 'non-dispatchable generator':
#            'non-dispatchable generator', 'generator', 'curtailment', 'lost_load', 'storage',  'transmission', or 'bidirectional_transmission'
#            'generator', 
#                         'storage',  'transmission', 'bidirectional_transmission']:
#            decision_dic['capacity'] = np.asscalar(capacity_dic[tech_name].value)
#        if tech_type in ['storage','transmission','bidirectional_transmission]':
#            decision_dic['dispatch_in'] = np.array(dispatch_dic[tech_name].value).flatten()
#        if n_dispatch == 1:
#            decision_dic['dispatch'] = np.array(dispatch_aux_dic[tech_name].value).flatten()
#                 decision_dic['capacity'] = np.asscalar(capacity_dic[tech_name].value)
#   if n_capacity == 1 and n_dispatch_in == 1 and n_dispatch  == 1:
#            decision_dic['energy_stored'] = np.array(energy_stored_dic[tech_name].value).flatten()
#            
#        decision_dic_list += [decision_dic]
#        
#    #--------------------------------------------------------------------------
#    global_results_dic = {}
#    
#    global_results_dic['system_cost'] = np.asscalar(prob.value)/case_dic('numerics_scaling')
#    global_results_dic['problem_status'] = prob.status
#    end_time = time.time()
#    global_results_dic['runtime'] = end_time - start_time
#    
#    #==========================================================================
#    return global_results_dic, decision_dic_list
#    
    
    end_time = datetime.datetime.now()    # timer starts
    if case_dic['verbose']:
        print ('    end time = ',end_time)
        print ('    elapsed time = ',end_time - start_time)

            
    return constraint_list,constraints,prob,capacity_dic,dispatch_dic    
    
    
    
    