# -*- coding: utf-8 -*-

from typing import List


class Cell:
    def __init__(self, value=0, locked=False):
        """
        Creates a cell with a specific value.
        :param value: must be between 0 and 9 inclusive
        :param locked: set to True if the cell value should be read-only, unless the value is 0 (empty), in which case
                       the cell cannot be locked and this value will be ignored
        """
        if value not in range(10):
            raise ValueError("cell value must be between 0 and 9 inclusive")

        self._value = value
        self.valid: bool = True

        # Only lock the cell if the value is non-zero
        if value == 0:
            self._locked = False
        else:
            self._locked = locked

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not self._locked and value in range(10):
            self._value = value

    @property
    def empty(self):
        return self.value == 0

    @property
    def locked(self):
        return self._locked

    def lock(self):
        if not self.empty:
            self._locked = True

    def unlock(self):
        self._locked = False

    def __eq__(self, o):
        if isinstance(o, Cell):
            return self.value == o.value
        return False

    def __hash__(self):
        return self.value

    def __str__(self):
        return " " if self.value == 0 else str(self.value)

    def __repr__(self):
        return "<Cell value:%d>" % self.value


class Grid:
    def __init__(self, grid_string: str = None):
        cells: List[List[Cell]] = []
        for i in range(9):
            row = []
            for j in range(9):
                row.append(Cell(0))
            cells.append(row)

        self.cells = cells
        self._valid = True

        if grid_string is not None:
            self.grid_string = grid_string

    @property
    def grid_string(self) -> str:
        result = []
        for cell in self.flattened():
            result.append(str(cell.value))

        return "".join(result)

    @grid_string.setter
    def grid_string(self, string: str):
        if len(string) != 81:
            raise ValueError("length of values must be 81")

        for i, cell in enumerate(self.flattened()):
            cell.unlock()
            cell.value = int(string[i])
            cell.lock()

        self.validate()

    def row(self, i) -> []:
        """
        Returns cells in the row at index i.
        :param i: the row index, counting from top to bottom
        :returns: a list of 9 cells
        """
        if i not in range(9):
            raise ValueError("i must be between 0 and 8 inclusive")
        row = self.cells[i]
        assert len(row) == 9

        return row

    def col(self, i) -> [Cell]:
        """
        Returns cells in the column at index i.

        :param i: the row index, counting from left to right

        :returns: a list of 9 cells
        """
        if i not in range(9):
            raise ValueError("i must be between 0 and 8 inclusive")
        col = [row[i] for row in self.rows()]
        assert len(col) == 9

        return col

    def box(self, i) -> [Cell]:
        """
        Returns cells in the box at index i.

        :param i: the box index, counting across from the top-left to
                  bottom-right

        :returns: a list of 9 cells, ordered across from top-left to
                  bottom-right
        """
        if i not in range(9):
            raise ValueError("i must be between 0 and 8 inclusive")
        row_start = 3 * (i // 3)
        col_start = 3 * (i % 3)
        box = []
        for row_i in range(row_start, row_start + 3):
            for col_i in range(col_start, col_start + 3):
                box.append(self.cells[row_i][col_i])

        return box

    def rows(self) -> [[Cell]]:
        """
        Returns a list of rows in the grid, ordered from top to bottom.

        :returns: a list of 9 rows, where each row is a list of 9 cells
        """
        rows = []
        for i in range(9):
            rows.append(self.row(i))

        return rows

    def cols(self) -> [[Cell]]:
        """
        Returns a list of columns in the grid, ordered from left to right.

        :returns: a list of 9 columns, where each column is a list of 9 cells
        """
        cols = []
        for i in range(9):
            cols.append(self.col(i))

        return cols

    def boxes(self) -> [[Cell]]:
        """
        Returns a list of 3x3 boxes in the grid, ordered from left-to-right
        then top-to-bottom

        :returns: a list of 9 boxes, where each box is a list of 9 cells
        """
        boxes = []
        for i in range(9):
            boxes.append(self.box(i))

        return boxes

    def flattened(self):
        return [cell for row in self.cells for cell in row]

    def empty_cell_coords(self) -> [(int, int)]:
        """
        Finds all empty cells in the grid.

        :returns: a list of coordinate tuples (x, y) of the grid's empty cells
        """
        coords = []
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].empty:
                    coords.append((j, i))

        return coords

    @property
    def valid(self) -> bool:
        """
        :returns: True if the board is valid, otherwise False
        """
        self.validate()
        return self._valid

    def validate(self):
        """
        Validates cell values in the board, and sets the valid property to True if valid, otherwise False. Empty cells
        are ignored, thus the board is valid if empty.

        The board is valid if all of the following conditions are true:
            * each column contains the numbers 1-9 or blank cells, with no
              repeated values
            * each row follows the same rule
            * each 3x3 box follows the same rule
        """
        # Reset valid flag of all cells
        for cell in self.flattened():
            cell.valid = True

        # Get all cell groups, and remove the empty cells (we don't care about these)
        cell_groups = self.rows() + self.cols() + self.boxes()
        cell_groups = [
            [c for c in cells if not c.empty] for cells in cell_groups
        ]

        valid = True
        for cell_group in cell_groups:
            # Flag the duplicate cells in this cell group
            # TODO: make this algorithm more efficient
            seen_cells = set()
            for cell in cell_group:
                if cell in seen_cells:
                    valid &= False
                    cell.valid = False
                    # Also set the 'seen' cell as invalid
                    for c in seen_cells:
                        if c == cell:
                            c.valid = False
                            break
                seen_cells.add(cell)

        self._valid = valid

    @property
    def solved(self) -> bool:
        """
        Ensures all cells are populated, before checking if the grid is valid.

        :returns: True if the grid is solved, otherwise False
        """
        for row in self.cells:
            for cell in row:
                if cell.empty:
                    return False
        return self.valid

    def possible_values_for_cell(self, x: int, y: int) -> set:
        """
        Returns a set of the possible values for a specific cell.

        :param x: the cell's x coordinate, between 0 and 8 inclusive
        :param y: the cell's y coordinate, between 0 and 8 inclusive

        :returns: a set of possible values for the cell at (x, y)
        """
        row_values = set([cell.value for cell in self.row(y)])
        col_values = set([cell.value for cell in self.col(x)])
        box_index = 3 * (y // 3) + x // 3
        box_values = set([cell.value for cell in self.box(box_index)])

        values = set(range(1, 10)) - row_values - col_values - box_values
        return values

    @property
    def empty(self) -> bool:
        result = True
        for cell in self.flattened():
            result &= cell.empty
        return result

    def __eq__(self, o):
        if isinstance(o, Grid):
            return self.cells == o.cells
        return False

    def __str__(self):
        s = ""
        for i, row in enumerate(self.cells):
            if i == 0:
                s += "┌" + "─" * 9 + "┬" + "─" * 9 + "┬" + "─" * 9 + "┐\n"
            elif i % 3 == 0:
                s += "├" + "─" * 9 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┤\n"
            for j, cell in enumerate(row):
                if j % 3 == 0:
                    s += "│"
                s += f" {cell} "
            s += "│\n"
        s += "└" + "─" * 9 + "┴" + "─" * 9 + "┴" + "─" * 9 + "┘"

        return s


if __name__ == "__main__":
    g = Grid("123456789" * 9)
    print(g)
