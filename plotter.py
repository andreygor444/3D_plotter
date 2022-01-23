import pygame
from multiprocessing import Process, Queue
import numpy as np
import os

from config import *
from gui import start_gui


class Chart:
    color = 'white'
    
    def __init__(self):
        self.X = np.empty(0)
        self.Y = np.empty(0)
        self.Z = np.empty((0, 0))
        self.x = np.empty(0)
        self.y = np.empty(0)
        self.z = np.empty(0)
        self.zoom_power = 1
        self.h_angle = 0
        self.v_angle = 0
        self.x_bias = 0
        self.y_bias = 0
        self.z_bias = 0
        self.show_points = False
        self.show_lines = True

    def make_chart(self, func, x_begin, x_end, y_begin, y_end, x_step, y_step, scale=1,
                   color=color, show_points=False, show_lines=True):
        try:
            self.show_points = show_points
            self.show_lines = show_lines
            self.color = color
            self.clear()
            x_axis = np.linspace(x_begin, x_end, round((x_end-x_begin) / x_step) + 1, dtype=np.float64) * scale
            y_axis = np.linspace(y_begin, y_end, round((y_end-y_begin) / y_step) + 1, dtype=np.float64) * scale
            self.X, self.Y = np.meshgrid(x_axis, y_axis)
            self.Z = func(self.X, self.Y) * scale
            self.Z[np.abs(self.Z) > INF] = np.nan
        except Exception as err:
            self.clear()
            print("Error:", err)
    
    def set_chart(self, x, y, z, color=color):
        self.X, self.Y, self.Z = x, y, z
        self.color = color

    def clear(self):
        self.X = np.empty(0)
        self.Y = np.empty(0)
        self.Z = np.empty((0, 0))
    
    def zoom(self, zoom):
        self.zoom_power = zoom
    
    def _zoom(self):
        self.x *= self.zoom_power
        self.y *= self.zoom_power
        self.z *= self.zoom_power
    
    def rotate(self, h_angle, v_angle):
        self.h_angle = h_angle
        self.v_angle = v_angle
    
    def _rotate(self):
        x = self.x*np.cos(self.h_angle) - self.y*np.sin(self.h_angle)
        y = self.x*np.sin(self.h_angle) + self.y*np.cos(self.h_angle)
        self.x = x
        self.y = y
        
        y = self.y*np.cos(self.v_angle) - self.z*np.sin(self.v_angle)
        self.z = -self.y*np.sin(self.v_angle) + self.z*np.cos(self.v_angle)
        self.y = y

    def move(self, x_bias=0, y_bias=0, z_bias=0):
        self.x_bias = x_bias
        self.y_bias = y_bias
        self.z_bias = z_bias

    def _move(self):
        self.x += self.x_bias
        self.y += self.y_bias
        self.z += self.z_bias

    def render(self, screen):
        self.x = self.X.copy()
        self.y = self.Y.copy()
        self.z = self.Z.copy()
        self._zoom()
        self._rotate()
        self._move()
        n = self.x.shape[0]
        m = self.x.shape[1] if len(self.x.shape) > 1 else 0
        x_gaps_, y_gaps_ = np.array(np.where(np.isnan(self.Z)))
        x_gaps = np.concatenate(([-1], x_gaps_, [n]))
        y_gaps = np.concatenate(([-1], y_gaps_, [m]))
        if self.show_points:
            for x in range(n):
                for y in range(m):
                    pygame.draw.circle(screen, self.color, (self.x[x][y], -self.z[x][y]), 2)
        if self.show_lines:
            x = n
            for i in range(1, len(x_gaps)):
                for x in range(x_gaps[i-1]+2, x_gaps[i]):
                    for y in range(1, m):
                        pygame.draw.line(screen, self.color, (self.x[x][y], -self.z[x][y]), (self.x[x][y-1], -self.z[x][y-1]), width=1)
                        pygame.draw.line(screen, self.color, (self.x[x][y], -self.z[x][y]), (self.x[x-1][y], -self.z[x-1][y]), width=1)
                j = i
                x += 1
                if x < n:
                    while j < len(x_gaps) and x_gaps[j] == x_gaps[i]:
                        y_gaps[j-1] = -1
                        for y in range(y_gaps[j-1]+2, y_gaps[j]):
                            pygame.draw.line(screen, self.color, (self.x[x][y], -self.z[x][y]), (self.x[x][y-1], -self.z[x][y-1]), width=1)
                        j += 1
                i = j
                x += 1
                y_gaps[j-1] = -1
                if x < n:
                    while j < len(x_gaps) and x_gaps[j] == x_gaps[i]:
                        for y in range(y_gaps[j-1]+2, y_gaps[j]):
                            pygame.draw.line(screen, self.color, (self.x[x][y], -self.z[x][y]), (self.x[x][y-1], -self.z[x][y-1]), width=1)
                        j += 1
            for x in range(1, n):
                if np.isnan(self.Z[x][0]) or np.isnan(self.Z[x-1][0]):
                    continue
                pygame.draw.line(screen, self.color, (self.x[x][0], -self.z[x][0]), (self.x[x-1][0], -self.z[x-1][0]), width=1)
            for y in range(1, m):
                if np.isnan(self.Z[0][y]) or np.isnan(self.Z[0][y-1]):
                    continue
                pygame.draw.line(screen, self.color, (self.x[0][y], -self.z[0][y]), (self.x[0][y-1], -self.z[0][y-1]), width=1)


