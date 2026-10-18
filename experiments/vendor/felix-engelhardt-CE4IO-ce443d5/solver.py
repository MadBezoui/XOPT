from gurobipy import GRB
import gurobipy as gp
from time import time

printout = False

def bip_solve_knapsack(weights,costs,b:int,enforced_elements=[],disallowed_elements=[],constrained_set=[],deviate_from_solution=[]):
    """Simple BIP for a Knapsack instance. Can solve Knapsack problems with variable fixations or constrained sets.
    deviate_from_solution enforces that at least one variable to differs from a given solution."""
    indices = list(range(len(weights)))
    m = gp.Model("Knapsack Subproblem")
    m.ModelSense = GRB.MAXIMIZE
    m.Params.OutputFlag = 0
    x = m.addVars(indices,vtype=GRB.BINARY,obj=costs)
    m.addConstr(gp.quicksum(weights[index]*x[index] for index in indices) <= b)  # This is the actual Knapsack constraint
    m.addConstrs(x[index] == 1 for index in enforced_elements) # These and the following two constraints model favoured solution spaces
    m.addConstrs(x[index] == 0 for index in disallowed_elements)
    for item in constrained_set: m.addConstr(gp.quicksum(x[index] for index in item["variables"]) <= item['rhs'])
    if deviate_from_solution != []: # This ensures that not all variables have the same assignment as in a given solution
        m.addConstr(gp.quicksum((1-x[index]) for index in deviate_from_solution) + gp.quicksum(x[index] for index in range(len(weights)) if index not in deviate_from_solution) >= 1)
    m.update()
    m.optimize()
    if m.status == GRB.OPTIMAL:
        return [index for index in indices if x[index].x > 0.999], int(m.getObjective().getValue()), m.Runtime
    else:
        return False
    
def bip_solve_cover(weights,costs,b:int,enforced_elements=[],disallowed_elements=[],constrained_set=[],deviate_from_solution=[],cover_set=[]):
    """Simple BIP for a Cover instance. Exclusively used in the separation problem for general weak/strong CFs."""
    indices = list(range(len(weights)))
    m = gp.Model("Cover")
    m.ModelSense = GRB.MINIMIZE
    m.Params.OutputFlag = 0
    x = m.addVars(indices,vtype=GRB.BINARY,obj=costs)
    m.addConstr(gp.quicksum(weights[index]*x[index] for index in indices) >= b) # Cover constraint
    m.addConstrs(x[index] == 1 for index in enforced_elements) # These and the following two constraints model favoured solution spaces
    m.addConstrs(x[index] == 0 for index in disallowed_elements)
    for item in constrained_set: m.addConstr(gp.quicksum(x[index] for index in item["variables"]) <= item['rhs'])
    for item in cover_set: m.addConstr(gp.quicksum(x[index] for index in item["variables"]) >= item['rhs'])
    if deviate_from_solution != []: # This ensures that not all variables have the same assignment as in a given solution
        m.addConstr(gp.quicksum((1-x[index]) for index in deviate_from_solution) + gp.quicksum(x[index] for index in range(len(weights)) if index not in deviate_from_solution) >= 1)
    m.update()
    m.optimize()
    if m.status == GRB.OPTIMAL:
        return [index for index in indices if x[index].x>0.999], int(m.getObjective().getValue()), m.Runtime
    else:
        return False,False,False

def seperate_minimal_inequality(weights:list,costs:list,b:int,favoured_domain_objective:int):
    """This finds a smallest violating subset for general weak/strong CEs. Returns true is a CE exists, otherwise returns false and a minimal counterexample."""
    indices = list(range(len(weights)))
    m = gp.Model("Separation")
    m.ModelSense = GRB.MINIMIZE
    m.Params.OutputFlag = 0
    x = m.addVars(indices,vtype=GRB.BINARY,obj=weights)
    m.addConstr(gp.quicksum(weights[index]*x[index] for index in indices) >= b) # Cover constraint
    m.addConstr(gp.quicksum(costs[index]*x[index] for index in indices) <= favoured_domain_objective-1) # Better solution
    m.update()
    m.optimize()
    if m.status == GRB.OPTIMAL:
        return [index for index in indices if x[index].x>0.999], int(m.getObjective().getValue()), m.Runtime
    else:
        return False,False,False

