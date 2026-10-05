"""
General fundamental-harmonic solver for SS / SP / PS / PP, same coils, same CV-battery + diode-bridge load.
Rectifier-input voltage Vc has fixed RMS magnitude 0.9*Vbat and the rectifier input current is in phase
with Vc (diode bridge into a CV battery).  Unknowns: phase theta of Vc and rectifier current r.
Parallel primary needs a series input inductor Lf (a voltage-fed inverter cannot drive Cp in parallel directly).
"""
import numpy as np
from scipy.optimize import fsolve
from wireless_power_transfer_model import Lp, Ls, Cp, Cs, VBAT, VF, RON, F0, v1_rms, VDC

def solve(topo, f, M, V1, Rp, Rs, Cp_=Cp, Cs_=Cs, Lf=0.0, vbat=VBAT, guess=(0.0, 20.0)):
    w = 2 * np.pi * f
    pri_par, sec_par = topo[0] == 'P', topo[1] == 'P'
    jwM = 1j * w * M
    Zc_sec = Rs + 1j * w * Ls + (0 if sec_par else 1 / (1j * w * Cs_))
    Zc_pri = Rp + 1j * w * Lp + (0 if pri_par else 1 / (1j * w * Cp_))
    V2 = 0.9 * vbat

    def network(theta, r):
        Vc = V2 * np.exp(1j * theta)
        Ir = r * np.exp(1j * theta)
        Is = (1j * w * Cs_ * Vc + Ir) if sec_par else Ir
        # secondary loop:  Zc_sec*Is_coil + jwM*I1 + Vc = 0 ; Is_coil = Is for S, coil current for P
        Icoil2 = Ir + 1j * w * Cs_ * Vc if sec_par else Ir
        I1 = -(Zc_sec * Icoil2 + Vc) / jwM
        Vn = Zc_pri * I1 + jwM * Icoil2
        if pri_par:
            Ilf = 1j * w * Cp_ * Vn + I1
            Vsrc = 1j * w * Lf * Ilf + Vn
            Iin = Ilf
        else:
            Vsrc, Iin = Vn, I1
        return Vsrc, I1, Icoil2, Ir, Iin

    def resid(u):
        Vs, *_ = network(u[0], u[1])
        return [Vs.real - V1, Vs.imag]
    best = None
    for th0 in (guess[0], -0.5, 0.5, 1.5, -1.5, 3.0):
        for r0 in (guess[1], 10.0, 30.0, 60.0):
            u, info, ier, _ = fsolve(resid, [th0, r0], full_output=True, xtol=1e-12)
            if ier == 1 and u[1] > 0:
                if best is None or u[1] > best[1]:
                    best = u
    if best is None:
        return dict(P=0.0, eff=0.0, I1=np.nan, I2=0.0, Pin=0.0, Iin=np.nan, Idc=0.0, phi_in=np.nan, ok=False)
    _, I1, I2c, Ir, Iin = network(*best)
    Idc = 2 * np.sqrt(2) / np.pi * abs(Ir)
    P = vbat * Idc
    P_coil = Rp * abs(I1) ** 2 + Rs * abs(I2c) ** 2
    P_inv = 2 * RON * abs(Iin) ** 2
    P_dio = 2 * VF * Idc + 2 * RON * abs(Ir) ** 2
    Pin = P + P_coil + P_dio + P_inv
    Vs, *_ = network(*best)
    pf = np.cos(np.angle(V1) - np.angle(Iin))   # source PF reference: V1 real
    return dict(P=P, Pin=Pin, eff=P / Pin, I1=abs(I1), I2=abs(I2c), Iin=abs(Iin), Idc=Idc,
                ok=True, phi_in=np.degrees(np.angle(Iin)))
