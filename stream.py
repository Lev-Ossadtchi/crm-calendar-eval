"""Поток заявок на месяц: адреса, окна клиента, длительности, бригады.

Координаты и адреса синтетические — реальные заказы чужие, и в открытый замер
их класть нельзя. Зато здесь известно по построению, где конфликт заложен
намеренно: в наборе есть заявки, которые физически нельзя поставить подряд,
и окна, которые пересекаются.
"""
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

WORK_START, WORK_END = 9, 19          # рабочий день бригады, часы
SPEED_KMH = 30                        # средняя скорость по городу с пробками


@dataclass
class Job:
    jid: int
    day: int                 # день от начала месяца
    lat: float
    lon: float
    minutes: int             # сколько длится работа
    window: tuple            # (с какого часа, по какой) клиент дома
    kind: str                # замер / монтаж / сервис


@dataclass
class Crew:
    cid: str
    lat: float               # откуда выезжает утром
    lon: float
    days_off: tuple = ()


def travel_minutes(a, b):
    """Время в пути между точками — по прямой, с поправкой на городскую сетку."""
    dx = (a[0] - b[0]) * 111
    dy = (a[1] - b[1]) * 111 * 0.6
    km = (dx * dx + dy * dy) ** 0.5 * 1.35
    return int(km / SPEED_KMH * 60) + 5          # плюс пять минут на подход


def build(seed=9, days=20, per_day=6):
    rnd = random.Random(seed)
    jobs, jid = [], 1
    for day in range(1, days + 1):
        for _ in range(per_day):
            lat = 55.60 + rnd.random() * 0.35          # разброс по городу
            lon = 37.35 + rnd.random() * 0.55
            kind = rnd.choice(["замер", "монтаж", "монтаж", "сервис"])
            minutes = {"замер": 40, "монтаж": 240, "сервис": 90}[kind]
            start = rnd.randrange(WORK_START, WORK_END - 2)
            window = (start, min(start + rnd.choice([3, 4, 6]), WORK_END))
            jobs.append(Job(jid, day, lat, lon, minutes, window, kind))
            jid += 1
    crews = [Crew("бригада-1", 55.75, 37.62),
             Crew("бригада-2", 55.70, 37.50, days_off=(6, 13, 20)),
             Crew("бригада-3", 55.80, 37.70)]
    return jobs, crews
