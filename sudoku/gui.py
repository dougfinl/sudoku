# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, Qt, QSize, QPropertyAnimation
from PyQt5.QtWidgets import *
from grid import Cell, Grid
from solvers import SolverDelegate, NaiveSolver
from copy import deepcopy


class CellWidget(QLabel):
    locked_cell_style = """
        QLabel {
            color: #000000;
            background-color: #e0e0e0;
            font-size: 14pt;
            border: 1px solid #a0a0a0;
        }
    """

    unlocked_cell_style = """
        QLabel {
            color: blue;
            background-color: #f8f8f8;
            font-size: 14pt;
            border: 1px solid #a0a0a0;
        }
    """

    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(self.locked_cell_style)

        self._cell = Cell()
        self.update_ui()

    def update_ui(self):
        self.setText("" if self.cell.empty else str(self.cell.value))
        self.setStyleSheet(self.locked_cell_style if self.cell.locked else self.unlocked_cell_style)

    def minimumSizeHint(self):
        return QSize(50, 50)

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


class SudokuSolverWindow(QMainWindow, SolverDelegate):
    grid = Grid.empty_grid()
    original_grid = Grid.empty_grid()

    def __init__(self):
        super().__init__()

        self._solver = None

        self._grid_widget = None
        self._combo_box_algorithm = None
        self._spin_box_step_interval = None
        self._btn_start_solver = None
        self._btn_stop_solver = None
        # self._btn_step_solver = None
        self._btn_reset_solver = None
        self._btn_load_grid = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sudoku Solver")
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
        self._spin_box_step_interval.setValue(100)
        self._spin_box_step_interval.valueChanged.connect(self.step_interval_changed)
        options_layout.addRow("Step Interval (ms)", self._spin_box_step_interval)

        self._btn_start_solver = QPushButton("Start")
        self._btn_start_solver.setEnabled(False)
        self._btn_start_solver.clicked.connect(self.start_solver)
        options_layout.addRow(self._btn_start_solver)

        self._btn_stop_solver = QPushButton("Stop")
        self._btn_stop_solver.setEnabled(False)
        self._btn_stop_solver.clicked.connect(self.stop_solver)
        options_layout.addRow(self._btn_stop_solver)

        # self._btn_step_solver = QPushButton("Step")
        # self._btn_step_solver.setEnabled(False)
        # options_layout.addRow(self._btn_step_solver)

        self._btn_reset_solver = QPushButton("Reset")
        self._btn_reset_solver.setEnabled(False)
        self._btn_reset_solver.clicked.connect(self.reset_solver)
        options_layout.addRow(self._btn_reset_solver)

        divider = QFrame()
        divider.setFrameStyle(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        options_layout.addRow(divider)

        self._btn_load_grid = QPushButton("Load Grid...")
        self._btn_load_grid.clicked.connect(self.load_grid_dialog)
        options_layout.addRow(self._btn_load_grid)

    def load_grid(self, grid: Grid):
        self.original_grid = deepcopy(grid)
        self.grid = grid
        self._grid_widget.grid = grid
        self._grid_widget.update_ui()

        self._combo_box_algorithm.setEnabled(True)
        self._spin_box_step_interval.setEnabled(True)
        self._btn_start_solver.setEnabled(True)
        # self._btn_step_solver.setEnabled(True)
        self._btn_reset_solver.setEnabled(True)

        self.statusBar().showMessage("Grid loaded")

    def on_solver_step(self):
        self.statusBar().showMessage("Running step {}".format(self._solver.steps + 1))

    def on_solver_step_complete(self):
        self._grid_widget.update_ui()

    @pyqtSlot()
    def load_grid_dialog(self):
        grid_str, ok = QInputDialog.getText(self, "Load Sudoku Grid", "81-char string:", QLineEdit.Normal, "")
        if ok and len(grid_str) == 81:
            self.load_grid(Grid(grid_str))

    @pyqtSlot()
    def step_interval_changed(self):
        if self._solver is not None:
            self._solver.step_interval = self._spin_box_step_interval.value()

    @pyqtSlot()
    def start_solver(self):
        self._combo_box_algorithm.setEnabled(False)
        self._btn_start_solver.setEnabled(False)
        self._btn_load_grid.setEnabled(False)
        self._btn_stop_solver.setEnabled(True)
        self._solver = NaiveSolver(self.grid)
        self._solver.delegate = self
        self._solver.step_interval = self._spin_box_step_interval.value()
        self._solver.start()

    @pyqtSlot()
    def stop_solver(self):
        if self._solver is None:
            return

        self.statusBar().showMessage("Stopping...")
        self._btn_stop_solver.setEnabled(False)
        # Repaint the window immediately, before self._solver.stop() blocks
        self.repaint()

        self._solver.stop()

        self.statusBar().showMessage("")
        self._btn_start_solver.setEnabled(True)
        self._combo_box_algorithm.setEnabled(True)
        self._btn_load_grid.setEnabled(True)

    @pyqtSlot()
    def reset_solver(self):
        self.stop_solver()
        self.load_grid(self.original_grid)

    def closeEvent(self, event):
        self.stop_solver()
        event.accept()


def main():
    import sys

    app = QApplication(sys.argv)
    w = SudokuSolverWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
