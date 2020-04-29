# -*- coding: utf-8 -*-


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
    def __init__(self, cell_values):
        if len(cell_values) != 81:
            raise ValueError("length of values must be 81")

        cells = [Cell(int(c), locked=True) for c in cell_values]

        # Convert to a 2-dimensional list
        self.cells = [cells[i: i + 9] for i in range(0, 81, 9)]

    @classmethod
    def empty_grid(cls):
        return cls("0" * 81)

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
        Validates cell values in the board. Empty cells are ignored, thus the
        board is valid if empty.

        The board is valid if all of the following conditions are true:
            * each column contains the numbers 1-9 or blank cells, with no
              repeated values
            * each row follows the same rule
            * each 3x3 box follows the same rule

        :returns: True if the board is valid, otherwise False
        """
        cell_groups = self.rows() + self.cols() + self.boxes()

        # Drop empty cells
        cell_groups = [
            [c for c in cells if not c.empty] for cells in cell_groups
        ]
        # Convert each cell group to a set (removes duplicates)
        cell_sets = [set(x) for x in cell_groups]

        result = True
        for cell_group, cell_set in zip(cell_groups, cell_sets):
            # If there were any duplicate cells in a cell group, then the set
            # representation of that group will contain fewer values
            if len(cell_group) != len(cell_set):
                result = False
                break

        return result

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
