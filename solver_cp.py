from itertools import product

import matplotlib.pyplot as plt
import numpy as np
from attrs import define
from matplotlib.colors import ListedColormap
from ortools.sat.python.cp_model import *


@define
class Result:
    status: str
    wall_time: float
    objective: float = None
    n_doctors_per_hour: np.ndarray = None
    doctors_view: np.ndarray = None
    days_view: np.ndarray = None

    @property
    def ok(self):
        return self.status in ['OPTIMAL', 'FEASIBLE']


def get_possible_decisions():
    possible = [[1 if i < 7 else 0 for i in range(24)]]
    for b in range(7, 24):
        for t in range(4, 9):
            if b + t <= 24:
                possible.append([1 if b <= i < b + t else 0 for i in range(24)])
    for b1, t1 in product(range(7, 24), range(4, 9)):
        for b2, t2 in product(range(b1 + t1 + 2, 24), range(4, 9)):
            if b2 + t2 <= 24 and t1 + t2 <= 10:
                possible.append([1 if b1 <= i < b1 + t1 or b2 <= i < b2 + t2 else 0 for i in range(24)])
    return np.array(possible)


def solve(hour_lbs: list[int], n_doctors: int):
    possible = get_possible_decisions()
    hour_indices = [possible[:, i].nonzero() for i in range(24)]
    night_conflict_indices = np.unique(np.concatenate([[0]] + hour_indices[17:], axis=None))
    model = CpModel()
    doctors = [model.NewBoolVar(f'x_{i:02}_{j}_{k}')
               for i in range(n_doctors)
               for j in range(7)
               for k in range(len(possible))]
    doctors = np.array(doctors).reshape((n_doctors, 7, len(possible)))
    for day_xs in doctors.reshape((-1, len(possible))):
        model.AddAtMostOne(day_xs)
    for d in range(n_doctors):
        for day in range(6):
            model.AddAtMostOne(np.concatenate((doctors[d, day + 1, [0]],
                                               doctors[d, day, night_conflict_indices])))
    for d in range(n_doctors):
        model.Add(sum(doctors[d, :, 0]) <= 2)
    for week_xs in doctors.reshape((n_doctors, -1)):
        model.Add(sum(week_xs) <= 6)
    for day in range(7):
        for hour in range(24):
            model.Add(doctors[:, day, hour_indices[hour]].sum() >= hour_lbs[24 * day + hour])

    model.Minimize((possible.sum(axis=1) * doctors).sum())

    solver = CpSolver()
    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    wall_time = solver.WallTime()

    if status in (OPTIMAL, FEASIBLE):
        objective = solver.ObjectiveValue()
        decisions = np.vectorize(solver.BooleanValue)(doctors)

        def decisions2schedule(arr):
            nonzero = arr.nonzero()[0]
            if nonzero.size:
                return possible[nonzero.item()]
            else:
                return np.zeros(24)

        schedules = np.apply_along_axis(decisions2schedule, 2, decisions)
        return Result(status_name, wall_time, objective,
                      schedules.sum(axis=0).flatten().astype(int),
                      schedules, np.swapaxes(schedules, 0, 1))
    else:
        return Result(status_name, wall_time)


def draw_schedule_1_doctor_1_day(schedule: list[int]):
    plt.imshow([schedule],
               cmap=ListedColormap(['xkcd:white', 'xkcd:pink']),
               extent=(0, 24, -0.5, 0.5))
    plt.grid()
    plt.xticks(range(25))
    plt.yticks([])


def draw_schedule_1_doctor_n_day(schedule: list[list[int]], title=None):
    plt.imshow(schedule,
               cmap=ListedColormap(['xkcd:white', 'xkcd:pink']),
               extent=(0, 24, len(schedule) - 0.5, -0.5))
    plt.xticks(range(25))
    plt.yticks(range(len(schedule)), range(1, len(schedule) + 1))
    plt.yticks([i + 0.5 for i in range(len(schedule) - 1)], minor=True)
    plt.tick_params(axis='y', which='both', length=0)
    plt.grid(axis='x')
    plt.grid(which='minor', axis='y', color='xkcd:black')
    if title is not None:
        plt.title(title)
    plt.gcf().dpi = 300


def draw_schedule_n_doctor_1_day(schedule: list[list[int]], title=None):
    plt.imshow(schedule,
               cmap=ListedColormap(['xkcd:white', 'xkcd:pink']),
               extent=(0, 24, len(schedule) - 0.5, -0.5))
    plt.xticks(range(25))
    plt.yticks(range(len(schedule)), [f'doctor {i}' for i in range(1, len(schedule) + 1)])
    plt.yticks([i + 0.5 for i in range(len(schedule) - 1)], minor=True)
    plt.tick_params(axis='y', which='both', length=0)
    plt.grid(axis='x')
    plt.grid(which='minor', axis='y', color='xkcd:black')
    if title is not None:
        plt.title(title)
    plt.gcf().dpi = 300
