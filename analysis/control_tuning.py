import numpy as np
from scipy.optimize import brentq
from wireless_power_transfer_model import *
LAV = np.sqrt(Lp*Ls); A = 0.02
Rl = brentq(lambda R: k_geom(R, A, 0.15) - K0, 0.1, 0.4)
Mg = {g: k_geom(Rl, A, g)*LAV for g in (0.125, 0.15, 0.20)}
R = 0.81; dnom = delta_for_power(F0, M0, P_TARGET, R, R)
plant = lambda d, M: solve_ss(F0, M, v1_rms(VDC, d), R, R)
dP = (plant(dnom+.01, M0)['P'] - plant(dnom-.01, M0)['P'])/.02
def sim(Mfun, T, Kp_n, Ti, tau=0.003, dt=2e-4):
    n = int(T/dt); t = np.arange(n)*dt; Kp = Kp_n/dP; Ki = Kp/Ti
    delta, integ, Pm = dnom, 0.0, P_TARGET; P = np.zeros(n); D = np.zeros(n)
    for i in range(n):
        r = plant(delta, Mfun(t[i])); Pm += dt/tau*(r['P']-Pm)
        e = P_TARGET-Pm; u = dnom+Kp*e+integ
        if 0.15 < u < np.pi or (u >= np.pi and e < 0) or (u <= 0.15 and e > 0): integ += Ki*e*dt
        delta = float(np.clip(dnom+Kp*e+integ, 0.15, np.pi)); P[i] = Pm; D[i] = delta
    return t, P, D
steps = lambda t: Mg[0.15 if t < .3 else 0.20 if t < .8 else 0.125 if t < 1.3 else 0.15]
def metrics(t, P):
    out = []
    for t0 in (.3, .8, 1.3):
        m = (t >= t0) & (t < t0+0.5); e = (P[m]-P_TARGET)/P_TARGET; tt = t[m]-t0
        bad = np.nonzero(np.abs(e) > 0.02)[0]
        out.append((100*np.abs(e).max(), 1000*(tt[min(bad[-1]+1, len(tt)-1)] if len(bad) else 0)))
    return out
if __name__ == "__main__":
    for Kp_n, Ti in [(0.25, .02), (0.5, .006), (0.8, .003), (1.0, .003), (1.5, .003), (1.0, .006)]:
        t, P, D = sim(steps, 1.8, Kp_n, Ti)
        m = metrics(t, P)
        print(f"Kp_n={Kp_n} Ti={Ti*1000:.0f}ms | " + " | ".join(f"peak dev {a:4.1f}% settle {b:5.0f} ms" for a, b in m), "| ripple-free?", np.abs(np.diff(P[-500:])).max() < 1)
