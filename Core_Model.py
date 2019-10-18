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
node_in (optional) character string name of node
node_out (optional) character string name of node
fixed_cost (required if capacity decision) real number
var_cost (required if dispatch decision) real number

'''
#%%

import cvxpy as cvx
import time
import datetime
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

Here is the basic logic:
    
Names shortened for table for space reasons.

n_cap = n_capacity
n_dis_in = n_dispatch_in
n_dis_out = n_dispatch_out 

n_cap   n_dis_in    n_dis_out   Notes
-----   --------    ---------   -----
0       0           0           Assumed to be demand, if series is available assume
                                 it is energy sink else assume energy sink of 1 kW.
0       0           1           Assumed to be unmet demand (lost load) with variable cost
                                 Requires: <var_cost>
0       1           0           Assumed to be generic curtailment.
                                 Accepts: <var_cost>
1       0           0           Assumed to be non-curtailable generator, if time series
                                 is available, it will be assumed to be output per unit
                                 capacity.
1       0           1           Assumed to be curtailable generator. If time series is
                                 available assumed to be maximum output per unit capacity.
1       1           1           Assumed to be storage equivalent to a battery

"""
#%% Define main code for Core_Model

def core_model(global_dic, tech_list):

    start_time = time.time()    # timer starts

    # Initialize variables to be used later
    fcn2min = 0
    constraints = []

    tech_names = [] # list of technology names
    node_balance = {} # dictionary of load balancing values; constrained to equal zero.
    # NOTE: node_names = node_balance.keys()     after this code runs.
    capacity_dic = {} # dictionary of capacity decision variables
    dispatch_in_dic = {} # dictionary of dispatch decision variables for inflow to tech
    dispatch_out_dic = {} # dictionary of dispatch decision variables for inflow to tech
    
    #loop through dics in tech_list
    for tech_dic in tech_list:

        tech_name = tech_dic['tech_name']
        tech_names.append(tech_name)
        
        num_time_periods = tech_dic['num_time_periods']
        
        n_capacity = tech_dic['n_capacity'] # number of capacity decisions for this tech
        n_dispatch = tech_dic['n_dispatch'] # number of dispatch decisions for this tech
        
        # check the input node
        node_in = tech_dic['node_in']
        if not node_in in node_balance.keys():
            node_balance[node_in] = 0.0
        
        # check the output node
        node_out = tech_dic['node_out']
        if node_out in tech_dic:
            if not node_out in node_balance.keys():
                node_balance[node_out] = np.zeros(num_time_periods)
                
"""
For the purposes of this routine, we will use a high level taxonomy based on
the number of capacity decisions (one decision per simulation) and number of
dispatch decisions (one decision per time step).

Names shortened for table for space reasons.

n_cap = n_capacity
n_dis_in = n_dispatch_in
n_dis_out = n_dispatch_out 

n_cap   n_dis_in    n_dis_out   Notes
-----   --------    ---------   -----
0       0           0           Assumed to be demand, if series is available assume
                                 it is energy sink else assume energy sink of 1 kW.
0       0           1           Assumed to be unmet demand (lost load) with variable cost
                                 Requires: <var_cost>
0       1           0           Assumed to be generic curtailment.
                                 Accepts: <var_cost>
1       0           0           Assumed to be non-curtailable generator, if time series
                                 is available, it will be assumed to be output per unit
                                 capacity.
1       0           1           Assumed to be curtailable generator. If time series is
                                 available assumed to be maximum output per unit capacity.
1       1           1           Assumed to be storage equivalent to a battery

"""

        #----------------------------------------------------------------------
        # demand (n_capacity = 0 and n_dispatch_in = 0 and n_dispatch_out = 0)
        #  Assumed to be demand, if series is available assume
        #  it is energy sink else assume energy sink of 1 kW.

        if n_capacity == 0 and n_dispatch_in == 0 and n_dispatch_out == 0:
            if 'series' in tech_dic:
                dispatch_in = tech_dic['series']
            else:
                dispatch_in = np.ones(num_time_periods)
            dispatch_in_dic[tech_name] = dispatch_in
            # note that dispatch from a node is regarded as negative influence on that node
            node_balance[node_in] += - dispatch_in

        #----------------------------------------------------------------------
        # unmet demand 
        # (n_capacity = 0 and n_dispatch_in = 0 and n_dispatch_out = 1)
        # Assumed to be unmet demand (lost load) with variable cost
        
        if n_capacity == 0 and n_dispatch_in == 0 and n_dispatch_out  == 1:
            dispatch_out = cvx.Variable(num_time_periods) 
            constraints += [ dispatch_out >= 0 ]
            dispatch_out_dic[tech_name] = dispatch_out
            node_balance[node_out] += + dispatch_out
            fnc2min +=  cvx.sum(dispatch_out * tech_dic['var_cost'])/num_time_periods

        #----------------------------------------------------------------------
        # generic curtailment
        # (n_capacity = 0 and n_dispatch_in = 1 and n_dispatch_out = 0)
        # Assumed to be curtailment
        
        if n_capacity == 0 and n_dispatch_in == 1 and n_dispatch_out  == 0:
            dispatch_in = cvx.Variable(num_time_periods) 
            constraints += [ dispatch_in >= 0 ]
            dispatch_in_dic[tech_name] = dispatch_in
            node_balance[node_in] += - dispatch_in
            if 'var_cost' in tech_dic: # if cost of curtailment
                fnc2min +=  cvx.sum(dispatch_in * tech_dic['var_cost'])/num_time_periods
                
        #----------------------------------------------------------------------
        # non-curtailable generator 
        # (n_capacity = 1 and n_dispatch_in = 0 and n_dispatch_out = 1)
        # If time series is available, it will be assumed to be output per unit
        #  capacity.
        
        if n_capacity == 1 and n_dispatch_in == 0 and n_dispatch_out  == 0:
            capacity = cvx.Variable(1)
            dispatch_out = cvx.Variable(num_time_periods) 
            constraints += [ capacity >= 0 ]
            if 'series' in tech_dic:
                dispatch_out = capacity * series
            else:
                dispatch_out = capacity
            capacity_dic[tech_name] = capacity
            dispatch_out_dic[tech_name] = dispatch_out # NOTE: Not a decision variable
            node_balance[node_out] += dispatch_out
            fnc2min += capacity * tech_dic['fixed_cost']

        #----------------------------------------------------------------------
        # curtailable generator
        # (n_capacity = 1 and n_dispatch_in = 0 and n_dispatch_out = 1)
        # Assumed to be non-curtailable generator, if time series
        # is available, it will be assumed to be output per unit capacity.
        
        if n_capacity == 1 and n_dispatch_in == 0 and n_dispatch_out  == 1:
            capacity = cvx.Variable(1)
            dispatch_out = cvx.Variable(num_time_periods) 
            constraints += [ capacity >= 0 ]
            constraints += [ dispatch_out >= 0 ]
            if 'series' in tech_dic:
                constraints += [ dispatch_out <= capacity * tech_dic['series'] ]
            else:
                constraints += [ dispatch_out <= capacity ]
            capacity_dic[tech_name] = capacity
            dispatch_out_dic[tech_name] = dispatch_out
            node_balance[node_out] = node_balance[node_out] + dispatch_out
            fnc2min +=  cvx.sum(dispatch_out * tech_dic['var_cost'])/num_time_periods + capacity * tech_dic['fixed_cost']
        
        #----------------------------------------------------------------------
        # Storage
        # (n_capacity = 1 and n_dispatch_in = 1 and n_dispatch_out = 1)
        # Assumed to be storage equivalent to a battery
        # Note variable cost, if present, is applied to output only
        # Optional variables: charging_time, round_trip_efficiency, decay_rate
        # Note: Charging time and decay rate is in units of number of time steps !!!
        
        if n_capacity == 1 and n_dispatch_in == 1 and n_dispatch_out  == 1:
            capacity = cvx.Variable(1)
            dispatch_in = cvx.Variable(num_time_periods) 
            dispatch_out = cvx.Variable(num_time_periods)
            energy_stored = cvx.Variable(num_time_periods)
            charging_time = 
            constraints += [ capacity >= 0 ]
            constraints += [ dispatch_in >= 0 ]
            constraints += [ dispatch_out >= 0 ]
            constraints += [ energy_stored >= 0 ]
            constraints += [ energy_stored <= capacity ]
            if 'charging_time' in tech_dic:
                constraints += [ dispatch_in  <= capacity / charging_time_storage ]
                constraints += [ dispatch_out <= capacity / charging_time_storage ]
            if 'decay_rate' in tech_dic:
                decay_rate = tech_dic['decay_rate']
            else:
                decay_rate = 0
            if 'round_trip_efficiency' in tech_dic:
                round_trip_efficiency = tech_dic['round_trip_efficiency']
            else:
                round_trip_efficiency = 1.0
                
            for i in range(num_time_periods):

            constraints += [
                    energy_stored[(i+1) % num_time_periods] ==
                        energy_stored[i] + round_trip_efficiency * dispatch_in[i]
                        - dispatch_out[i] - energy_stored[i]*decay_rate
                    ]
            if 'var_cost' in tech_dic
                fcn2min += cvx.sum(dispatch_out * tech_dic['var_cost'])/num_time_periods
            fnc2min += capacity * tech_dic['fixed_cost']

        #----------------------------------------------------------------------
        # end of loop to build up minimization function and constraints 
        # Now work on solving the problem
        
        obj = cvx.Minimize(fcn2min)
        prob = cvx.Problem(obj, constraints)
        prob.solve(solver = 'GUROBI')
    
    
    
    