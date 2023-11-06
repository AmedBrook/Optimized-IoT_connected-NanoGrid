
'''
######################################################
Mixed integer energy hybridization problem solved
with Pulp script to optimize fuel oil consumption
######################################################
'''
# IMPORTING LIBRARIES.
from flask import Flask, render_template
import numpy as np
from pulp import *
from IPython.display import Image
import plotly
import plotly.express as px
import pandas as pd
import json


app = Flask(__name__)


def lwd(
 val11, val12, val13,
 val21, val22, val23,
 val31, val32, val33,
 val41, val42, val43,
 L1, L2, L3, L4):

    L = {}

    E1 = np.atleast_2d(np.linspace(val11, val12, val13)).T.conj()
    E2 = np.atleast_2d(np.linspace(val21, val22, val23)).T.conj()
    E3 = np.atleast_2d(np.linspace(val31, val32, val33)).T.conj()
    E4 = np.atleast_2d(np.linspace(val41, val42, val43)).T.conj()

    L1 = dict(enumerate(E1.flatten(), L1))
    L2 = dict(enumerate(E2.flatten(), L2))
    L3 = dict(enumerate(E3.flatten(), L3))
    L4 = dict(enumerate(E4.flatten(), L4))
    L = {**L1, **L2, **L3, **L4}
    return L
# Function testing.


lwd(
 200, 200, 10,
 400, 400, 10,
 600, 600, 10,
 600, 200, 30,
 0, 10, 20, 30)


from src.functions.fuel_consumption import fuelCon

def fuelCon(P, P_max):

    fc = {}
    fc = 260 * P - 67 / P_max * P**2
    return fc


# DEFINING SET OF PARAMETERS.
Q_max = 250
Q_0 = 0.5*Q_max
Q_final = 0.5*Q_max
eff_to_bat = 0.98
eff_from_bat = 0.98
P_max = 1000
P_min = 0
dt = 1
t_max = 10
t = np.atleast_2d(np.arange(0, t_max, dt)).T.conj()
n = len(t)
m = 1
fc_offset = 190
V_steps = [x for x in range(0, n)]
V_steps_z = V_steps[:-1]

# CONSTRUCTING LOAD PROFILE.
L = lwd(200, 50, 5,
        50, 300, 5,
        200, 150, 10,
        150, 250, 30,
        0, 5, 20, 30)


# CREATING OPTIMIZATION PROBLEM VARIABLE.
Optim = LpProblem('Energy_Opt', LpMinimize)


# CALCULATING THE SLOPE AND INTERCEPT FOR THE PROBLEM.
a_j = (fuelCon(0.9 * P_max, P_max) - fuelCon(0.2 * P_max, P_max)) / (0.9 * P_max)  # slope.
b_j = fuelCon(0.2*P_max, P_max) - a_j*0.2*P_max  # Intercept.
maxFC = fuelCon(0.9*P_max, P_max)  # Max fuel bound.


# SETTING UP THE LP VARIABLES.
Q_bat = pulp.LpVariable.dicts("Q_bat", V_steps, lowBound=0.2 * Q_max, upBound=Q_max, cat=LpContinuous)
P_From_bat = pulp.LpVariable.dicts("P_From_bat", V_steps, lowBound=P_min, upBound=0.9 * P_max, cat=LpContinuous)
P = pulp.LpVariable.dicts("P", V_steps, lowBound=P_min, upBound=0.9 * P_max, cat=LpContinuous)
P_load = pulp.LpVariable.dicts("P_load", V_steps, lowBound=P_min, upBound=0.9 * P_max, cat=LpContinuous)
Z = pulp.LpVariable.dicts("Z", V_steps_z, lowBound=0, upBound=1, cat=LpInteger)
FOC = pulp.LpVariable.dicts("FOC", V_steps, lowBound=0, upBound=maxFC, cat=LpContinuous)
P_to_bat = pulp.LpVariable.dicts("P_to_bat", V_steps, lowBound=P_min, upBound=0.9*P_max, cat=LpContinuous)
Y_to_bat = pulp.LpVariable.dicts("Y_to_bat", V_steps, lowBound=0, upBound=1, cat=LpInteger)
Y_from_bat = pulp.LpVariable.dicts("Y_from_bat", V_steps, lowBound=0, upBound=1, cat=LpInteger)
Y = pulp.LpVariable.dicts("Y", V_steps, lowBound=0, upBound=1, cat=LpInteger)


