"""
Fundamental-harmonic (FHA) model of an SS/SP-compensated inductive EV charger,
parameterised from rishivexe-alt/Resonant-Inductive-Power-Transfer-for-EVs.

Chain: DC bus -> phase-shift full bridge -> compensated coils -> diode bridge -> CV battery.
All quantities RMS phasors at the fundamental. Battery = constant-voltage sink (390 V).
"""
import numpy as np
from scipy.optimize import brentq

Lp, Cp = 266.16e-6, 105.74e-9
Ls, Cs = 256.79e-6, 109.69e-9
M0 = 85.46e-6
F0 = 30e3
VBAT = 390.0
P_TARGET = 7956.0           # 390 V x 20.4 A
VF, RON = 0.8, 1e-3         # diode drop, on-resistance (repo values)
VDC = 500.0                 # inverter DC bus (Scope01 in repo shows +/-500 V)
K0 = M0 / np.sqrt(Lp * Ls)

def v1_rms(vdc, delta):
    """Fundamental RMS of a phase-shift full-bridge output; delta = phase shift [rad], pi = full square wave."""
    return 4 * vdc / (np.pi * np.sqrt(2)) * np.sin(delta / 2)

_XS = np.logspace(-2, 2.7, 1500)

def solve_ss(f, M, V1, Rp=1e-3, Rs=1e-3, Cp_=Cp, Cs_=Cs, vbat=VBAT):
    """
    Series-series link feeding a diode bridge + CV battery.
    The rectifier input voltage has fundamental magnitude 0.9*Vbat (RMS) and is in phase with I2,
    so Req = 0.9*Vbat/|I2|. Solve the self-consistent |I2| and return a dict of results.
    """
    w = 2 * np.pi * f
    Zp = Rp + 1j * (w * Lp - 1 / (w * Cp_))
    Zs0 = Rs + 1j * (w * Ls - 1 / (w * Cs_))
    jwM = 1j * w * M
    V2 = 0.9 * vbat

    def i2_given(x):
        Req = V2 / x
        Zs = Zs0 + Req
        I2 = (jwM * V1 / Zp) / (Zs + (w * M) ** 2 / Zp)   
        return I2

    def resid(x):
        return abs(i2_given(x)) - x

    xs = _XS
    Zs_v = Zs0 + V2 / xs
    r = np.abs((jwM * V1 / Zp) / (Zs_v + (w * M) ** 2 / Zp)) - xs
    idx = np.nonzero(r[:-1] * r[1:] < 0)[0]
    roots = [brentq(resid, xs[i], xs[i + 1], xtol=1e-12) for i in idx]
    if not roots:
        return dict(P=0.0, Pin=0.0, eff=0.0, I1=abs(V1 / Zp), I2=0.0, Idc=0.0, Vout=vbat, conducting=False)
    x = max(roots)                                      # highest-current (conducting) solution
    Req = V2 / x
    Zs = Zs0 + Req
    I2 = i2_given(x)
    I1 = (V1 - jwM * I2 * 0) / Zp                       
    # Exact loop equations:  V1 = Zp*I1 + jwM*I2 ;  0 = Zs*I2 + jwM*I1  ->  I1 = -Zs*I2/jwM
    I1 = -Zs * I2 / jwM if abs(jwM) > 0 else 0
    return _pack(I1, I2, x, V1, Rp, Rs, vbat, f)

def _pack(I1, I2, x, V1, Rp, Rs, vbat, f=None):
    I1a, I2a = abs(I1), abs(I2)
    Idc = 2 * np.sqrt(2) / np.pi * I2a
    P = vbat * Idc
    P_coil = Rp * I1a**2 + Rs * I2a**2
    P_inv = 2 * RON * I1a**2
    P_dio = 2 * VF * Idc + 2 * RON * I2a**2
    Pin_ac = P + P_coil + P_dio + P_inv
    return dict(P=P, Pin=Pin_ac, eff=P / Pin_ac if Pin_ac > 0 else 0.0, I1=I1a, I2=I2a,
                Idc=Idc, Vout=vbat, P_coil=P_coil, P_dio=P_dio, P_inv=P_inv,
                V1=abs(V1), conducting=True)

def delta_for_power(f, M, P_des, Rp, Rs, vdc=VDC, **kw):
    """Phase-shift angle that delivers P_des (None if outside [0, pi])."""
    g = lambda d: solve_ss(f, M, v1_rms(vdc, d), Rp, Rs, **kw)['P'] - P_des
    try:
        return brentq(g, 0.05, np.pi)
    except ValueError:
        return np.nan

MU0 = 4e-7 * np.pi
def neumann_M(R, gap, lateral=0.0, n=360):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    t1, t2 = np.meshgrid(th, th, indexing='ij')
    dx = R * np.cos(t1) - lateral - R * np.cos(t2)
    dy = R * np.sin(t1) - R * np.sin(t2)
    r = np.sqrt(dx**2 + dy**2 + gap**2)
    return MU0 / (4 * np.pi) * R**2 * np.sum(np.cos(t1 - t2) / r) * (2 * np.pi / n) ** 2

def loop_L1(R, a):
    """Single-turn circular loop self-inductance (wire/bundle radius a)."""
    return MU0 * R * (np.log(8 * R / a) - 2)

def k_geom(R, a, gap, lateral=0.0):
    """Coupling coefficient of two identical N-turn coils = M1/L1 (turn count cancels)."""
    return neumann_M(R, gap, lateral) / loop_L1(R, a)
