import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import bpsffa2
import solver_cp


def gen_lbs_1(mu, lams):
    lbs = []
    lens = [0]
    for i in range(7 * 24):
        lbs.append(1)
        while True:
            ll = bpsffa2.get_next_system_length(mu, lams[i], lbs[i], lens[i])
            if ll <= 15:
                lens.append(ll)
                break
            lbs[i] += 1
    return lbs


def gen_lbs_2(mu, lams):
    lbs = [1] * 24 * 7
    lens = [0]
    for i in range(7 * 24):
        while True:
            ll = bpsffa2.get_next_system_length(mu, lams[i], lbs[i], lens[i])
            if ll <= 15:
                lens.append(ll)
                break
            if 0 <= i % 24 < 7:
                begin = i - i % 24
                for j in range(begin, begin + 7):
                    lbs[j] += 1
                for j in range(begin, i):
                    lens[j + 1] = bpsffa2.get_next_system_length(mu, lams[j], lbs[j], lens[j])
            elif 7 <= i % 24 < 11:
                for j in range(i, i + 4):
                    lbs[j] += 1
            else:
                lbs[i] += 1
    return lbs


def gen_lbs_3(mu, lams):
    lbs = [1] * 24 * 7
    lens = [0]
    for i in range(7 * 24):
        while True:
            ll = bpsffa2.get_next_system_length(mu, lams[i], lbs[i], lens[i])
            if ll <= 15:
                lens.append(ll)
                break
            begin = i - i % 24
            if 0 <= i % 24 < 7:
                for j in range(begin, begin + 7):
                    lbs[j] += 1
                for j in range(begin, i):
                    lens[j + 1] = bpsffa2.get_next_system_length(mu, lams[j], lbs[j], lens[j])
            elif 7 <= i % 24 < 11:
                for j in range(i, begin + 11):
                    lbs[j] += 1
            elif 21 <= i % 24 < 24:
                t = i
                while t > begin + 20 and lbs[t - 1] == lbs[i]:
                    t -= 1
                lbs[t] += 1
                for j in range(t, i):
                    lens[j + 1] = bpsffa2.get_next_system_length(mu, lams[j], lbs[j], lens[j])
            else:
                lbs[i] += 1
    return lbs


def solve(hour_lbs: list[int], n_doctors: int):
    result = solver_cp.solve(hour_lbs, n_doctors)
    print(f'{n_doctors=} {result.status} time={result.wall_time:.3f}s')
    if result.ok:
        print(f'objective_base={result.objective}')
        print(f'objective={result.objective + 10 * max(0, n_doctors - 10)}')
    return result


def visualize_result(result: solver_cp.Result, lbs: list[int]):
    img = Path('img')
    if img.exists():
        shutil.rmtree(img)
    img.mkdir()
    (img / 'doctors_view').mkdir()
    (img / 'days_view').mkdir()
    for i in range(7):
        solver_cp.draw_schedule_n_doctor_1_day(result.days_view[i], title=f'day {i + 1}')
        plt.savefig(f'img/days_view/day_{i + 1}')
        plt.show()
    for i in range(len(result.doctors_view)):
        solver_cp.draw_schedule_1_doctor_n_day(result.doctors_view[i], title=f'doctor {i + 1}')
        plt.savefig(f'img/doctors_view/doctor_{i + 1:02}')
        plt.show()
    plt.figure(figsize=(20, 5))
    sns.lineplot(pd.DataFrame({'lbs': lbs, 'n_doctors': result.n_doctors_per_hour}))
    plt.savefig(f'img/lbs_vs_cs')
    plt.show()


def _main():
    mu = 5.9113
    lams = pd.read_csv('lam_2.csv').to_numpy().reshape((-1))
    lbs = gen_lbs_3(mu, lams)

    best_result = None
    best_objective = None
    count_down = 1
    n_doctors = 10
    while count_down:
        result = solve(lbs, n_doctors)
        if result.ok:
            count_down -= 1
            objective = result.objective + 10 * max(0, n_doctors - 10)
            if best_objective is None or objective < best_objective:
                best_objective = objective
                best_result = result
        n_doctors += 1
    print(f'best_n_doctors={len(best_result.doctors_view)}')
    print(f'{best_objective=}')

    lens = [0]
    per_hour = best_result.n_doctors_per_hour
    for i in range(7 * 24):
        lens.append(bpsffa2.get_next_system_length(mu, lams[i], per_hour[i], lens[i]))
    assert all(e <= 15 for e in lens)

    visualize_result(best_result, lbs)


if __name__ == '__main__':
    _main()
