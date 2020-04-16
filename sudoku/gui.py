# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import *
from grid import Cell, Grid


class CellWidget(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(2)

        self._cell = Cell()
        self.update_ui()

    def update_ui(self):
        self.setText("" if self.cell.empty else str(self.cell.value))

    @property
    def cell(self):
        return self._cell

    @cell.setter
    def cell(self, cell):
        self._cell = cell
        self.update_ui()


class GridWidget(QWidget):
    def __init__(self):
        super().__init__()

        self._grid = Grid.empty_grid()
        self._cell_widgets = None
        self.init_ui()
        self.update_ui()

    def init_ui(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        self.setLayout(grid_layout)

        # 9x9 grid of buttons
        self._cell_widgets = []
        for i in range(9):
            row = []
            for j in range(9):
                b = CellWidget()
                b.setFixedSize(50, 50)
                row.append(b)

                grid_layout.addWidget(b, i, j)
            self._cell_widgets.append(row)

    def update_ui(self):
        for i in range(9):
            for j in range(9):
                self._cell_widgets[i][j].cell = self.grid.cells[i][j]

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
        self._grid = grid
        self.update_ui()


class SudokuSolverWindow(QMainWindow):
    grid = Grid.empty_grid()

    def __init__(self):
        super().__init__()

        # TODO replace with actual solver
        self._solver_running = False

        self._grid_widget = None
        self._combo_box_algorithm = None
        self._spin_box_step_interval = None
        self._btn_start_stop_solver = None
        self._btn_step_solver = None
        self._btn_reset_solver = None
        self.init_ui()

    def init_ui(self):
        self.statusBar().showMessage("Load a grid to get started")

        main_layout = QHBoxLayout()
        w = QWidget()
        w.setLayout(main_layout)
        self.setCentralWidget(w)

        # Left side - sudoku grid
        self._grid_widget = GridWidget()
        main_layout.addWidget(self._grid_widget)

        # Right side - options
        options_layout = QFormLayout()
        main_layout.addLayout(options_layout)

        self._combo_box_algorithm = QComboBox()
        self._combo_box_algorithm.setEnabled(False)
        self._combo_box_algorithm.addItems(["Naive"])
        self._combo_box_algorithm.setCurrentIndex(0)
        options_layout.addRow("Algorithm", self._combo_box_algorithm)

        self._spin_box_step_interval = QSpinBox()
        self._spin_box_step_interval.setEnabled(False)
        self._spin_box_step_interval.setMaximum(1000)
        options_layout.addRow("Step Interval (ms)", self._spin_box_step_interval)

        self._btn_start_stop_solver = QPushButton("Solve!")
        self._btn_start_stop_solver.setEnabled(False)
        self._btn_start_stop_solver.clicked.connect(self.start_stop_solver)
        options_layout.addRow(self._btn_start_stop_solver)

        self._btn_step_solver = QPushButton("Step")
        self._btn_step_solver.setEnabled(False)
        options_layout.addRow(self._btn_step_solver)

        self._btn_reset_solver = QPushButton("Reset")
        self._btn_reset_solver.setEnabled(False)
        options_layout.addRow(self._btn_reset_solver)

        divider = QFrame()
        divider.setFrameStyle(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        options_layout.addRow(divider)

        load_grid_button = QPushButton("Load Grid...")
        load_grid_button.clicked.connect(self.load_grid_dialog)
        options_layout.addRow(load_grid_button)

    def grid_loaded(self):
        self._combo_box_algorithm.setEnabled(True)
        self._spin_box_step_interval.setEnabled(True)
        self._btn_start_stop_solver.setEnabled(True)
        self._btn_step_solver.setEnabled(True)
        self._btn_reset_solver.setEnabled(True)

        self.statusBar().showMessage("Grid loaded")
        self._grid_widget.grid = self.grid

    @pyqtSlot()
    def load_grid_dialog(self):
        grid_str, ok = QInputDialog.getText(self, "Load Sudoku Grid", "81-char string:", QLineEdit.Normal, "")
        if ok and len(grid_str) == 81:
            self.grid = Grid(grid_str)
            self.grid_loaded()

    @pyqtSlot()
    def start_stop_solver(self):
        # TODO start solver running
        if self._solver_running:
            # TODO stop the solver
            self._solver_running = False
            self._btn_start_stop_solver.setText("Solve!")
        else:
            # TODO start the solver
            self._solver_running = True
            self._btn_start_stop_solver.setText("Stop")


def main():
    import sys
    app = QApplication(sys.argv)
    w = SudokuSolverWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
