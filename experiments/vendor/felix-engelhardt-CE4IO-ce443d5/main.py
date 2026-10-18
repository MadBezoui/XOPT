from IO import kplib_reader,write_as_json
from sys import argv
from random import seed,sample
from time import time
from solver import bip_solve_cover,find_bounds_for_c,is_cf,solve_counterfactual_subproblem,counterfactual_lb
from statistics import mean
from gurobipy import GRB

def run_cf(weights,costs,capacity,strong:bool,enforced_elements=[],disallowed_elements=[],constrained_set=[],parameters=[],max_deviation=0.05,epsilon=0.001,timelimit=10*3600):
    """ Determines a counterfactual explenation for mutable in a,b."""
    solution,c_opt,runtime = bip_solve_cover(weights,costs,capacity)
    log = {} # This is used to log everything
    log['original_runtime'] = runtime
    starttime = time() # Used to measure timelimit

    # preprocessing
    c_min,c_max = find_bounds_for_c(weights,costs,capacity,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,max_deviation=max_deviation)
    print("Beginning optimisation:\nPotential objective range for CE: c_min:",c_min,"c_max:",c_max,"c_opt",c_opt,"\n")
    log['c_min'] = c_min
    log['c_max'] = c_max
    log['n_subproblems'] = c_max-c_min
    incumbent_objective = GRB.INFINITY

    lb = 0
    lb_time = 0
    cuts = [] # format: [[indices to include in cut],[...]]
    iterationcounter = 0
    incumbents,lbs = {},{}
    time_per_iteration = {}

    cf_found, solution = is_cf(weights,costs,capacity,strong=strong,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set)
    
    if cf_found:
        print("Solution was already CE: CE found:",cf_found,"with objective",solution)
        log['solution'] = "Solution was already CF with cost 0."
        incumbent_objective = 0
        incumbent_weights = list(weights)
        incumbent_capacity = capacity
    else:
        # variables
        incumbent_weights,incumbent_capacity,incumbent_objective = None,None,GRB.INFINITY

        # This is the main iteration
        for current_obj_candidate in range(c_min,c_max+1): 
            if time() - starttime > timelimit:
                print(int(iterationcounter/(c_max-c_min)*100),r"% of values searched before timelimit.")
                log['timelimit'] = True
                break

            iterationcounter += 1
            start = time()
            if incumbent_objective != GRB.INFINITY:
                print(current_obj_candidate,current_obj_candidate-c_min,"out of",c_max-c_min,"Incumbent:",int(incumbent_objective),"LB:",int(lb))
            else:
                print(current_obj_candidate,current_obj_candidate-c_min,"out of",c_max-c_min,"No Incumbent. LB:",int(lb))
        
            # Solve CF problem
            new_weights,new_capacity,new_objective,runtime,cuts = solve_counterfactual_subproblem(weights,costs,capacity,current_obj_candidate,strong,cuts,best_known_objective=incumbent_objective,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set,timerlimit=starttime+timelimit)
            
            # Solve LB problem based on CF cuts
            lb_start = time()
            lb_new,lb_runtime = counterfactual_lb(weights,capacity,cuts=cuts,max_deviation=max_deviation)
            lb_time += lb_start - time()

            # Track optimality status
            if lb_new > lb: 
                lb = lb_new 
                lbs[current_obj_candidate] = lb
            if new_objective < incumbent_objective: 
                print("    Found new incumbent at ",current_obj_candidate," with objective",new_objective,", LB",lb,"\n")
                print("    New weights:",new_weights)
                incumbent_weights,incumbent_capacity,incumbent_objective = new_weights,new_capacity,new_objective
                incumbents[current_obj_candidate] = new_objective

            # Track time
            time_per_iteration[current_obj_candidate] = time() -start
        
            # Check termination criteria
            if incumbent_objective <= lb + epsilon: 
                if incumbent_objective == 0:
                    print("Found final CF solution with objective 0, stopped search.",incumbent_weights,incumbent_capacity,incumbent_objective)
                else:
                    print("Found final CF solution with objective",incumbent_objective,"current LB is",lb_new)
                break
    
    # Log all potentially important information
    if incumbent_objective != GRB.INFINITY and 'timelimit' not in log: log['solved'] = True
    elif 'timelimit' in log: log['solved'] = False
    else: log['solved'] = "infeasible"
    log['Final_UB'] = incumbent_objective
    log['Final_LB'] = lb
    log['total_iterations'] = iterationcounter
    if incumbent_weights != None:
        log['final_solution_weights'] = list(incumbent_weights)
        log['final_solution_delta'] = [incumbent_weights[index]-weights[index] for index in range(len(incumbent_weights))] # This is the deviation from the original weights
        log['final_solution_capacity'] = incumbent_capacity
        log['incumbents'] = incumbents
    log['lbs'] = lbs
    log['cuts'] = cuts
    log['total_time_for_LBs'] = lb_time
    log['time_per_iteration_in_s'] = time_per_iteration

    return log