def is_cf(weights,costs,b:int,strong:bool,enforced_elements=[],disallowed_elements=[],constrained_set=[],objective=False) -> tuple[bool,list]:
    """ Validates whether an instance is a CE by comparing the objective of the nominal problem with the objective of the problem constrained to the favoured solution space.
        If a CE exists, return true and a solution, otherwise, returns and a minimal counterexample solution."""
    
    # If the problem does not contain a feasible solution in the favoured solution space, we do no have a CF => return False
    solution,favoured_domain_objective,dummy = bip_solve_cover(weights,costs,b,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set)
    if solution == False: 
        if printout: print("Problem infeasible, no CE")
        return False, []
    
    # Otherwise, solve the separation problem for the favoured solution space
    counterexample,nominal_objective,dummy = seperate_minimal_inequality(weights,costs,b,favoured_domain_objective=favoured_domain_objective) 

    if counterexample == False:
        if not strong:
            if printout: print("Weak CE found in check cf. Favoured domain objective:",favoured_domain_objective)
            return True, solution
        else:
            # Invert all favoured solution space types, note that this only works for single favoured solution space types
            if enforced_elements != []: # The inversion of enforced elements is a capacity constraint on the enforced set
                local_constrained_set = [{'variables':enforced_elements,'rhs':len(enforced_elements)-1} ]
                local_cover_set = []
            elif disallowed_elements != []: # The inversion of disallowed elements is a cover constraint with b = 1
                local_constrained_set = []
                local_cover_set = [{'variables':disallowed_elements,'rhs':1}]
            elif constrained_set != []: # The inversion of a constraint set is a cover set
                local_constrained_set = []
                local_cover_set = [{'variables':item['variables'],'rhs':item['rhs']+1} for item in constrained_set] 
            
            alt_solution,other_domain_objective,dummy = bip_solve_cover(weights,costs,b,constrained_set=local_constrained_set,cover_set=local_cover_set)

            if abs(other_domain_objective-favoured_domain_objective) < 0.001:
                if printout: print("Weak but no strong CE, adding ineqality to seperate non-favoured solution.")
                return False, alt_solution
            else:  
                if printout: print("Strong CE found at objective value:",favoured_domain_objective)
                return True, solution
    else:
        if printout: print("No CE but Counterexample found at objective value:",nominal_objective," with favoured domain objective:",favoured_domain_objective)
        return False, counterexample

def find_bounds_for_c(weights,costs,b,enforced_elements=[],disallowed_elements=[],constrained_set=[],max_deviation=0.05):
    """c_max is set to maximum objective value that can be attained through varying a,b within H, and having x in D 
       c_min is set to maximum objective value that can be attained when varying all weights in favour of our solution elements"""
    if sum(weights*(1-max_deviation)) < b*(1+max_deviation): c_max = sum(costs)
    else: dummy, c_max,dummy = bip_solve_cover(weights*(1-max_deviation),costs,b*(1+max_deviation),enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set)
    dummy, c_min,dummy = bip_solve_cover(weights*(1+max_deviation),costs,b*(1-max_deviation),enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set)
    return int(c_min),int(c_max)

