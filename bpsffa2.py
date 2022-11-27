import math


def get_system_length(rho, c):
    r = rho / (1 - rho)
    r /= 1 + (1 - rho) * sum((c * rho) ** k / math.factorial(k) for k in range(c)) * math.factorial(c) / (c * rho) ** c
    r += c * rho
    return r


def estimate_rho(mu, lam, c, length):
    low, high = 0, 1
    for _ in range(20):
        mid = (low + high) / 2
        ll = get_system_length(mid, c) + mu * mid * c - lam
        if ll == length:
            break
        if ll < length:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def get_next_system_length(mu, lam, c, length):
    rho = estimate_rho(mu, lam, c, length)
    return max(length + lam - mu * rho * c, 0)
