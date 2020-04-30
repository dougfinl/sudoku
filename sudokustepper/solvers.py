# -*- coding: utf-8 -*-

import itertools
from abc import ABC, abstractmethod
from copy import deepcopy

from sudokustepper.grid import Grid


class SolverDelegate:
    def on_solver_step_complete(self, grid: Grid):
        """
        Called each time a step in the solver is completed.

        :param grid: a copy of the grid from the current step
        """
        pass

    def on_solver_solved(self):
        """
        Called if the solver finds a solution to the puzzle.
        """
        pass

    def on_solver_failed(self):
        """
        Called if the solver was unable to find a solution for the puzzle.
        """
        pass


class Solver(ABC):
    def __init__(self, grid: Grid, delegate=None):
        self.grid: Grid = grid
        self.step_history = []
        self.delegate: SolverDelegate = delegate

    def _step_complete(self):
        self.step_history.append(deepcopy(self.grid))

        if self.delegate is not None:
            grid_copy = deepcopy(self.grid)
            self.delegate.on_solver_step_complete(grid_copy)

    def _solved(self):
        if self.delegate is not None:
            self.delegate.on_solver_solved()

    def _failed(self):
        if self.delegate is not None:
            self.delegate.on_solver_failed()

    @property
    def num_steps(self):
        return len(self.step_history)

    @abstractmethod
    def solve(self) -> bool:
        """
        Attempts to find a solution for the Sudoku grid.

        :returns: True if a solution has been found, otherwise False.
        """
        pass


class NaiveSolver(Solver):
    def solve(self):
        success = False

        # Initialisation
        empty_cell_coords = self.grid.empty_cell_coords()
        all_possible_cell_values = []
        for (x, y) in empty_cell_coords:
            possible_values = self.grid.possible_values_for_cell(x, y)
            all_possible_cell_values.append(possible_values)

        # Solving
        for values_to_try in itertools.product(*all_possible_cell_values):
            for i, (x, y) in enumerate(empty_cell_coords):
                self.grid.cells[y][x].value = values_to_try[i]

            if self.grid.valid:
                success = True
                break

            self._step_complete()

        if success:
            self._solved()
        else:
            self._failed()

        return success


class BacktracingSolver(Solver):
    def solve(self):
        # Find the next empty cell
        empty_cell_coords = self.grid.empty_cell_coords()
        if not empty_cell_coords:
            self._failed()
            return False

        x, y = empty_cell_coords[0]
        for possible_value in self.grid.possible_values_for_cell(x, y):
            self.grid.cells[y][x].value = possible_value

            self._step_complete()

            if self.grid.solved:
                self._solved()
                return True
            else:
                if self.solve():
                    return True

        self.grid.cells[y][x].value = 0
        return False


ALL_SOLVERS = {
    "naive": NaiveSolver,
    "backtracing": BacktracingSolver
}


def main():
    g = Grid("862341950"
             "573000800"
             "900007023"
             "009510460"
             "080602070"
             "025034100"
             "240173589"
             "008000716"
             "050986234")

    print(g)
    print("Valid? {}".format(g.valid))
    print("Solved? {}".format(g.solved))

    s = NaiveSolver(g)
    if s.solve():
        print(g)
        print("Valid? {}".format(g.valid))
        print("Solved? {}".format(g.solved))


if __name__ == "__main__":
    main()