if __name__ == "__main__": 
    # Example execution: python3 main.py 'uncorrelated' 10 'p' 0.05 12 strong
    # Meaning: python3 main.py [instance type] [instance size] [favoured solution space] [size of mutable parameter space] [instance index] [CE type]
    # [instance type]: "strongly_correlated" and "uncorrelated"
    # [instance size]: 50, 100, 200, 500, 1000, 2000, 5000, 10000
    # [favoured solution space]:
    # * p positive fixations
    # * n negative fixations
    # * c constraint fixations 
    # combinations are possible
    # [size of mutable parameter space]: between 0 and 1, e.g. 0.05 for 5%
    # [instance index]: between 1 and 10
    # [CE type]: 'strong' or any other string for weak CEs

    # parameters
    seed(0) # Hardcoded, if you change this, change the logging as well => tracked_data
    epsilon = 0.01
    if argv[6] == 'strong':
        strong = True
    else:
        strong = False
    favoured_solution_space_type = argv[3]
    mutable_parameter_space_size = float(argv[4])
    instance_index = int(argv[5])

    if len(favoured_solution_space_type) > 1 and strong:
        print("ERROR: Strong CFs with multiple favoured solution space types are not supported. Please choose only one of p, n or c.")

    # This captures all relevant data
    tracked_data = {"input":{'instance_type':argv[1],'instance_size':argv[2],'favoured_solution_space_types':argv[3],'mutable_parameter_space_size':argv[4],'instance_index':instance_index},"Is strong?":strong,"parameters":{"epsilon":epsilon,'strong':strong,'seed':0}}
    
    # Read in data
    if int(argv[2]) < 50:
        weights, costs, capacity = kplib_reader(argv[1], 50, 1000,instance_index)
        weights = weights[:int(argv[2])]
        costs = costs[:int(argv[2])]
        capacity = int(capacity*int(argv[2])/50)
    else:
        weights, costs, capacity = kplib_reader(argv[1], int(argv[2]), 1000,instance_index)

    # We begin with computing a nominal solution
    solution,objective,dummy = bip_solve_cover(weights,costs,capacity) 
    print("\nSolved nominal problem\nNominal solution has objective",objective,"with items",solution,"and costs",costs)

    # randomised enforcing of elements
    if 'p' in favoured_solution_space_type:
        enforced_elements = sample([item for item in range(len(weights)) if item not in solution],max(round(capacity/mean(weights)/10),1))
        print("Enforcing elements",enforced_elements,"\n")
    else:
        enforced_elements = []    
    tracked_data['enforced_elements'] = enforced_elements

    # randomised disallowal of elements
    if 'n' in favoured_solution_space_type:
        disallowed_elements = sample([item for item in range(len(weights)) if item not in enforced_elements if item in solution],max(round(capacity/mean(weights)/10),1))
        print("Disallowing elements",disallowed_elements,"\n")
    else:
        disallowed_elements = []
    tracked_data['disallowed_elements'] = disallowed_elements

    # randomised constraints on elements
    if 'c' in favoured_solution_space_type:
        constrained_set = [{'variables':sample([item for item in range(len(weights))],max(round(len(weights)/10),1)),'rhs':1}]
        print("Constraints on", constrained_set," / pick at least one.\n")
    else:
        constrained_set = []
    tracked_data['constrained_set'] = constrained_set

    timer = time()
    result = run_cf(weights,costs,capacity,strong=strong,enforced_elements=enforced_elements,disallowed_elements=disallowed_elements,constrained_set=constrained_set,max_deviation=mutable_parameter_space_size,epsilon=epsilon)
    tracked_data['result'] = result
    tracked_data['total_runtime_in_s'] = time()-timer
    name = str(instance_index)+'_'+str(argv[1])+'_'+str(argv[2])+'_1000_'+str(argv[3])+'_'+str(argv[4])+'_'+str(argv[6])
    tracked_data['instance'] = {'weights':list(weights),'costs':list(costs),'capacity':capacity}
    write_as_json(tracked_data,name)
    print("Finished execution for instance",name)