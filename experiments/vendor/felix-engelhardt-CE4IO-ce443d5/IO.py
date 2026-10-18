from os import getcwd
from os.path import join
from numpy import empty
import matplotlib.pyplot as plt
import json as j

def kplib_reader(
    instance_type: str = "strongly_correlated",
    size: int = 50,
    weight_ub: int = 1000,
    index: int = 0,
):
    """Reads in kplib instances.
    * Possible instance types: 'strongly_correlated', 'uncorrelated'
    * Possible sizes: 50, 100, 200, 500, 1000, 2000, 5000, 10000
    * Possible weight upper bounds; 1000, 10000
    * Possible instance index: 0, 1, ... , 99"""

    path = join(
        getcwd(),
        "data",
    )

    if instance_type not in ["strongly_correlated", "uncorrelated"]:
        return False
    elif instance_type == "strongly_correlated":
        path = join(path, "02StronglyCorrelated")
    elif instance_type == "uncorrelated":
        path = join(path, "00Uncorrelated")

    size = str(size)
    for dummy in range(5-len(str(size))):
        size = "0" + size
    size = "n" + size

    path = join(path, size)

    if weight_ub not in [1000, 10000]:
        print("here")
        return False
    elif weight_ub == 1000:
        path = join(path, "R01000")
    elif weight_ub == 10000:
        path = join(path, "R10000")

    if index not in range(100):
        print("Here")
        return False
    elif index < 10:
        path = join(path, "s00" + str(index) + ".kp")
    else:
        path = join(path, "s0" + str(index) + ".kp")

    try:
        f = open(path)
    except FileNotFoundError:
        print("Incorrect path:", path)
        return False
    else:
        with f:
            lines = f.readlines()
            weights = empty(len(lines) - 4)
            costs = empty(len(lines) - 4)
            objective = None

            for counter in range(len(lines)):
                if counter < 2 or counter == 3:
                    continue
                elif counter == 2:
                    objective = int(lines[counter].rstrip("\n"))
                else:
                    item = lines[counter].rstrip("\n").split(" ")
                    costs[counter - 4] = int(item[0])
                    weights[counter - 4] = int(item[1])
            return weights, costs, objective

def simple_CF_plot(x,y):
    plt.plot(x, y, marker='o', linestyle='-', color='b', label='Line 1')
    plt.xlabel('Candidate value')
    plt.ylabel('Solution value')
    plt.title('Counterfactuals for Knapsacks')
    plt.legend()
    plt.show()

def write_as_json(current_data,filename:str):
    """ This is used to log results. """
    with open(join('results', filename)+".json", "w") as file:
        j.dump(current_data, file)

def read_json(filename: str):
    """Read a JSON file from the 'results' directory and return its contents as a dictionary."""
    try:
        with open(join('results', filename) + ".json", "r") as file:
            return j.load(file)
    except (FileNotFoundError, j.JSONDecodeError) as e:
        print(f"Error reading the file: {e}")
        return False