# -*- coding: utf-8 -*-

"""

Save_Basic_Results.py

save basic results for the simple energy model
    
"""

# -----------------------------------------------------------------------------



import cvxpy
import utilities
import numpy as np

       
#%%
# save scalar results for all cases
def extract_cvxpy_output(case_dic,tech_list,constraint_list, 
                        cvxpy_constraints,cvxpy_prob,
                        cvxpy_capacity_dic,cvxpy_dispatch_dic):
        
    # conert everything to numpy arrays
    numerics_scaling = case_dic['numerics_scaling']
    num_time_periods = case_dic['num_time_periods']
                            
    node_list = utilities.get_nodes(tech_list)
    
    # case_scalar_output_dic = copy.deepcopy(capacity_dic)
    # case_vector_output_dic = copy.deepcopy(dispatch_dic)
    
    capacity_dic = {}
    dispatch_dic = {}

    for item in cvxpy_capacity_dic:
        val = cvxpy_capacity_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            capacity_dic[item] = np.asscalar(cvxpy_capacity_dic[item].value)
       
    for item in cvxpy_dispatch_dic:
        val = cvxpy_dispatch_dic[item]
        if type(val) ==  cvxpy.expressions.variable.Variable:
            dispatch_dic[item+' dispatch'] = cvxpy_dispatch_dic[item].value
    
    prob = {}
    prob['status'] = cvxpy_prob.status
    prob['value'] = cvxpy_prob.value / numerics_scaling
    prob['avg_cost'] = prob['value']/num_time_periods
    
    # get electricity price at each node by taking dual value of node balance equation
    node_price = {}
    for node in node_list:
        idx = constraint_list.index(node + ' balance')
        node_price[node] = -cvxpy_prob.constraints[idx].dual_value / numerics_scaling
    prob['node_price'] = node_price
    
    return prob,capacity_dic,dispatch_dic