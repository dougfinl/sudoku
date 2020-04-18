import itertools

from grid import Grid
from abc import ABC, abstractmethod
import threading
import time


class SolverDelegate:
    def on_solver_step(self):
        pass

    def on_solver_step_complete(self):
        pass


class BaseSolver(ABC):
    grid: Grid = None
    step_interval: int = 0
    steps: int = 0

    delegate: SolverDelegate = None

    def __init__(self, grid: Grid):
        self.grid = grid

        self._solver_thread = threading.Thread(target=self._solve_loop)
        self._should_stop = False

    def start(self):
        if self.running:
            return

        self.steps = 0
        self.init_solver()
        self._should_stop = False
        self._solver_thread.start()

    def _solve_loop(self):
        while not self._should_stop:
            self._run_step()
            time.sleep(self.step_interval / 1000)

    @abstractmethod
    def init_solver(self):
        pass

    def stop(self):
        if self._solver_thread.is_alive():
            self._should_stop = True
            self._solver_thread.join()

    def _run_step(self) -> bool:
        if self.delegate is not None:
            self.delegate.on_solver_step()

        self.steps += 1
        success = self.step()

        if self.delegate is not None:
            self.delegate.on_solver_step_complete()

        return success

    @abstractmethod
    def step(self) -> bool:
        """
        Runs a single iteration of the solving algorithm.

        :returns: True if the step completed successfully, otherwise False (usually because there are no more steps to
                  run)
        """
        pass

    @property
    def running(self):
        return self._solver_thread.is_alive()


class NaiveSolver(BaseSolver):
    def __init__(self, grid: Grid):
        super().__init__(grid)
        self._possible_values_combinations = None
        self._empty_cell_coords = None

    def init_solver(self):
        self._empty_cell_coords = []
        all_possible_values = []

        for i in range(9):
            for j in range(9):
                if self.grid.cells[i][j].empty:
                    self._empty_cell_coords.append((i, j))
                    possible_values = self.grid.possible_values_for_cell(i, j)
                    all_possible_values.append(possible_values)

        self._possible_values_combinations = itertools.product(*all_possible_values)

    def step(self) -> bool:
        success = True
        try:
            values_to_try = next(self._possible_values_combinations)

            # Plug the values back in to the empty cells
            value_index = 0
            for coord in self._empty_cell_coords:
                x = coord[0]
                y = coord[1]
                self.grid.cells[x][y].value = values_to_try[value_index]
                value_index += 1
        except StopIteration:
            success = False

        return success
