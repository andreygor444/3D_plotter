import pygame
from math import sin, cos, atan
from multiprocessing import Process, Queue
import os

from config import *
from gui import start_gui


class Point:
    default_color = 'white'
    default_size = 3
    
    def __init__(self, x, y, z, color=default_color, size=default_size, x_bias=0, y_bias=0, z_bias=0, zoom_power=1):
        self._setup(x, y, z, zoom_power)
        self.start_v_angle = self.v_angle
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.size = size
        self.x_bias = x_bias
        self.y_bias = y_bias
        self.z_bias = z_bias
        self.zoom_power = zoom_power

    def _setup(self, x, y, z, zoom_power=1):
        self.h_radius = (x ** 2 + y ** 2) ** 0.5 * zoom_power
        self.v_radius = (y ** 2 + z ** 2) ** 0.5 * zoom_power
        try:
            self.h_angle = atan(y / x)
        except ZeroDivisionError:
            self.h_angle = pi / 2 if y > 0 else -pi / 2 
        if x < 0:
            self.h_angle += pi
        elif y == 0:
            self.h_angle = pi * (x < 0)
        try:
            self.v_angle = atan(z / y)
        except ZeroDivisionError:
            self.v_angle = pi / 2 if y > 0 else -pi / 2 
        if y < 0:
            self.v_angle += pi

    def set_bias(self, x_bias=0, y_bias=0, z_bias=0):
        self.x_bias = x_bias
        self.y_bias = y_bias
        self.z_bias = z_bias

    def zoom(self, d_zoom):
        self.zoom_power += d_zoom
    
    def rotate(self, d_h_angle, d_v_angle):
        self.h_angle += d_h_angle
        self.v_angle += d_v_angle
    
    def move(self, dx, dy, dz):
        self.x_bias += dx
        self.y_bias += dy
        self.z_bias += dz
    
    def get_coords(self):
        x = cos(self.h_angle) * self.h_radius / self.zoom_power
        y = sin(self.h_angle) * self.h_radius / self.zoom_power
        v_radius = (y ** 2 + self.z ** 2) ** 0.5
        try:
            v_angle = atan(self.z / y) + self.v_angle - self.start_v_angle
        except ZeroDivisionError:
            v_angle = pi / 2 + self.v_angle - self.start_v_angle
            if self.z < 0:
                v_angle -= pi
        if y < 0:
            v_angle += pi
        y = cos(v_angle) * v_radius / self.zoom_power
        z = sin(v_angle) * v_radius / self.zoom_power
        return x + self.x_bias, y + self.y_bias, -z + self.z_bias
    
    def render(self, screen):
        x, y, z = self.get_coords()
        pygame.draw.circle(screen, self.color, (x, z), self.size)


class Line:
    default_color = 'white'
    default_width = 1
    
    def __init__(self, point_1, point_2, color=default_color, width=default_width):
        self.point_1 = point_1
        self.point_2 = point_2
        self.color = color
        self.width = width
    
    def set_bias(self, x_bias=0, y_bias=0, z_bias=0):
        self.point_1.set_bias(x_bias, y_bias, z_bias)
        self.point_2.set_bias(x_bias, y_bias, z_bias)
    
    def zoom(self, d_zoom):
        self.point_1.zoom(d_zoom)
        self.point_2.zoom(d_zoom)
    
    def rotate(self, d_h_angle, d_v_angle):
        self.point_1.rotate(d_h_angle, d_v_angle)
        self.point_2.rotate(d_h_angle, d_v_angle)
    
    def move(self, dx, dy, dz):
        self.point_1.move(dx, dy, dz)
        self.point_2.move(dx, dy, dz)

    def render(self, screen):
        x1, y1, z1 = self.point_1.get_coords()
        x2, y2, z2 = self.point_2.get_coords()
        pygame.draw.line(screen, self.color, (x1, z1), (x2, z2), width=self.width)