def solve_counterfactual_subproblem(weights,costs,b,target_objective,strong:bool,cuts=[],best_known_objective=GRB.INFINITY,enforced_elements=[],disallowed_elements=[],constrained_set=[],max_deviation=0.05,timerlimit=None):
    """ Solves a CE subproblem for one fixed objective values.
    max_deviation = maximum relative change to a,b in %, i.e. 0.05 -> 5%
    """
    indices = list(range(len(weights)))
    m = gp.Model("CE-Knapsack-Subproblem")
    m.Params.OutputFlag = 0
    m.Params.LazyConstraints = 1 

    # Variables
    x = m.addVars(indices,vtype=GRB.BINARY)
    new_weights = m.addVars(indices,vtype=GRB.INTEGER,lb=weights*(1-max_deviation),ub=weights*(1+max_deviation))
    delta_a = m.addVars(indices,vtype=GRB.CONTINUOUS) # Variables encoding norms
    
    # Constraints
    m.addConstr(gp.quicksum(costs[index]*x[index] for index in indices) == target_objective) # Optimality
    m.addConstr(gp.quicksum(new_weights[index]*x[index] for index in indices) >= b) # Feasibility in new A,b
    m.addConstrs(x[index] == 0 for index in disallowed_elements) # Enforced parameter domains
    m.addConstrs(x[index] == 1 for index in enforced_elements)
    for item in constrained_set: m.addConstr(gp.quicksum(x[index] for index in item["variables"]) <= item['rhs'])
    m.addConstrs(delta_a[index] >= new_weights[index] - weights[index] for index in indices) # Linking/Objective
    m.addConstrs(delta_a[index] >= weights[index] - new_weights[index] for index in indices)
    m.addConstr(gp.quicksum(delta_a[index] for index in indices) <= best_known_objective) # Cutting off solution space
    y_constraints = {}
    original_y_range = range(len(cuts))
    for cutindex in original_y_range:
        y_constraints[cutindex] = m.addConstr(gp.quicksum(new_weights[index] for index in cuts[cutindex]) <= b - 1) # y cuts added from previous iterations

    # Objective
    m.setObjective(gp.quicksum(delta_a[index] for index in indices),GRB.MINIMIZE)
    
    optimal =  False
    counter = 0
    while not optimal:
        counter += 1
        m.optimize()
        if m.Status == GRB.INFEASIBLE: 
            return None,None, GRB.INFINITY, m.Runtime, cuts
        if timerlimit != None and time() > timerlimit:
            if printout: print("Timelimit reached, stopping subproblem solve.")
            return None,None, GRB.INFINITY, m.Runtime, cuts
        incumbent_weights = [int(new_weights[index].x) for index in indices]

        cf_found, solution_or_counterexample = is_cf(incumbent_weights,costs,b,strong=strong,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set)

        if cf_found:    
            if printout: print("ACTUALLY found a CE. Cost",m.getObjective().getValue(),"Solution:",solution_or_counterexample)
            optimal = True
        else: # Save the old solution to check if it changes
            y_constraints[len(cuts)] = m.addConstr(gp.quicksum(new_weights[index] for index in solution_or_counterexample) <= b-1) # Since any feasible solution has cTy >= v+1
            if solution_or_counterexample in cuts: # If the solution is already in the cuts, we do not add it again
                if printout:print("ERROR: Solution already in cuts, this should not happen",solution_or_counterexample)
                break
            else:
                cuts.append(solution_or_counterexample)
                m.update()
                if printout:print("No CE found, adding cut",len(cuts),solution_or_counterexample)
                
    if m.status == GRB.OPTIMAL:
        return [int(new_weights[index].x) for index in indices],b, int(m.getObjective().getValue()), m.Runtime, cuts
    else:
        return None,None, GRB.INFINITY, m.Runtime, cuts

def counterfactual_lb(weights,capacity,cuts=[],max_deviation=0.05):
    """ Determines a CF lower bound for the 1-norm
    max_deviation = maximum relative change to a,b in %, i.e. 0.05 -> 5%
    """
    indices = list(range(len(weights)))
    m = gp.Model("CF-Knapsack-Subproblem")
    m.Params.OutputFlag = 0
    m.Params.LazyConstraints = 1 

    # Variables
    new_weights = m.addVars(indices,vtype=GRB.INTEGER,lb=weights*(1-max_deviation),ub=weights*(1+max_deviation))
    delta_a = m.addVars(indices,vtype=GRB.CONTINUOUS,lb=0) # Variables encoding norms
    
    # Constraints
    m.addConstrs(delta_a[index] >= new_weights[index] - weights[index] for index in indices) # Linking/Objective
    m.addConstrs(delta_a[index] >= weights[index] - new_weights[index] for index in indices)
    for cut in cuts:
        m.addConstr(gp.quicksum(new_weights[index] for index in cut) <= capacity - 1) # y cuts added from previous iterations
    m.update()

    m.setObjective(gp.quicksum(delta_a[index] for index in indices),GRB.MINIMIZE)
    m.optimize()

    if m.status == GRB.OPTIMAL:
        return m.getObjective().getValue(), m.Runtime
    else:
        return GRB.INFINITY, m.Runtime