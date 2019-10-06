# Core computation code for the Macro Energy Model
#
'''

File name: Core_Model.py

Macro Energy Model ver. 2.0

This is the heart of the Macro Energy Model. 

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


'''