# SETTING UP THE OBJECTIF FUNCTION.
FC = sum(FOC[k] for k in V_steps) * dt/1000  # sum of the fuel oil comsumption for all gensets over all k steps.
L_added_cost = sum(Z[i] for i in V_steps_z)  # Sum of all of the additional costs including starting costs.
Optim += lpSum(FC + L_added_cost), "Minimization fuel oil consumption objective"
print(FC)


# SETTING UP THE OBJECTIF FUNCTION.
for k in V_steps:

    # Fuel oil consumption constraint.
    Optim += FOC[k] == P[k]*a_j + b_j - fc_offset*Y[k]

    # Load requirements constraints
    Optim += P_load[k] + eff_from_bat*P_From_bat[k] == L[k]
    Optim += P_load[k] + P_to_bat[k] == P[k]

    # Genset logical constraints.
    Optim += P[k] <= 0.9 * P_max * Y[k]
    Optim += P[k] >= 0.2 * P_max * Y[k]

    # Battery charging logical constraints.
    Optim += P_to_bat[k] <= 0.9 * P_max * Y_to_bat[k]
    Optim += P_From_bat[k] <= 0.9 * P_max * Y_from_bat[k]
    Optim += Y_to_bat[k] + Y_from_bat[k] <= 1

    # Charge balance logical constraints.
    if k == V_steps[0]:
        Optim += Q_bat[k] == Q_0 + eff_to_bat*P_to_bat[k]*dt - P_From_bat[k]*dt

    else:
        Optim += Q_bat[k] == Q_bat[k-1] + eff_to_bat*P_to_bat[k]*dt - P_From_bat[k]*dt

# ADDITIONAL STARTING COSTS CONSTRAINT.
for k in range(V_steps[0], V_steps[-1]):
    Optim += Z[k] >= Y[k + 1] - Y[k]

# CHARGE BALANCE AT THE FINAL TIME STEP.
Optim += Q_bat[V_steps[-1]] == Q_final


# SOLVING THE PRBLEM USING GUROBI SOLVER.
status = Optim.solve(GUROBI())






# Constructing list out of the P_A vector.

P_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('P_'+ str(i)):
      P_list.append(v.varValue)


# Constructing list out of the P_A_load vector.

P_load_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('P_load_'+ str(i)):
      P_load_list.append(v.varValue)


# Constructing list out of the P_A_to_bat vector.

P_to_bat_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('P_to_bat_'+ str(i)):
      P_to_bat_list.append(v.varValue)


# Constructing list out of the P_From_bat.

P_From_bat_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('P_From_bat_'+ str(i)):
      P_From_bat_list.append(v.varValue)


# Constructing list out of the Q_bat vector.

Q_bat_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('Q_bat_'+ str(i)):
      Q_bat_list.append(v.varValue)


# constructing list out of the FC_A vector.

FOC_list = []
for v in Optim.variables():
  for i in V_steps:
    if v.name == ('FOC_'+ str(i)):
      FOC_list.append(v.varValue/10**5)


# Constructing list out of load profil vector.

d_load_list = []              
for i in V_steps:
    d_load_list.append(L[i])



##################################################################



# Generated power chart
@app.route('/Energy_dash')
def Energy_dash(): 
    
# Power generated by the Genset.(Chart 1)    
    P_A_dframe = {
             'Power generated by the Genset.': P_list,
             'Scale' : P_list}

    P_A_df = pd.DataFrame(P_A_dframe)
    fig = px.bar(P_A_df, x = V_steps,
             y = P_list,
             title = '________Power Generated By The Genset A._________',
             labels = dict(x = "Time Step (h)", y = "Power(kw)"), text_auto = True)
             
    graphJSON1 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


#--------------------------------------------------------------------------------#
     

# Power from Genset to laod.(Chart 2)   
    P_to_load_dframe = {
             "Power from Genset to laod.": P_load_list,
             'Scale' : P_load_list}

    P_to_load_df = pd.DataFrame(P_to_load_dframe)


    fig = px.bar(P_to_load_df, x = V_steps,
             y = P_load_list,
             title = '_________Power Transfered From The Genset To Load.________',
             labels = dict(x = "Time Step (h)", y = "Power(kw)"), text_auto = True)
    graphJSON2 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('dashboard.html', graphJSON2=graphJSON2, graphJSON1=graphJSON1)



if __name__=='__main__': 
    app.run(port=8080)