# Importing libraries
from optilog.solvers.sat import Glucose41
from itertools import combinations
import subprocess
import copy
import sys
import os

# Maps a cell's coordinates (i, j) and value (c) to a unique variable
def cell_to_variable(i, j, c):
    return 81 * i + 9 * j + c

# Maps a variable back to its cell coordinates (i, j, c)
def variable_to_cell(var):
    i = (var - 1) // 81
    j = ((var - 1) % 81) // 9
    c = ((var - 1) % 9) + 1
    return (i, j, c)

# Generates a list representing the "at least one" constraint for a set of variables
def at_least_one(vars):
    return vars[:]

# Generates clauses ensuring uniqueness within a set of variables
def unique(vars):
    L = [vars]
    for c in combinations(vars, 2):
        intermediate_list = list(c)
        for i in range(0, len(intermediate_list)):
            intermediate_list[i] = -intermediate_list[i]
        L.append(intermediate_list)
    return L

# Generates constraints for each cell in the Sudoku grid
def create_cell_constraints():
    L = []
    for i in range(0, 9):
        for j in range(0, 9):
            intermediate_list = []
            for c in range(1, 10):
                var = cell_to_variable(i, j, c)
                intermediate_list.append(var)
            L = L + unique(intermediate_list)
    return L

# Generates constraints for each row in the Sudoku grid
def create_line_constraints():
    L = []
    for c in range(1, 10):
        for i in range(0, 9):
            intermediate_list = []
            for j in range(0, 9):
                var = cell_to_variable(i, j, c)
                intermediate_list.append(var)
            L.append(intermediate_list)
    return L

# Generates constraints for each column in the Sudoku grid
def create_column_constraints():
    L = []
    for c in range(1, 10):
        for j in range(0, 9):
            intermediate_list = []
            for i in range(0, 9):
                var = cell_to_variable(i, j, c)
                intermediate_list.append(var)
            L.append(intermediate_list)
    return L

# Generates constraints for each 3x3 box in the Sudoku grid
def create_box_constraints():
    L = []
    for c in range(1, 10):
        for i in range(0, 3):
            for j in range(0, 3):
                clause = [[3 * i, 3 * j, c], [3 * i, 3 * j + 1, c], [3 * i, 3 * j + 2, c],
                          [3 * i + 1, 3 * j, c], [3 * i + 1, 3 * j + 1, c], [3 * i + 1, 3 * j + 2, c],
                          [3 * i + 2, 3 * j, c], [3 * i + 2, 3 * j + 1, c], [3 * i + 2, 3 * j + 2, c]]
                intermediate_list = []
                for k in clause:
                    var = cell_to_variable(k[0], k[1], k[2])
                    intermediate_list.append(var)
                L.append(intermediate_list)
    return L

# Generates constraints based on the initial values in the Sudoku grid
def create_value_constraints(grid):
    L = []
    for i in range(0, 9):
        for j in range(0, 9):
            if grid[i][j] != 0:
                var = cell_to_variable(i, j, grid[i][j])
                L.append(var)
    return L

# Combines all constraints to create the SAT problem for the given Sudoku grid
def generate_problem(grid):
    L = create_cell_constraints() + create_line_constraints() + create_column_constraints() + create_box_constraints() + create_value_constraints(grid)
    return L

# Adds clauses to the SAT solver
def clauses_to_solver(clauses, solver):
    for clause in clauses:
        if isinstance(clause, int):
            clause = [clause]
        solver.add_clause(clause)
    return solver

# Converts the SAT model to a Sudoku grid
def model_to_grid(model, nb_vals=9):
    grid = []
    for _ in range(0, nb_vals):
        grid.append([0, 0, 0, 0, 0, 0, 0, 0, 0])
    for var in model:
        if var > 0:
            cell = variable_to_cell(var)
            grid[cell[0]][cell[1]] = cell[2]
    return grid

# Displays the Sudoku grid
def grid_display(grid):
    line_counter = 0
    for line in grid:
        if line_counter % 3 == 0:
            print('-------------------------------')
        line_counter += 1
        display_line = ''
        column_counter = 0
        for element in line:
            if column_counter % 3 == 0:
                display_line += '|'
            if element == 0:
                display_line += ' . '
            else:
                display_line += ' ' + str(element) + ' '
            column_counter += 1
        display_line += '|'
        print(display_line)
    print('--------------------------------')

# Solves the SAT problem and displays the result
def find_model(clauses):
    solver = Glucose41()
    solver = clauses_to_solver(clauses, solver)
    solver.solve()
    model = solver.model()
    return model, solver

# Computes the negation of a clause
def negation(clause):
    neg_clause = copy.deepcopy(clause)
    for i in range(0, len(neg_clause)):
        neg_clause[i] = -neg_clause[i]
    return neg_clause

# Displays the resolution of the Sudoku grid
def display_resolution(problem_grid, solution, solution_grid):
    print("\n\nInitial Problem\n")
    grid_display(problem_grid)
    print("\n\nSolved Problem\n")
    print(solution + "\n")
    if solution == "UNIQUE SOLUTION":
        print(grid_display(solution_grid))

# Solves the Sudoku grid and displays the result
def grid_resolution(problem_grid, display):
    solution = ""
    clauses = generate_problem(problem_grid)
    model, solver = find_model(clauses)
    if model == []:
        solution = "NO SOLUTION"
        if display:
            display_resolution(problem_grid, solution, None)
        return solution, None
    else:
        # Add a blocking clause to exclude the found model
        blocking_clause = [-literal for literal in model]
        solver.add_clause(blocking_clause)
        solver.solve()
        new_model = solver.model()
        if new_model == []:
            solution = "UNIQUE SOLUTION"
            solution_grid = model_to_grid(model)
            if display:
                display_resolution(problem_grid, solution, solution_grid)
            return solution, solution_grid
        else:
            solution = "MULTIPLE SOLUTIONS"
            if display:
                display_resolution(problem_grid, solution, None)
            return solution, None

# Converts stdin to a Sudoku problem grid
def stdin_to_problem_grid(stdin):
    problem_grid = []
    for line in stdin.split('\n'):
        row = []
        for char in line:
            if char.isdigit():
                row.append(int(char))
            else:
                row.append(0)
        problem_grid.append(row)
    return problem_grid

# Converts solution grid to stdout format
def solution_grid_to_stdout(solution_grid):
    stdout = ""
    for row in solution_grid:
        for num in row:
            if num != 0:
                stdout += str(num)
            else:
                stdout += "."
        stdout += "\n"
    return stdout.strip()

# Recovers input from the user
def input_recovery():
    stdin = str(input())
    for i in range(0, 8):
        stdin += "\n" + str(input())
    return stdin

# Main function to execute the Sudoku solver
def main():
    stdin = input_recovery()
    problem_grid = stdin_to_problem_grid(stdin)
    (solution, solution_grid) = grid_resolution(problem_grid, display=False)
    if solution == "UNIQUE SOLUTION":
        stdout = solution_grid_to_stdout(solution_grid)
        print(stdout)
    else:
        print(solution)

# Call to the main function to start the Sudoku solver
main()
