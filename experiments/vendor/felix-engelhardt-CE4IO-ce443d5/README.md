# Counterfactual Explanations for Integer Optimization Problems (CE4IO)

## Description

This repository contains code for the paper **Counterfactual Explanations for Integer Optimization Problems** by - [Felix Engelhardt](https://www.opt.tu-darmstadt.de/opt/team_opt/felix_engelhardt.en.jsp), [Jannis Kurtz](https://github.com/JannisKu), [S. Ilker Birbil](https://sibirbil.github.io/) and [Ted Ralphs](https://github.com/tkralphs).

The implementation contains one main file to compute different counterfactual explanations for knapsack instances from [klib](https://github.com/likr/kplib). This was the basis for our main computational study. csp.ipynb is a jupyter notebook containing the code for the example given in Subsection "5.3 An Application to the Resource Constrained Shortest Path Problem". It is meant as an interactive tool to compute simple counterfactual explanations. 

## Using the repository

Python is required to run the code, we use the sys, random, time, statistics, os, matplotlib, json ana time packages as well as numpy and networkx. For executing integer linear programs, you also have to have Gurobi + gurobipy installed. Check their website for current installation guidelines. 

Then, clone the repository and use a terminal to navigate to the branching folder. You will find five files

- *solver.py* contains functions that are executed in main.py.
- *main.py* contains the algorithm. This is excecutable as a main file.
- *IO.py* has functions that deal with reading and writing data.
- *csp.ipynb* is an interactive example for the RCSP problem.

Thus, to generate results you need to either execute *csp.ipynb* or *main.py*. Either logs the algorithm's progress in the terminal and produces a results file that is automatically saved in the *results* folder. That folder already contains all results from our computaitonal study, which can be used for verification.

To execute *main.py*  you will have to enter something like this

`python3 main.py 'uncorrelated' 10 'p' 0.05 12 strong`

This represents computing a counterfactual explanation for the following features 

`python3 main.py [instance type] [instance size] [favoured solution space] [size of mutable parameter space] [instance index] [CE type]`

The meaning of all possible parameters is given in comments in the main file. 

## Data

We thank Yosuke Onoue, who build and hosts the [klib](https://github.com/likr/kplib) knapsack instance library. Their instances are based on:

Kellerer, H., Pferschy, U., & Pisinger, D. (2004). Exact solution of the knapsack problem. In Knapsack Problems (pp. 117-160). Springer, Berlin, Heidelberg. [https://doi.org/10.1007/978-3-540-24777-7_5](https://doi.org/10.1007/978-3-540-24777-7_5)

The ressource constrained shortest path instances were taken from [pathwyse](https://github.com/pathwyse/pathwyse):

Salani, M., Basso, S., & Giuffrida, V. (2024). PathWyse: a flexible, open-source library for the resource constrained shortest path problem. Optimization Methods and Software, 1–23. [https://doi.org/10.1080/10556788.2023.2296978](https://doi.org/10.1080/10556788.2023.2296978)

## Questions
Feel free to write to the corresponding author [Mr. Felix Engelhardt](mailto:felix.engelhardt@rwth-aachen.de) if you have any questions.

## Acknowledgments
Computations were performed with computing resources granted by RWTH Aachen University High Performance computing.
We thank Christina Büsing and Hector Geffner for enabling this research collaboration, as well as Christoph Grüne for insightful discussions on complexity theory.

## License
All code is under a GNU Affero General Public License v3.0 only.