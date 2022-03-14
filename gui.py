from PyQt5.QtWidgets import (QApplication, QWidget, QScrollArea,
                             QVBoxLayout, QGroupBox, QPushButton,
                             QHBoxLayout, QAbstractSpinBox, QColorDialog,
                             QInputDialog, QSlider
                             )
from PyQt5 import uic
from PyQt5.QtGui import QFont
from functools import partial
import sys

from config import Signals, GUI_WINDOW_POS, GUI_WINDOW_SIZE, DEFAULT_CHARTS, FUNCTION_SUBSTITUTIONS


class ChartWidget(QWidget):
    def __init__(self, id_, plot_chart_func, hide_chart_func, del_chart_func):
        super().__init__()
        self.id = id_
        self.plot_chart_func = plot_chart_func
        self.hide_chart_func = hide_chart_func
        self.del_chart_func = del_chart_func
        self.color = (255, 255, 255)
        self.points_visibility = False
        self.lines_visibility = True
        self._initUI()

    def _initUI(self):
        uic.loadUi('res/chart_widget.ui', self)
        self.x_from_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.x_to_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.x_step_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.y_from_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.y_to_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.y_step_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.scale_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.function_input.textChanged.connect(self.redraw_chart)
        self.x_from_spin_box.valueChanged.connect(self.redraw_chart)
        self.x_to_spin_box.valueChanged.connect(self.redraw_chart)
        self.x_step_spin_box.valueChanged.connect(self.redraw_chart)
        self.y_from_spin_box.valueChanged.connect(self.redraw_chart)
        self.y_to_spin_box.valueChanged.connect(self.redraw_chart)
        self.y_step_spin_box.valueChanged.connect(self.redraw_chart)
        self.scale_spin_box.valueChanged.connect(self.redraw_chart)

        self.plot_btn.clicked.connect(self.plot_or_hide_chart)
        self.function_input.returnPressed.connect(self.plot_or_hide_chart)
        self.delete_btn.clicked.connect(partial(self.del_chart_func, self))
        self.color_btn.clicked.connect(self.change_color)
        self.show_points_checkbox.stateChanged.connect(self.redraw_chart)
        self.show_lines_checkbox.stateChanged.connect(self.redraw_chart)

    def set_params(self, func, x_from, x_to, y_from, y_to, x_step, y_step, scale):
        self.function_input.setText(func)
        self.x_from_spin_box.setValue(x_from)
        self.x_to_spin_box.setValue(x_to)
        self.x_step_spin_box.setValue(x_step)
        self.y_from_spin_box.setValue(y_from)
        self.y_to_spin_box.setValue(y_to)
        self.y_step_spin_box.setValue(y_step)
        self.scale_spin_box.setValue(scale)

    def get_id(self):
        return self.id

    def get_params(self):
        return (
            self.get_func(),
            self.x_from_spin_box.value(), self.x_to_spin_box.value(),
            self.y_from_spin_box.value(), self.y_to_spin_box.value(),
            self.x_step_spin_box.value(), self.y_step_spin_box.value(),
            self.scale_spin_box.value(), self.color,
            self.show_points_checkbox.isChecked(), self.show_lines_checkbox.isChecked()
        )

    def get_func(self):
        func = self.function_input.text()
        for pattern, repl in FUNCTION_SUBSTITUTIONS.items():
            func = func.replace(pattern, repl)
        return f'lambda x, y: np.zeros(x.shape)+{func}'

    def validate_user_input(self, show_errors=True):
        try:
            func, x_from, x_to, y_from, y_to, x_step, y_step, _, _, _, _ = self.get_params()
            assert x_from < x_to
            assert y_from < y_to
            assert x_step < x_to - x_from
            assert y_step < y_to - y_from
            assert x_step and y_step
            eval(func)
            self.show_error_message('')
            return True
        except AssertionError:
            if show_errors:
                self.show_error_message('Incorrect bounds!')
            return False
        except Exception:
            if show_errors:
                self.show_error_message('Incorrect function!')
            return False

    def show_error_message(self, msg):
        self.error_display_label.setText(msg)

    def redraw_chart(self):
        if self.plot_btn.text() == 'Plot':
            return
        if not self.validate_user_input(show_errors=False):
            self.hide_chart_func(self.id)
            return
        self.plot_chart_func(self.id, *self.get_params())

    def plot_or_hide_chart(self):
        if self.plot_btn.text() == 'Plot':
            if not self.validate_user_input():
                return
            self.plot_btn.setText('Hide')
            self.plot_btn.setStyleSheet('border: 3px solid black;border-radius:5px;background-color:#ff5500')
            self.plot_chart_func(self.id, *self.get_params())
        else:
            self.plot_btn.setText('Plot')
            self.plot_btn.setStyleSheet('border: 3px solid black;border-radius:5px;background-color:#00aa00')
            self.hide_chart_func(self.id)

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.getRgb()[:3]
            self.color_btn.setStyleSheet(f'border:3px solid black;border-radius:5px;background-color:rgb{self.color};')
            self.redraw_chart()


