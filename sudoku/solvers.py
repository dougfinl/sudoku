from abc import ABC, abstractmethod


class BaseSolver(ABC):
    grid = None

    steps = 0

    def __init__(self, grid):
        self.grid = grid

    def solve(self) -> bool:
        """
        Attempts to solve the sudoku puzzle.

        :returns: True if successful, otherwise False
        """
        while not self.solved:
            success = self.step()
            if not success:
                return False
        return True

    @abstractmethod
    def step(self):
        """
        Runs a single iteration of the solving algorithm.

        :returns: False if there are no more steps available to take, otherwise
                  True
        """
        self.steps += 1