def add_axis_charts(charts):
    INF = 10**7
    x_axis_chart = Chart()
    x_axis_chart.set_chart(
        np.array([[-INF], [INF]], dtype=np.float64),
        np.array([[0], [0]], dtype=np.float64),
        np.array([[0], [0]], dtype=np.float64),
        color='blue'
    )
    x_axis_chart.move(x_bias=WIDTH // 2, z_bias=-HEIGHT // 2)
    x_axis_chart.rotate(START_H_ANGLE, START_V_ANGLE)
    y_axis_chart = Chart()
    y_axis_chart.set_chart(
        np.array([[0], [0]], dtype=np.float64),
        np.array([[-INF], [INF]], dtype=np.float64),
        np.array([[0], [0]], dtype=np.float64),
        color='green'
    )
    y_axis_chart.move(x_bias=WIDTH // 2, z_bias=-HEIGHT // 2)
    y_axis_chart.rotate(START_H_ANGLE, START_V_ANGLE)
    z_axis_chart = Chart()
    z_axis_chart.set_chart(
        np.array([[0], [0]], dtype=np.float64),
        np.array([[0], [0]], dtype=np.float64),
        np.array([[-INF], [INF]], dtype=np.float64),
        color='red'
    )
    z_axis_chart.move(x_bias=WIDTH // 2, z_bias=-HEIGHT // 2)
    z_axis_chart.rotate(START_H_ANGLE, START_V_ANGLE)
    charts[-1] = x_axis_chart
    charts[-2] = y_axis_chart
    charts[-3] = z_axis_chart


def main():
    pygame.init()
    
    charts = {}
    add_axis_charts(charts)
    
    queue = Queue()
    gui_process = Process(target=start_gui, args=(queue,))
    gui_process.start()

    os.environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(*PLOTTER_WINDOW_POS)
    os.environ['SDL_VIDEO_CENTERED'] = '0'
    screen = pygame.display.set_mode(DISPLAY_SIZE, pygame.RESIZABLE)
    mainloop(screen, charts, queue)
    
    gui_process.kill()
    pygame.quit()


def mainloop(screen, charts, queue):
    width, height = screen.get_size()
    time = pygame.time.Clock()
    rotation = False
    moving = False
    last_mouse_pos, mouse_pos = None, None
    fps_font = pygame.font.Font(None, 50)
    x_bias = WIDTH // 2
    y_bias = 0
    z_bias = -HEIGHT // 2
    h_angle = START_H_ANGLE
    v_angle = START_V_ANGLE
    zoom = 1
    
    while True:
        time.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == LEFT_MOUSE_BUTTON:
                    rotation = True
                    last_mouse_pos = event.pos
                elif event.button == RIGHT_MOUSE_BUTTON:
                    moving = True
                    last_mouse_pos = event.pos
                elif event.button == MOUSEWHEELUP:
                    zoom += ZOOM_CHANGE_SPEED
                    for chart in charts.values():
                        chart.zoom(zoom)
                elif event.button == MOUSEWHEELDOWN:
                    if zoom - ZOOM_CHANGE_SPEED > 0:
                        zoom -= ZOOM_CHANGE_SPEED
                    for chart in charts.values():
                        chart.zoom(zoom)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                rotation = False
                moving = False
            
            elif event.type == pygame.MOUSEMOTION:
                if rotation:
                    mouse_pos = event.pos
                    d_x = (mouse_pos[0] - last_mouse_pos[0]) / ROTATION_COEF
                    d_y = (mouse_pos[1] - last_mouse_pos[1]) / ROTATION_COEF
                    v_angle += d_y
                    if not (v_angle // pi % 2):
                        d_x *= -1
                    h_angle += d_x
                    for chart in charts.values():
                        chart.rotate(h_angle, v_angle)
                if moving:
                    mouse_pos = event.pos
                    d_x = (mouse_pos[0] - last_mouse_pos[0]) / MOVING_COEF
                    d_z = (last_mouse_pos[1] - mouse_pos[1]) / MOVING_COEF
                    x_bias += d_x
                    z_bias += d_z
                    for chart in charts.values():
                        chart.move(x_bias, 0, z_bias)
                last_mouse_pos = event.pos

            elif event.type == pygame.VIDEORESIZE:
                dx = screen.get_width() // 2 - width // 2
                dz = height // 2 - screen.get_height() // 2
                x_bias += dx
                z_bias += dz
                for chart in charts.values():
                    chart.move(x_bias, 0, z_bias)
                width, height = screen.get_size()
            
            elif event.type == pygame.QUIT:
                return
        
        screen.fill(BG_COLOR)
        for chart in charts.values():
            chart.render(screen)
        
        fps = fps_font.render(str(int(time.get_fps())), True, 'green')
        screen.blit(fps, (width - 50, 0))
        
        pygame.display.flip()
        
        if not queue.empty():
            signal = queue.get()
            if signal[0] == Signals.show_chart:
                chart_id = signal[1]
                if chart_id not in charts:
                    charts[chart_id] = Chart()
                signal[2] = eval(signal[2])
                charts[chart_id].make_chart(*signal[2:])
                charts[chart_id].move(x_bias, y_bias, z_bias)
                charts[chart_id].rotate(h_angle, v_angle)
                charts[chart_id].zoom(zoom)
            elif signal[0] == Signals.remove_chart:
                chart_id = signal[1]
                if chart_id in charts:
                    del charts[chart_id]
            elif signal[0] == Signals.stop_execution:
                return


if __name__ == '__main__':
    main()