class ParamWidget(QWidget):
    def __init__(self, name, change_param_func, del_param_func):
        super().__init__()
        self.name = name
        self.change_param_func = change_param_func
        self.del_param_func = del_param_func
        self.min = -10
        self.max = 10
        self.step = 1
        self._initUI()
        self.change()

    def _initUI(self):
        uic.loadUi('res/param_widget.ui', self)
        self.setFixedHeight(115)
        self.name_label.setText(f'Parameter {self.name}')
        self.min_val_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.max_val_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.step_spin_box.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.min_val_spin_box.valueChanged.connect(self.change_range)
        self.max_val_spin_box.valueChanged.connect(self.change_range)
        self.step_spin_box.valueChanged.connect(self.change_range)
        self.val_slider.valueChanged.connect(self.change)
        self.delete_btn.clicked.connect(partial(self.del_param_func, self))
        self.val_slider.setTickPosition(QSlider.TicksBothSides)

    def change_range(self):
        self.min = self.min_val_spin_box.value()
        self.max = self.max_val_spin_box.value()
        self.step = self.step_spin_box.value()
        if self.min >= self.max:
            self.min = self.max - 1
            self.min_val_spin_box.setValue(self.min)
        if self.step == 0:
            self.step = 0.1
            self.step_spin_box.setValue(self.step)
        self.val_slider.setMaximum((self.max - self.min) / self.step)

    def get_name(self):
        return self.name

    def change(self):
        val = round(self.min + (self.max - self.min) * self.val_slider.value() / self.val_slider.maximum(), 2)
        self.val_label.setText(str(val))
        self.change_param_func(self.name, val)


