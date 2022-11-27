from attrs import define, field
from collections import defaultdict
import itertools
import bpsffa


@define
class Doctor:
    periods: list['Period'] = field(factory=list)


@define
class Period:
    begin: int
    end: int

    @property
    def is_night(self):
        return self.begin % 24 == 0 and self.end % 24 == 7


class InitialSolutionGenerator:
    def __init__(self, lams, mu=5.9113, limit=15):
        self.lams = lams
        self.cs = [0 for _ in range(len(lams))]
        self.lens = [0 for _ in range(len(lams) + 1)]
        self.mu = mu
        self.limit = limit
        self.index = 0
        self.doctors: list['Doctor'] = list()

    def __call__(self):
        for _ in self.lams:
            if self.cs[self.index] == 0:
                begin = self._schedule_doctor()
                self._update_lens(begin)
            else:
                self._update_lens(self.index)
            while self.lens[self.index + 1] > self.limit:
                begin = self._schedule_doctor()
                self._update_lens(begin)
            # self.doctors.sort(key=lambda x: len(x.periods))
            self.doctors.sort(key=lambda x: len(set(p.begin // 24 for p in x.periods)))
            # self.doctors.sort(key=lambda x: len(set(p.begin // 24 for p in x.periods)) == self.index // 24 + 1)
            self.index += 1

    def _schedule_doctor(self):
        hour = self.index % 24
        if 0 <= hour < 7:
            return self._schedule_doctor_0_7()
        if 7 <= hour < 13:
            return self._schedule_doctor_7_13()
        else:
            return self._schedule_doctor_13_24()

    def _schedule_doctor_0_7(self):
        day = self.index // 24
        r = None
        for doc in self.doctors:
            if any(p.begin <= self.index < p.end for p in doc.periods):
                continue
            if day == 6 and len(set(p.begin // 24 for p in doc.periods)) == 6:
                continue
            if sum(p.is_night for p in doc.periods) >= 2:
                continue
            prev_day_periods = [p for p in doc.periods if p.begin // 24 == day - 1]
            if any(p.is_night or p.end > 16 for p in prev_day_periods):
                continue
            r = doc
            break
        if r is None:
            r = Doctor()
            self.doctors.append(r)
        begin = day * 24
        period = Period(begin, begin + 7)
        r.periods.append(period)
        for i in range(period.begin, period.end):
            self.cs[i] += 1
        return begin

    def _schedule_doctor_7_13(self):
        day = self.index // 24
        r = None
        for doc in self.doctors:
            if any(p.begin <= self.index < p.end for p in doc.periods):
                continue
            if day == 6 and len(set(p.begin // 24 for p in doc.periods)) == 6:
                continue
            if any(p.is_night for p in doc.periods if p.begin // 24 == day):
                continue
            r = doc
            break
        if r is None:
            r = Doctor()
            self.doctors.append(r)
        begin = self.index
        period = Period(begin, begin + 6)
        r.periods.append(period)
        for i in range(period.begin, period.end):
            self.cs[i] += 1
        return begin

    def _schedule_doctor_13_24(self):
        day = self.index // 24
        period = None
        for doc in self.doctors:
            if any(p.begin <= self.index < p.end for p in doc.periods):
                continue
            if day == 6 and len(set(p.begin // 24 for p in doc.periods)) == 6:
                continue
            day_periods = [p for p in doc.periods if p.begin // 24 == day]
            if any(p.is_night for p in day_periods):
                continue
            if len(day_periods) >= 2:
                continue
            if day_periods and day_periods[0].end + 2 <= self.index:
                period = self._get_period(4)
                doc.periods.append(period)
                break
            if not day_periods:
                period = self._get_period(8)
                doc.periods.append(period)
                break
        if period is None:
            r = Doctor()
            self.doctors.append(r)
            period = self._get_period(8)
            r.periods.append(period)
        for i in range(period.begin, period.end):
            self.cs[i] += 1
        return period.begin

    def _get_period(self, max_duration):
        hour = self.index % 24
        if hour > 20:
            day = self.index // 24
            return Period(24 * day + 20, 24 * day + 24)
        return Period(self.index, self.index + min(max_duration, 24 - hour))

    def _update_lens(self, begin):
        for i in range(begin, self.index + 1):
            lam = self.lams[i]
            c = self.cs[i]
            ll = self.lens[i]
            next_ll = bpsffa.get_next_system_length(self.mu, lam, c, ll)
            self.lens[i + 1] = next_ll


def validate(doctors: list['Doctor']):
    for doc in doctors:
        periods = defaultdict(list)
        for k, v in itertools.groupby(doc.periods, lambda x: x.begin // 24):
            periods[k] += list(v)
        periods = dict(periods)
        assert len(periods) < 7
        assert all(len(ps) == 1 or len(ps) == 2 and all(not p.is_night for p in ps) for ps in periods.values())
        assert all(4 <= p.end - p.begin <= 8 for ps in periods.values() for p in ps)
        assert all(sum(p.end - p.begin for p in ps) <= 10 for ps in periods.values())
        assert all(ps[1].begin - ps[0].end >= 2 for ps in periods.values() if len(ps) == 2)
        assert sum(ps[0].is_night for ps in periods.values()) <= 2
        for d, ps in periods.items():
            if ps[0].is_night:
                if d - 1 in periods:
                    assert all(ps[0].begin - p.end >= 8 for p in periods[d - 1])
                if d + 1 in periods:
                    assert all(p.begin - ps[0].end >= 24 for p in periods[d + 1])
        prev = -1
        for p in doc.periods:
            assert p.begin > prev
            prev = p.end
    cs = [0 for _ in range(7 * 24)]
    for doc in generator.doctors:
        for p in doc.periods:
            for i in range(p.begin, p.end):
                cs[i] += 1
    assert all(cs)


if __name__ == '__main__':
    import pandas as pd

    df = pd.read_csv('lam_2.csv')
    print(df.head())
    lams = df.to_numpy().reshape((-1))
    generator = InitialSolutionGenerator(lams)
    generator()
    score = sum(p.end - p.begin for d in generator.doctors for p in d.periods)
    score += 10 * (len(generator.doctors) - 10)
    print(score)
    validate(generator.doctors)
    cs = [0 for _ in range(7 * 24)]
    for doc in generator.doctors:
        for p in doc.periods:
            for i in range(p.begin, p.end):
                cs[i] += 1
    lens = [0]
    for i, c in enumerate(cs):
        lens.append(bpsffa.get_next_system_length(5.9113, lams[i], c, lens[i]))
    print(repr(cs))
