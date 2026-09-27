"""Два планировщика: наивный и с проверкой дороги.

Наивный делает то, что обычно и делают в самописных CRM: ищет свободное окно
в календаре бригады и ставит работу туда. Дорога между адресами в расчёт
не идёт — в календаре ведь пусто, значит можно.

Аккуратный проверяет три вещи: работа влезает в окно клиента, она влезает
в рабочий день, и до неё успевают доехать с предыдущего адреса.
"""
from dataclasses import dataclass, field

from stream import WORK_START, WORK_END, travel_minutes


@dataclass
class Slot:
    jid: int
    crew: str
    day: int
    start: int          # минуты от начала суток
    end: int
    lat: float
    lon: float


class Naive:
    """Ставит в первое свободное место календаря, дорогу не считает."""

    name = "в лоб"

    def __init__(self, crews):
        self.crews = crews
        self.slots = []

    def place(self, job):
        for crew in self.crews:
            if job.day in crew.days_off:
                continue
            busy = sorted((s for s in self.slots if s.crew == crew.cid and s.day == job.day),
                          key=lambda s: s.start)
            t = max(job.window[0] * 60, WORK_START * 60)
            limit = min(job.window[1] * 60, WORK_END * 60)
            for s in busy:
                if t + job.minutes <= s.start:
                    break
                t = max(t, s.end)
            if t + job.minutes <= limit:
                self.slots.append(Slot(job.jid, crew.cid, job.day, t, t + job.minutes,
                                       job.lat, job.lon))
                return True
        return False


class Careful:
    """То же, но с дорогой и проверкой рабочего дня."""

    name = "с проверкой дороги"

    def __init__(self, crews):
        self.crews = crews
        self.slots = []

    def place(self, job):
        best = None
        for crew in self.crews:
            if job.day in crew.days_off:
                continue
            busy = sorted((s for s in self.slots if s.crew == crew.cid and s.day == job.day),
                          key=lambda s: s.start)
            t = max(job.window[0] * 60, WORK_START * 60)
            prev = (crew.lat, crew.lon)
            ok = True
            for s in busy:
                # доехать до нового адреса можно только после предыдущей работы
                if t + travel_minutes(prev, (job.lat, job.lon)) + job.minutes <= s.start \
                        - travel_minutes((job.lat, job.lon), (s.lat, s.lon)):
                    break
                t = max(t, s.end)
                prev = (s.lat, s.lon)
            t += travel_minutes(prev, (job.lat, job.lon))
            limit = min(job.window[1] * 60, WORK_END * 60)
            if t + job.minutes > limit:
                ok = False
            if ok and (best is None or t < best[1]):
                best = (crew.cid, t)
        if best is None:
            return False
        self.slots.append(Slot(job.jid, best[0], job.day, best[1], best[1] + job.minutes,
                               job.lat, job.lon))
        return True
