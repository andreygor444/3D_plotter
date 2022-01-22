from PyQt5.QtWidgets import (QApplication, QWidget, QScrollArea,
                             QVBoxLayout, QGroupBox, QPushButton,
                             QHBoxLayout, QAbstractSpinBox, QColorDialog)
from PyQt5 import uic
from PyQt5.QtGui import QFont
from functools import partial
import sys
from config import Signals, GUI_WINDOW_POS, DEFAULT_CHARTS


class ChartWidget(QWidget):
    def __init__(self, id_, plot_chart_func, hide_chart_func, del_chart_func):
        super().__init__()
        self.id = id_
        self.plot_chart_func = plot_chart_func
        self.hide_chart_func = hide_chart_func
        self.del_chart_func = del_chart_func
        self.color = (255, 255, 255)
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
            self.scale_spin_box.value(), self.color
        )
    
    def get_func(self):
        func = self.function_input.text()
        for pattern, repl in (('^', '**'), (',', '.')):
            func = func.replace(pattern, repl)
        return f'lambda x, y: {func}'
    
    def validate_user_input(self, show_errors=True):
        try:
            func, x_from, x_to, y_from, y_to, x_step, y_step, scale, color = self.get_params()
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
            self.color_btn.setStyleSheet(f'border: 3px solid black;border-radius: 5px;background-color: rgb{self.color};')
            self.redraw_chart()


class MainWindow(QWidget):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self._initUI()
        self.next_chart_id = 0
        self.load_default_charts()
        self.resize_charts_list()
    
    def _initUI(self):
        self.setWindowTitle('Plotter')
        self.setGeometry(*GUI_WINDOW_POS, 800, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        self.group_box = QGroupBox('Charts')
        self.group_box.setStyleSheet('border: none;')
        self.chart_list = QVBoxLayout(self)
        self.chart_list.setSpacing(0)
        self.group_box.setLayout(self.chart_list)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.group_box)
        self.scroll.setWidgetResizable(True)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll)
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
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.add_chart_btn)
        self.layout.addLayout(self.button_layout)
    
    def load_default_charts(self):
        for func, x_from, x_to, y_from, y_to, x_step, y_step, scale in DEFAULT_CHARTS:
            chart_widget = ChartWidget(self.next_chart_id, self.plot_chart, self.hide_chart, self.del_chart)
            chart_widget.set_params(func, x_from, x_to, y_from, y_to, x_step, y_step, scale)
            self.chart_list.addWidget(chart_widget)
            self.next_chart_id += 1

    def resize_charts_list(self):
        self.group_box.setFixedHeight(int(len(self.chart_list) * 180 + 40))

    def add_chart(self):
        chart_widget = ChartWidget(self.next_chart_id, self.plot_chart, self.hide_chart, self.del_chart)
        self.chart_list.addWidget(chart_widget)
        self.resize_charts_list()
        self.next_chart_id += 1
    
    def del_chart(self, chart_widget):
        self.queue.put([Signals.remove_chart, chart_widget.get_id()])
        chart_widget.close()
        self.chart_list.removeWidget(chart_widget)
        self.resize_charts_list()
    
    def plot_chart(self, *chart_data):
        self.queue.put([Signals.show_chart, *chart_data])
    
    def hide_chart(self, chart_id):
        self.queue.put([Signals.remove_chart, chart_id])
    
    def closeEvent(self, e):
        self.queue.put([Signals.stop_execution])


def start_gui(queue):
    app = QApplication(sys.argv)
    window = MainWindow(queue)
    window.show()
    sys.exit(app.exec_())
