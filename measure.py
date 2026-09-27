"""Метрики расписания: двойные брони, недостижимые выезды, перенос.

Главное число — двойные брони: две работы у одной бригады в пересекающееся
время. Второе по важности — выезд, до которого физически не успеть: в календаре
он выглядит нормально, а на деле бригада опаздывает и клиент ждёт зря.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stream as S
from plan import Naive, Careful
from stream import travel_minutes

DIR = Path(__file__).resolve().parent


def overlaps(slots):
    bad = 0
    by = {}
    for s in slots:
        by.setdefault((s.crew, s.day), []).append(s)
    for key, day_slots in by.items():
        day_slots.sort(key=lambda s: s.start)
        for a, b in zip(day_slots, day_slots[1:]):
            if b.start < a.end:
                bad += 1
    return bad


def unreachable(slots):
    """Выезды, до которых не успеть с предыдущего адреса."""
    bad = 0
    by = {}
    for s in slots:
        by.setdefault((s.crew, s.day), []).append(s)
    for key, day_slots in by.items():
        day_slots.sort(key=lambda s: s.start)
        for a, b in zip(day_slots, day_slots[1:]):
            if b.start - a.end < travel_minutes((a.lat, a.lon), (b.lat, b.lon)):
                bad += 1
    return bad


def move_creates_conflicts(engine):
    """Клиент просит сдвинуть визит на час — что становится с соседними.

    Проверяется не «сдвинулись ли чужие записи» (в обоих планировщиках они
    не двигаются), а появился ли после переноса конфликт: наложение или выезд,
    до которого уже не успеть. Календарь, который молча принимает такой перенос,
    ломает день бригады.
    """
    if not engine.slots:
        return "—"
    was = overlaps(engine.slots) + unreachable(engine.slots)
    bad = 0
    for target in engine.slots:
        target.start += 60
        target.end += 60
        if overlaps(engine.slots) + unreachable(engine.slots) > was:
            bad += 1
        target.start -= 60
        target.end -= 60
    return f"{bad} из {len(engine.slots)} ({bad / len(engine.slots):.0%})"


def run(cls):
    jobs, crews = S.build()
    eng = cls(crews)
    placed = sum(eng.place(j) for j in jobs)
    return {
        "планировщик": cls.name,
        "заявок": len(jobs),
        "разложено": f"{placed} ({placed / len(jobs):.0%})",
        "двойных броней": overlaps(eng.slots),
        "недостижимых выездов": unreachable(eng.slots),
        "конфликтов после переноса": move_creates_conflicts(eng),
    }


if __name__ == "__main__":
    res = [run(c) for c in (Naive, Careful)]
    cols = list(res[0])
    w = [max(len(str(r[c])) for r in res + [dict(zip(cols, cols))]) for c in cols]
    print(" | ".join(c.ljust(x) for c, x in zip(cols, w)))
    print("-|-".join("-" * x for x in w))
    for r in res:
        print(" | ".join(str(r[c]).ljust(x) for c, x in zip(cols, w)))
    (DIR / "out").mkdir(exist_ok=True)
    (DIR / "out/results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