class Chart:
    default_color = 'white'
    
    def __init__(self):
        self.points = []
        self.lines = []
        self.zoom_power = 1
        self.h_angle = 0
        self.v_angle = 0
        self.x_bias = 0
        self.y_bias = 0
        self.z_bias = 0

    def make_chart(self, func, x_begin, x_end, y_begin, y_end, x_step, y_step, scale=1, color=default_color):
        self.clear()
        matrix = []
        x_end += x_step
        y_end += y_step
        x = x_begin
        while x <= x_end:
            matrix.append([])
            y = y_begin
            while y <= y_end:
                try:
                    matrix[-1].append((x * scale, y * scale, func(x, y) * scale))
                except Exception:
                    matrix[-1].append(None)
                y += y_step
            x += x_step

        for i in range(len(matrix)):
            for j in range(1, len(matrix[i])):
                if matrix[i][j-1] and matrix[i][j]:
                    self.lines.append(Line(Point(*matrix[i][j-1], color), Point(*matrix[i][j], color), color))
        if len(matrix) == 0:
            return
        for i in range(1, len(matrix)):
            for j in range(len(matrix[0])):
                if matrix[i-1][j] and matrix[i][j]:
                    self.lines.append(Line(Point(*matrix[i-1][j], color), Point(*matrix[i][j], color), color))
    
    def set_points(self, points):
        self.points = points
    
    def set_lines(self, lines):
        self.lines = lines
    
    def set_bias(self, x_bias=0, y_bias=0, z_bias=0):
        for point in self.points:
            point.set_bias(x_bias, y_bias, z_bias)
        for line in self.lines:
            line.set_bias(x_bias, y_bias, z_bias)

    def clear(self):
        self.points.clear()
        self.lines.clear()
    
    def zoom(self, d_zoom):
        if self.zoom_power + d_zoom <= 0:
            return
        self.zoom_power += d_zoom
        for point in self.points:
            point.zoom(d_zoom)
        for line in self.lines:
            line.zoom(d_zoom)
    
    def rotate(self, d_h_angle, d_v_angle):
        if not (-pi/2 <= self.v_angle + d_v_angle <= pi/2):
            d_v_angle = 0
        self.h_angle += d_h_angle
        self.v_angle += d_v_angle
        for point in self.points:
            point.rotate(d_h_angle, d_v_angle)
        for line in self.lines:
            line.rotate(d_h_angle, d_v_angle)

    def move(self, dx=0, dy=0, dz=0):
        self.x_bias += dx
        self.y_bias += dy
        self.z_bias += dz
        for point in self.points:
            point.move(dx, dy, dz)
        for line in self.lines:
            line.move(dx, dy, dz)

    def render(self, screen):
        for point in self.points:
            point.render(screen)
        
        for line in self.lines:
            line.render(screen)


def make_axis_chart():
    axis_chart = Chart()
    axis_chart.set_lines(
        [
            Line(Point(-INF, 0, 0, 'blue'), Point(INF, 0, 0, 'blue'), 'red'),
            Line(Point(0, -INF, 0, 'green'), Point(0, INF, 0, 'green'), 'green'),
            Line(Point(0, 0, -INF, 'red'), Point(0, 0, INF, 'red'), 'blue')
        ]
    )
    axis_chart.set_bias(x_bias=WIDTH // 2, z_bias=HEIGHT // 2)
    return axis_chart


def main():
    pygame.init()
    
    charts = {}
    axis_chart = make_axis_chart()
    charts[-1] = axis_chart
    
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
    z_bias = HEIGHT // 2
    h_angle = 0
    v_angle = 0
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
                    for chart in charts.values():
                        chart.zoom(ZOOM_CHANGE_SPEED)
                    zoom += ZOOM_CHANGE_SPEED
                elif event.button == MOUSEWHEELDOWN:
                    for chart in charts.values():
                        chart.zoom(-ZOOM_CHANGE_SPEED)
                    if zoom - ZOOM_CHANGE_SPEED > 0:
                        zoom -= ZOOM_CHANGE_SPEED
            
            elif event.type == pygame.MOUSEBUTTONUP:
                rotation = False
                moving = False
            
            elif event.type == pygame.MOUSEMOTION:
                if rotation:
                    mouse_pos = event.pos
                    d_x = (last_mouse_pos[0] - mouse_pos[0]) / ROTATION_COEF
                    d_y = (last_mouse_pos[1] - mouse_pos[1]) / ROTATION_COEF
                    h_angle += d_x
                    if -pi/2 <= v_angle + d_y <= pi/2:
                        v_angle += d_y
                    for chart in charts.values():
                        chart.rotate(d_x, d_y)
                if moving:
                    mouse_pos = event.pos
                    d_x = (mouse_pos[0] - last_mouse_pos[0]) / MOVING_COEF
                    d_z = (mouse_pos[1] - last_mouse_pos[1]) / MOVING_COEF
                    x_bias += d_x
                    z_bias += d_z
                    for chart in charts.values():
                        chart.move(d_x, 0, d_z)
                last_mouse_pos = event.pos

            elif event.type == pygame.VIDEORESIZE:
                dx = screen.get_width() // 2 - width // 2
                dz = screen.get_height() // 2 - height // 2
                x_bias += dx
                z_bias += dz
                for chart in charts.values():
                    chart.move(dx, 0, dz)
                width, height = screen.get_size()
            
            elif event.type == pygame.QUIT:
                return
        
        screen.fill(BG_COLOR)
        for chart in charts.values():
            chart.render(screen)
        
        fps = fps_font.render(str(int(time.get_fps())), True, 'green')
        screen.blit(fps, (width-50, 0))
        
        pygame.display.flip()
        
        if not queue.empty():
            signal = queue.get()
            if signal[0] == Signals.show_chart:
                chart_id = signal[1]
                if chart_id not in charts:
                    charts[chart_id] = Chart()
                signal[2] = eval(signal[2])
                charts[chart_id].make_chart(*signal[2:])
                charts[chart_id].set_bias(x_bias, y_bias, z_bias)
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