class MainWindow(QWidget):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self._initUI()
        self.next_chart_id = 0
        self.load_default_charts()
        self.resize_chart_list()
        self.resize_param_list()

    def _initUI(self):
        self.setWindowTitle('Plotter')
        self.setGeometry(*GUI_WINDOW_POS, *GUI_WINDOW_SIZE)
        self.setMinimumWidth(819)
        self.setMinimumHeight(400)
        self.layout = QVBoxLayout(self)

        self.charts_group_box = QGroupBox('Charts')
        self.charts_group_box.setStyleSheet('border: none;')
        self.chart_list = QVBoxLayout()
        self.chart_list.setSpacing(0)
        self.charts_group_box.setLayout(self.chart_list)
        self.functions_scroll = QScrollArea()
        self.functions_scroll.setWidget(self.charts_group_box)
        self.functions_scroll.setWidgetResizable(True)
        self.layout.addWidget(self.functions_scroll)

        self.add_chart_btn = QPushButton('New chart', self)
        self.add_chart_btn.setFont(QFont('Arial', 14))
        self.add_chart_btn.clicked.connect(self.add_chart)
        self.add_chart_btn.setFixedWidth(350)
        self.add_chart_btn.setFixedHeight(40)
        self.add_chart_btn.setStyleSheet('''background: none;
                                            background-color: rgb(255, 255, 255);
                                            border: 2px solid;
                                            border-radius: 10px;
                                            ''')
        self.button_layout_1 = QHBoxLayout()
        self.button_layout_1.addWidget(self.add_chart_btn)
        self.layout.addLayout(self.button_layout_1)

        self.params_group_box = QGroupBox('Parameters')
        self.params_group_box.setStyleSheet('border: none;')
        self.param_list = QVBoxLayout()
        self.param_list.setSpacing(0)
        self.params_group_box.setLayout(self.param_list)
        self.params_scroll = QScrollArea()
        self.params_scroll.setWidget(self.params_group_box)
        self.params_scroll.setWidgetResizable(True)
        self.params_scroll.setFixedHeight(240)
        self.layout.addWidget(self.params_scroll)

        self.add_param_btn = QPushButton('New parameter', self)
        self.add_param_btn.setFont(QFont('Arial', 14))
        self.add_param_btn.clicked.connect(self.add_param)
        self.add_param_btn.setFixedWidth(350)
        self.add_param_btn.setFixedHeight(40)
        self.add_param_btn.setStyleSheet('''background: none;
                                            background-color: rgb(255, 255, 255);
                                            border: 2px solid;
                                            border-radius: 10px;
                                            ''')
        self.button_layout_2 = QHBoxLayout()
        self.button_layout_2.addWidget(self.add_param_btn)
        self.layout.addLayout(self.button_layout_2)

    def load_default_charts(self):
        for func, x_from, x_to, y_from, y_to, x_step, y_step, scale in DEFAULT_CHARTS:
            chart_widget = ChartWidget(self.next_chart_id, self.plot_chart, self.hide_chart, self.del_chart)
            chart_widget.set_params(func, x_from, x_to, y_from, y_to, x_step, y_step, scale)
            self.chart_list.addWidget(chart_widget)
            self.next_chart_id += 1

    def resize_chart_list(self):
        self.charts_group_box.setFixedHeight(self.chart_list.count() * 180 + 40)

    def resize_param_list(self):
        self.params_group_box.setFixedHeight(self.param_list.count() * 115 + 17)

    def add_chart(self):
        chart_widget = ChartWidget(self.next_chart_id, self.plot_chart, self.hide_chart, self.del_chart)
        self.chart_list.addWidget(chart_widget)
        self.resize_chart_list()
        self.next_chart_id += 1

    def plot_chart(self, *chart_data):
        self.queue.put([Signals.show_chart, *chart_data])

    def hide_chart(self, chart_id):
        self.queue.put([Signals.del_chart, chart_id])

    def del_chart(self, chart_widget):
        self.queue.put([Signals.del_chart, chart_widget.get_id()])
        chart_widget.close()
        self.chart_list.removeWidget(chart_widget)
        self.resize_chart_list()

    def add_param(self):
        param_name, ok = QInputDialog.getText(self, 'Parameter name input', 'Enter parameter name:')
        if ok and param_name and not param_name[0].isdigit():
            param_widget = ParamWidget(param_name, self.change_param, self.del_param)
            self.param_list.addWidget(param_widget)
            self.resize_param_list()

    def change_param(self, *param_data):
        self.queue.put([Signals.add_param, *param_data])
        for i in range(self.chart_list.count()):
            self.chart_list.itemAt(i).widget().redraw_chart()

    def del_param(self, param_widget):
        self.queue.put([Signals.del_param, param_widget.get_name()])
        param_widget.close()
        self.param_list.removeWidget(param_widget)
        self.resize_param_list()

    def closeEvent(self, _):
        self.queue.put([Signals.stop_execution])


def start_gui(queue):
    app = QApplication(sys.argv)
    window = MainWindow(queue)
    window.show()
    sys.exit(app.exec_())
