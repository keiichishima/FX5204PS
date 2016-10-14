#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import pygame

from fx5204ps import FX5204PS

GRAPH_WIDTH = 600
GRAPH_HEIGHT = 100
SCREEN_SIZE = (GRAPH_WIDTH + 200, (GRAPH_HEIGHT + 50) * 4 + 50)

BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

class Graph(object):
    def __init__(self, screen, pos, index):
        self._screen = screen
        self._x = pos[0]
        self._y = pos[1]
        self._index = index
        self._watt_history = [0] * GRAPH_WIDTH
        self._avg_history = [0] * GRAPH_WIDTH
        self._max_history = [0] * GRAPH_WIDTH
        self._scale = 1.0
        self._font = pygame.font.SysFont(None, 24)

    def _draw_line(self, history, color):
        for t in range(1, GRAPH_WIDTH - 1):
            x0 = t - 1 + self._x
            y0 = (GRAPH_HEIGHT - history[t - 1] * self._scale + self._y)
            x1 = t + self._x
            y1 = (GRAPH_HEIGHT - history[t] * self._scale + self._y)
            pygame.draw.line(self._screen, color, (x0, y0), (x1, y1))

    def draw(self):
        self._draw_line(self._max_history, RED)
        self._draw_line(self._watt_history, BLUE)
        self._draw_line(self._avg_history, GREEN)

        pygame.draw.line(self._screen, WHITE,
                         (self._x, self._y),
                         (self._x, self._y + GRAPH_HEIGHT))
        pygame.draw.line(self._screen, WHITE,
                         (self._x, self._y + GRAPH_HEIGHT),
                         (self._x + GRAPH_WIDTH, self._y + GRAPH_HEIGHT))

        max_text = self._font.render(
            'Max: {0} W'.format(self._max_history[-1]),
            True, RED)
        self._screen.blit(max_text, (self._x + GRAPH_WIDTH, self._y))
        avg_text = self._font.render(
            'Avg:  {0} W'.format(self._avg_history[-1]),
            True, GREEN)
        self._screen.blit(avg_text, (self._x + GRAPH_WIDTH, self._y + 30))
        watt_text = self._font.render(
            'Watt: {0} W'.format(self._watt_history[-1]),
            True, BLUE)
        self._screen.blit(watt_text, (self._x + GRAPH_WIDTH, self._y + 60))

        y_zero_text = self._font.render('0', True, WHITE)
        w = y_zero_text.get_rect().width
        self._screen.blit(y_zero_text,
                          (self._x - w, self._y + GRAPH_HEIGHT))
        y_max_text = self._font.render(
            '{0} W'.format(int(GRAPH_HEIGHT / self._scale)),
            True, WHITE)
        w = y_max_text.get_rect().width
        self._screen.blit(y_max_text, (self._x - w, self._y))

        title_text = self._font.render('Port {0}'.format(self._index),
                                       True, WHITE)
        self._screen.blit(title_text, (self._x + 20, self._y - 20))

    def update(self, watt, watt_avg, watt_max):
        self._max_history.pop(0)
        self._max_history.append(watt_max)
        self._watt_history.pop(0)
        self._watt_history.append(watt)
        self._avg_history.pop(0)
        self._avg_history.append(watt_avg)

        max_in_history = max(self._max_history)
        if max_in_history > GRAPH_HEIGHT:
            self._scale = GRAPH_HEIGHT / max_in_history
        else:
            self._scale = 1.0

def draw_graph(fx):
    pygame.init()
    pygame.display.set_caption('FX5204PS Status')
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    font = pygame.font.SysFont(None, 24)
    graphs = []
    for i in range(4):
        graphs.append(Graph(screen,
                            (60, (GRAPH_HEIGHT + 50) * i + 50),
                            i))

    while True:
        clock.tick(10)
        screen.fill(BLACK)

        watt = fx.wattage
        watt_avg = fx.wattage_avg
        watt_max = fx.wattage_max
        for i in range(4):
            graphs[i].update(watt[i], watt_avg[i], watt_max[i])
            graphs[i].draw()

        freq = fx.frequency
        volt = fx.voltage
        temp = fx.temperature
        status_text = font.render(
            'Volt:{0} V, Freq: {1} Hz, Temp: {2} C'.format(
                volt, freq, temp),
            True, WHITE)
        screen.blit(status_text, (0, 0))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

if __name__ == '__main__':
    fx = FX5204PS(sumup_interval=10)
    fx.start()
    draw_graph(fx)
    fx.stop()
