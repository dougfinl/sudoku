# -*- coding: utf-8 -*-

import threading
from copy import deepcopy
from typing import List, Optional

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, Qt, QSize, QTimer, QFile, QTextStream, QObject, QEvent
from PyQt5.QtGui import QKeyEvent, QKeySequence, QMouseEvent, QPaintEvent, QShowEvent
from PyQt5.QtWidgets import *

from sudokustepper import solvers
from sudokustepper.grid import Cell, Grid


class CellWidget(QLabel):
    on_edited = pyqtSignal()
    on_selected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._cell: Cell = Cell()
        self._locked: bool = False
        self._valid: bool = True
        self._selected: bool = False
        self._editable: bool = False
        self.x_coord: int = -1
        self.y_coord: int = -1

        self.setAlignment(Qt.AlignCenter)

    def minimumSizeHint(self):
        return QSize(50, 50)

    @property
    def cell(self) -> Cell:
        return self._cell

    @cell.setter
    def cell(self, cell) -> None:
        self._cell = cell
        self.update()

    def paintEvent(self, e: QPaintEvent) -> None:
        self._locked = self._cell.locked
        self._valid = self._cell.valid

        t = "" if self.cell.empty else str(self.cell.value)
        self.setText(t)

        # Qt trick to reload the QSS style for this widget
        self.style().unpolish(self)
        self.style().polish(self)

        super().paintEvent(e)

    @pyqtProperty(bool)
    def valid(self) -> bool:
        return self._valid

    @pyqtProperty(bool)
    def locked(self) -> bool:
        return self._locked

    @pyqtProperty(bool)
    def selected(self) -> bool:
        return self._selected

    def select(self) -> None:
        if self._editable:
            self._cell.unlock()
            self._selected = True
            self.on_selected.emit()
            self.update()

    def deselect(self) -> None:
        self._selected = False
        self._cell.lock()
        self.update()

    def mousePressEvent(self, e: QMouseEvent):
        self.select()

    @pyqtProperty(bool)
    def editable(self) -> bool:
        return self._editable

    @editable.setter
    def editable(self, editable: bool) -> None:
        self._editable = editable
        if not editable:
            self.deselect()


