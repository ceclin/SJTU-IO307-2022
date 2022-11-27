import math


def approximate_system_length(rho, c):
    cf = math.factorial(c)
    r = (rho * c) ** (c + 1)
    r /= cf * (1 - rho) ** 2
    r /= sum((rho * c) ** n / math.factorial(n) for n in range(c)) + (rho * c) ** c / (cf * (1 - rho))
    r *= 1 - 1 / (16 * rho * c)
    r += rho * c
    return r


def get_system_length(rho, c):
    r = rho / (1 - rho)
    r /= 1 + (1 - rho) * sum((c * rho) ** k / math.factorial(k) for k in range(c)) * math.factorial(c) / (c * rho) ** c
    r += c * rho
    return r


def estimate_rho(c, length):
    low, high = 0, 1
    for _ in range(10):
        mid = (low + high) / 2
        ll = get_system_length(mid, c)
        if ll == length:
            break
        if ll < length:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def get_correction_factor(mu, c):
    return 1 - 1.09 / (c ** 0.866 * mu ** 1.045)


# Should first sub-period use last_c?
def get_next_system_length(mu, lam, c, length, n_points=None):
    tmu = mu * c
    if n_points is None:
        n_points = math.ceil(tmu)
    smu = tmu / n_points
    slam = lam / n_points
    ll = length
    for _ in range(n_points):
        rho = estimate_rho(c, ll)
        ll = max(ll + slam - smu * rho, 0)
    return ll
