# -*- coding: utf-8 -*-


class Cell:
    value = 0

    def __init__(self, value=0):
        if value not in range(10):
            raise ValueError("cell value must be between 0 and 9 inclusive")

        self.value = value

    def __str__(self):
        return " " if self.value == 0 else str(self.value)

    def __repr__(self):
        return "<Cell value:%d>" % self.value


class Grid:
    cells = []

    def __init__(self, cells):
        if len(cells) != 81:
            raise ValueError("length of values must be 81")

        cells = [Cell(int(c)) for c in cells]

        # Convert to a 2-dimensional list
        self.cells = [cells[i:i+9] for i in range(0, 81, 9)]

    @classmethod
    def emptygrid(cls):
        return cls("0" * 81)

    def __str__(self):
        s = ""
        for i, row in enumerate(self.cells):
            if i == 0:
                s += "┌" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*9 + "┐\n"
            elif i % 3 == 0:
                s += "├" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*9 + "┤\n"
            for j, cell in enumerate(row):
                if j % 3 == 0:
                    s += "│"
                s += f" {cell} "
            s += "│\n"
        s += "└" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*9 + "┘"

        return s


if __name__ == "__main__":
    g = Grid("123456789"*9)
    print(g)