class GridWidget(QWidget):
    on_edited = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._selected_cell: Optional[CellWidget] = None
        self._grid = Grid()
        self._cell_widgets: List[List[CellWidget]] = []
        self._editable: bool = False
        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        self.setLayout(grid_layout)

        # 9x9 grid of buttons
        for i in range(9):
            row = []
            for j in range(9):
                w = CellWidget()
                w.x_coord = j
                w.y_coord = i
                w.cell = self._grid.cells[i][j]
                w.on_selected.connect(self.cell_selected)
                w.on_edited.connect(self.on_edited)
                if (i // 3 + j // 3) % 2 != 0:
                    w.setProperty("class", "alternate")
                row.append(w)
                grid_layout.addWidget(w, i, j)
            self._cell_widgets.append(row)

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
        self._grid = grid
        for i in range(9):
            for j in range(9):
                self._cell_widgets[i][j].cell = self._grid.cells[i][j]
        self.update()

    @pyqtProperty(bool)
    def editable(self) -> bool:
        return self._editable

    @editable.setter
    def editable(self, editable: bool) -> None:
        if editable:
            self.setFocusPolicy(Qt.StrongFocus)

        self._editable = editable
        for row in self._cell_widgets:
            for cell_widget in row:
                cell_widget.editable = editable
        self.update()

    @pyqtSlot()
    def cell_selected(self) -> None:
        self.deselect_current_cell()
        self._selected_cell = self.sender()

    def deselect_current_cell(self) -> None:
        if self._selected_cell is not None:
            self._selected_cell.deselect()
        self._selected_cell = None

    def select_cell_at(self, x: int, y: int) -> None:
        self.deselect_current_cell()

        # Wrap the coordinates to the grid size
        x %= 9
        y %= 9
        self._cell_widgets[y][x].select()

    def select_next_cell(self) -> None:
        selected_cell = self._selected_cell
        if selected_cell is None:
            return
        if selected_cell.x_coord == 8 and selected_cell.y_coord == 8:
            self.deselect_current_cell()
            return

        x = selected_cell.x_coord
        y = selected_cell.y_coord
        x += 1
        y += max(x // 9, 0)
        x %= 9
        self.select_cell_at(x, y)

    def select_prev_cell(self) -> None:
        selected_cell = self._selected_cell
        if selected_cell is None:
            return
        if selected_cell.x_coord == 0 and selected_cell.y_coord == 0:
            self.deselect_current_cell()
            return

        x = selected_cell.x_coord
        y = selected_cell.y_coord
        x -= 1
        y += max(x // 9, -1)
        x %= 9
        self.select_cell_at(x, y)

    def eventFilter(self, o: QObject, e: QEvent) -> bool:
        if e.type() == QEvent.KeyPress:
            k = e.key()
            if self._editable and (Qt.Key_0 <= k <= Qt.Key_9 or Qt.Key_Up <= k <= Qt.Key_Down or
                                   k == Qt.Key_Backspace or k == Qt.Key_Delete):
                return True
            else:
                super().eventFilter(o, e)
        else:
            super().eventFilter(o, e)

    def keyPressEvent(self, e: QKeyEvent):
        if not self._editable or self._selected_cell is None:
            super().keyPressEvent(e)
            return

        k = e.key()
        if k == Qt.Key_Left:
            self.select_cell_at(self._selected_cell.x_coord - 1, self._selected_cell.y_coord)
        elif k == Qt.Key_Right:
            self.select_cell_at(self._selected_cell.x_coord + 1, self._selected_cell.y_coord)
        elif k == Qt.Key_Up:
            self.select_cell_at(self._selected_cell.x_coord, self._selected_cell.y_coord - 1)
        elif k == Qt.Key_Down:
            self.select_cell_at(self._selected_cell.x_coord, self._selected_cell.y_coord + 1)
        elif Qt.Key_0 <= k <= Qt.Key_9:
            self._selected_cell.cell.value = int(QKeySequence(k).toString())
            self.select_next_cell()
            self.on_edited.emit()
        elif k == Qt.Key_Backspace:
            self.select_prev_cell()
            self._selected_cell.cell.value = 0
            self.on_edited.emit()
        elif k == Qt.Key_Delete:
            self._selected_cell.cell.value = 0
            self.on_edited.emit()
        else:
            super().keyPressEvent(e)


class PlaybackControlsWidget(QWidget):
    step_selected = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._step)

        self._slider_steps = None
        self._lbl_end_step = None
        self._btn_play_pause = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        #
        # Top layout - scrubbing slider
        #
        scrubbing_layout = QHBoxLayout()
        main_layout.addLayout(scrubbing_layout)

        lbl_start_step = QLabel("Original")

        self._slider_steps = QSlider(Qt.Horizontal)
        self._slider_steps.valueChanged.connect(self.step_selected)
        self._slider_steps.sliderMoved.connect(self.pause)  # If the user manually drags the slider, pause playback
        self._slider_steps.setMinimum(0)
        self._slider_steps.setSingleStep(1)

        self._lbl_end_step = QLabel("?")

        scrubbing_layout.addWidget(lbl_start_step)
        scrubbing_layout.addWidget(self._slider_steps)
        scrubbing_layout.addWidget(self._lbl_end_step)

        #
        # Bottom layout - playback control buttons
        #
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        btn_rewind = QPushButton("<<<")
        btn_rewind.clicked.connect(self.rewind)

        btn_step_back = QPushButton("<")
        btn_step_back.clicked.connect(self.step_back)

        self._btn_play_pause = QPushButton("Play")
        self._btn_play_pause.clicked.connect(self.toggle_play_pause)

        btn_step_next = QPushButton(">")
        btn_step_next.clicked.connect(self.step)
        btn_fast_forward = QPushButton(">>>")
        btn_fast_forward.clicked.connect(self.fastforward)

        controls_layout.addWidget(btn_rewind)
        controls_layout.addWidget(btn_step_back)
        controls_layout.addWidget(self._btn_play_pause)
        controls_layout.addWidget(btn_step_next)
        controls_layout.addWidget(btn_fast_forward)

    def reset(self, num_steps: int):
        self._slider_steps.setMaximum(num_steps)
        self._slider_steps.setSliderPosition(num_steps)
        self._lbl_end_step.setText("Step {}".format(num_steps))

    @pyqtSlot()
    def toggle_play_pause(self):
        self.pause() if self._playback_timer.isActive() else self.play()

    @property
    def play_head_at_start(self) -> bool:
        return self._slider_steps.sliderPosition() == self._slider_steps.minimum()

    @property
    def play_head_at_end(self) -> bool:
        return self._slider_steps.sliderPosition() == self._slider_steps.maximum()

    @pyqtSlot()
    def play(self):
        if self.play_head_at_end:
            self.rewind()

        self._playback_timer.start(100)
        self._btn_play_pause.setText("Pause")

    @pyqtSlot()
    def pause(self):
        self._playback_timer.stop()
        self._btn_play_pause.setText("Play")

    @pyqtSlot()
    def rewind(self):
        self.pause()
        self._slider_steps.setSliderPosition(self._slider_steps.minimum())

    @pyqtSlot()
    def fastforward(self):
        self.pause()
        self._slider_steps.setSliderPosition(self._slider_steps.maximum())

    @pyqtSlot()
    def step(self):
        self.pause()
        self._step()

    def _step(self):
        new_pos = self._slider_steps.sliderPosition() + 1
        self._slider_steps.setSliderPosition(new_pos)

        if self.play_head_at_end:
            self.pause()

    @pyqtSlot()
    def step_back(self):
        self.pause()
        new_pos = self._slider_steps.sliderPosition() - 1
        self._slider_steps.setSliderPosition(new_pos)


class EditGridDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.grid: Grid = Grid()
        self._grid_preview = GridWidget()
        self._grid_preview.grid = self.grid
        self._grid_preview.editable = True
        self._grid_preview.on_edited.connect(self.grid_widget_edited)

        self._button_box: QDialogButtonBox = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Grid Editor")

        main_layout = QGridLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel("Edit below, or paste an 81-char grid string (0070090301...)"), 0, 0)
        main_layout.addWidget(self._grid_preview, 1, 0)

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        main_layout.addWidget(self._button_box, 2, 0, 1, 2)

        self._grid_preview.select_cell_at(0, 0)
        self._grid_preview.setFocus(Qt.OtherFocusReason)

        self.update_ui()

    @property
    def valid(self) -> bool:
        return self.grid.valid and not self.grid.solved

    @pyqtSlot()
    def grid_widget_edited(self) -> None:
        self.update_ui()

    def update_ui(self):
        self._grid_preview.update()
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(self.valid)

    def mousePressEvent(self, e: QMouseEvent):
        self._grid_preview.deselect_current_cell()
        super().mousePressEvent(e)

    def showEvent(self, e: QShowEvent) -> None:
        # If the grid is empty, attempt to create a grid from the clipboard upon showing the dialog
        if self.grid.empty:
            self.load_grid_from_clipboard()

    def load_grid_from_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            try:
                grid_str = clipboard.text()
                self.grid.grid_string = grid_str
                self.update_ui()
            except ValueError:
                # TODO: notify the user of the error
                return

    def eventFilter(self, o: QObject, e: QEvent) -> bool:
        if e.type() == e.KeyPress:
            if QKeyEvent(e).matches(QKeySequence.Paste):
                return True
            else:
                super().eventFilter(o, e)
        else:
            super().eventFilter(o, e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.matches(QKeySequence.Paste):
            self.load_grid_from_clipboard()
        else:
            super().keyPressEvent(e)


class SudokuSolverWindow(QMainWindow, solvers.SolverDelegate):
    def __init__(self):
        super().__init__()

        self.original_grid = Grid()
        self.solver: solvers.Solver = None
        self._solver_thread: threading.Thread = None

        self._grid_widget = None
        self._btn_load_grid = None
        self._combo_box_algorithm = None
        self._btn_start_solver = None
        self._playback_controls = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sudoku Solver")
        self.statusBar().showMessage("Edit a grid to get started")

        main_layout = QVBoxLayout()
        w = QWidget()
        w.setLayout(main_layout)
        self.setCentralWidget(w)

        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Left side - sudokustepper grid
        self._grid_widget = GridWidget()
        top_layout.addWidget(self._grid_widget)

        # Right side - options
        options_layout = QFormLayout()
        top_layout.addLayout(options_layout)

        self._btn_load_grid = QPushButton("Grid Editor")
        self._btn_load_grid.clicked.connect(self.load_grid_dialog)
        options_layout.addRow(self._btn_load_grid)

        divider_top = QFrame()
        divider_top.setFrameStyle(QFrame.HLine)
        divider_top.setFrameShadow(QFrame.Sunken)
        options_layout.addRow(divider_top)

        self._combo_box_algorithm = QComboBox()
        self._combo_box_algorithm.setEnabled(False)
        # Add all solver names to the list
        self._combo_box_algorithm.addItems([k.capitalize() for k in solvers.ALL_SOLVERS.keys()])
        self._combo_box_algorithm.setCurrentIndex(0)
        options_layout.addRow("Algorithm", self._combo_box_algorithm)

        self._btn_start_solver = QPushButton("Solve!")
        self._btn_start_solver.setEnabled(False)
        self._btn_start_solver.clicked.connect(self.start_solver)
        options_layout.addRow(self._btn_start_solver)

        self._playback_controls = PlaybackControlsWidget()
        self._playback_controls.setEnabled(False)
        self._playback_controls.step_selected.connect(self.preview_solver_step)
        main_layout.addWidget(self._playback_controls)

    def load_grid(self, grid: Grid):
        self.original_grid = deepcopy(grid)
        self._grid_widget.grid = self.original_grid
        self._grid_widget.update()

        self._combo_box_algorithm.setEnabled(True)
        self._btn_start_solver.setEnabled(True)
        self.statusBar().showMessage("Grid loaded")

    def on_solver_solved(self):
        self.statusBar().showMessage("Solved in {} seconds".format("..."))
        self._grid_widget.grid = self.solver.grid
        self._btn_load_grid.setEnabled(True)
        self._combo_box_algorithm.setEnabled(True)
        self._btn_start_solver.setEnabled(True)
        self._playback_controls.reset(self.solver.num_steps)
        self._playback_controls.setEnabled(True)

    def on_solver_failed(self):
        self._btn_load_grid.setEnabled(True)
        self._combo_box_algorithm.setEnabled(True)
        self._btn_start_solver.setEnabled(True)

    @pyqtSlot()
    def load_grid_dialog(self):
        dialog = EditGridDialog(self)
        dialog.grid.grid_string = self.original_grid.grid_string
        if dialog.exec():
            self.load_grid(dialog.grid)

    @pyqtSlot()
    def start_solver(self):
        self._btn_load_grid.setEnabled(False)
        self._combo_box_algorithm.setEnabled(False)
        self._btn_start_solver.setEnabled(False)

        solver_cls = solvers.ALL_SOLVERS[self._combo_box_algorithm.currentText().lower()]
        assert solver_cls is not None
        self.solver = solver_cls(deepcopy(self.original_grid), delegate=self)

        self._solver_thread = threading.Thread(target=self.solver.solve)
        self._solver_thread.start()

    @pyqtSlot(int)
    def preview_solver_step(self, step: int):
        if step == 0:
            self._grid_widget.grid = self.original_grid
            self.statusBar().showMessage("Original puzzle")
        else:
            self._grid_widget.grid = self.solver.step_history[step - 1]
            self.statusBar().showMessage("Showing step {}".format(step))


def main():
    import sys
    import resources

    app = QApplication(sys.argv)

    # Load app stylesheet from the resource file
    style_sheet_file = QFile(":/styles/app.qss")
    style_sheet_file.open(QFile.ReadOnly | QFile.Text)
    style_sheet = QTextStream(style_sheet_file).readAll()
    app.setStyleSheet(style_sheet)

    w = SudokuSolverWindow()
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
