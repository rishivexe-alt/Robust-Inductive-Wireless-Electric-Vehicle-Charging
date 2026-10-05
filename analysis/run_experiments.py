import sys, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import brentq, fsolve
from wireless_power_transfer_model import *
import compensation_topologies as T

OUT = "results"
LAV = np.sqrt(Lp * Ls)
A_BUNDLE = 0.02
R_LOOP = brentq(lambda R: k_geom(R, A_BUNDLE, 0.15) - K0, 0.1, 0.4)
Mgap = lambda g, x=0.0: k_geom(R_LOOP, A_BUNDLE, g, x) * LAV

CASES = {"R = 0.81 ohm per coil (repo loss budget)": 0.81, "R = 0.10 ohm per coil (assumed low-loss Litz)": 0.10}
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
COL = [BLUE, ORANGE, AQUA, VIOLET]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 130})

def save_csv(name, rows):
    with open(f"{OUT}/{name}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

nominal = {}
for lab, R in CASES.items():
    d = delta_for_power(F0, M0, P_TARGET, R, R)
    nominal[lab] = (R, d, v1_rms(VDC, d))

# ------------------------------------------------ A: air-gap sweep (open loop, inverter command fixed)
gaps = [0.10, 0.125, 0.15, 0.175, 0.20, 0.25]
rowsA = []
for lab, (R, d, V1) in nominal.items():
    for g in gaps:
        M = Mgap(g); r = solve_ss(F0, M, V1, R, R)
        rowsA.append(dict(case=lab, gap_cm=g * 100, M_uH=M * 1e6, k=M / LAV, Vout_V=VBAT, Iout_A=r["Idc"],
                          Pout_W=r["P"], I1_A=r["I1"], I2_A=r["I2"], Pin_W=r["Pin"], eff_pct=r["eff"] * 100))
save_csv("A_air_gap_sweep", rowsA)

# ------------------------------------------------ B: lateral misalignment sweep at 15 cm gap
lats = [0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12]
rowsB = []
for lab, (R, d, V1) in nominal.items():
    for x in lats:
        M = Mgap(0.15, x); r = solve_ss(F0, M, V1, R, R)
        rowsB.append(dict(case=lab, lateral_mm=x * 1000, M_uH=M * 1e6, k=M / LAV, Iout_A=r["Idc"], Pout_W=r["P"],
                          I1_A=r["I1"], I2_A=r["I2"], eff_pct=r["eff"] * 100))
save_csv("B_misalignment_sweep", rowsB)

# ------------------------------------------------ C: frequency sweep (open loop, nominal coupling)
fgrid = np.arange(20e3, 40e3 + 1, 250)
rowsC = []
for lab, (R, d, V1) in nominal.items():
    for f in fgrid:
        r = solve_ss(f, M0, V1, R, R)
        rowsC.append(dict(case=lab, f_kHz=f / 1e3, Pout_W=r["P"], I1_A=r["I1"], I2_A=r["I2"],
                          eff_pct=r["eff"] * 100 if r["P"] > 0 else 0.0, conducting=int(r["conducting"])))
save_csv("C_frequency_sweep", rowsC)

# ------------------------------------------------ D: compensation topologies (R = 0.81, same coils, same battery)
R = 0.81
w0 = 2 * np.pi * F0
design = {}
# SS: repo values, phase-shift sets power
d = delta_for_power(F0, M0, P_TARGET, R, R); design["SS"] = dict(Cp_=Cp, Cs_=Cs, Lf=0.0, V1=v1_rms(VDC, d))
# SP: tune series Cp for zero input phase and delta for power
def tuneSP(u):
    Cp_ = u[0] * 1e-7
    g = lambda dd: T.solve("SP", F0, M0, v1_rms(VDC, dd), R, R, Cp_=Cp_)["P"] - P_TARGET
    try:
        dd = brentq(g, 0.05, np.pi)
    except ValueError:
        return [10.0], np.pi
    r = T.solve("SP", F0, M0, v1_rms(VDC, dd), R, R, Cp_=Cp_)
    return [np.radians(r["phi_in"])], dd
Cp_seed = 1 / (w0**2 * (Lp - M0**2 / Ls)) * 1e7          # analytic SP primary tuning as the seed
Cp_sp = fsolve(lambda u: tuneSP(u)[0], [Cp_seed])[0] * 1e-7
design["SP"] = dict(Cp_=Cp_sp, Cs_=Cs, Lf=0.0, V1=v1_rms(VDC, tuneSP([Cp_sp * 1e7])[1]))
# PS / PP: V1 = full square wave, solve (Cp, Lf) for rated power + zero input phase
V1full = v1_rms(VDC, np.pi)
for topo in ("PS", "PP"):
    def res(u):
        r = T.solve(topo, F0, M0, V1full, R, R, Cp_=u[0] * 1e-7, Lf=u[1] * 1e-4)
        return [1e3, 1e3] if not r["ok"] else [(r["P"] - P_TARGET) / 1e3, np.radians(r["phi_in"])]
    u = fsolve(res, [1.7, 3.0]); design[topo] = dict(Cp_=u[0] * 1e-7, Cs_=Cs, Lf=u[1] * 1e-4, V1=V1full)

rowsD, rowsDn = [], []
for topo, p in design.items():
    r0 = T.solve(topo, F0, M0, p["V1"], R, R, Cp_=p["Cp_"], Cs_=p["Cs_"], Lf=p["Lf"])
    rowsDn.append(dict(topology=topo, Cp_nF=p["Cp_"] * 1e9, Lf_uH=p["Lf"] * 1e6, V1_V=p["V1"], Pout_W=r0["P"],
                       eff_pct=r0["eff"] * 100, I1_coil_A=r0["I1"], I_source_A=r0["Iin"], I2_A=r0["I2"], input_phase_deg=r0["phi_in"]))
    for g in gaps:
        r = T.solve(topo, F0, Mgap(g), p["V1"], R, R, Cp_=p["Cp_"], Cs_=p["Cs_"], Lf=p["Lf"])
        rowsD.append(dict(topology=topo, gap_cm=g * 100, k=Mgap(g) / LAV, Pout_W=r["P"], eff_pct=r["eff"] * 100,
                          I1_coil_A=r["I1"], I_source_A=r["Iin"], I2_A=r["I2"], input_phase_deg=r["phi_in"]))
save_csv("D_topology_nominal", rowsDn); save_csv("D_topology_gap_sweep", rowsD)

# ------------------------------------------------ E: closed-loop power regulation (phase-shift PI)
R = 0.81
dnom = nominal[list(CASES)[0]][1]
def plant(delta, M): return solve_ss(F0, M, v1_rms(VDC, delta), R, R)
# local plant gain for tuning
dP = (plant(dnom + 0.01, M0)["P"] - plant(dnom - 0.01, M0)["P"]) / 0.02
def simulate(Mfun, T_end, closed, tau=0.003, dt=2e-4, Kp_n=1.0, Ti=0.003):
    n = int(T_end / dt); t = np.arange(n) * dt
    Kp = Kp_n / dP; Ki = Kp / Ti
    delta, integ, P_meas = dnom, 0.0, P_TARGET
    log = {k: np.zeros(n) for k in ("t", "M", "delta", "P", "I1", "eff")}
    for i in range(n):
        M = Mfun(t[i]); r = plant(delta, M)
        P_meas += dt / tau * (r["P"] - P_meas)               # sensing / battery-filter lag
        if closed:
            e = P_TARGET - P_meas
            u = dnom + Kp * e + integ
            if 0.15 < u < np.pi or (u >= np.pi and e < 0) or (u <= 0.15 and e > 0):
                integ += Ki * e * dt
            delta = float(np.clip(dnom + Kp * e + integ, 0.15, np.pi))
        log["t"][i], log["M"][i], log["delta"][i], log["P"][i], log["I1"][i], log["eff"][i] = t[i], M, delta, P_meas, r["I1"], r["eff"]
    return log
def ramp(t, t0, t1, a, b): return a + (b - a) * np.clip((t - t0) / (t1 - t0), 0, 1)
_lat_x = np.linspace(0, 0.08, 41); _lat_M = np.array([Mgap(0.15, x) for x in _lat_x])
_gap_cache = {g: Mgap(g) for g in (0.125, 0.15, 0.20)}
M_lat = lambda x: float(np.interp(x, _lat_x, _lat_M))
scen = {
  "E1: lateral misalignment 0 -> 80 mm -> 0 (15 cm gap)":
      lambda t: M_lat(ramp(t, .2, .6, 0, .08) if t < .9 else ramp(t, 1.0, 1.4, .08, 0)),
  "E2: air-gap steps 15 -> 20 -> 12.5 -> 15 cm":
      lambda t: _gap_cache[0.15 if t < .3 else 0.20 if t < .8 else 0.125 if t < 1.3 else 0.15]}
E = {}
for name, Mf in scen.items():
    E[name] = (simulate(Mf, 1.8, False), simulate(Mf, 1.8, True))
    for tag, lg in zip(("open", "closed"), E[name]):
        save_csv(f"E_{name[:2]}_{tag}", [dict(t_s=lg["t"][j], k=lg["M"][j] / LAV, delta_deg=np.degrees(lg["delta"][j]), Pout_W=lg["P"][j],
                                          I1_A=lg["I1"][j], eff_pct=lg["eff"][j] * 100) for j in range(0, len(lg["t"]), 25)])
import control_tuning as CT
# regulation range: M range where P = target is reachable at the DC bus limit
Mreach = lambda: brentq(lambda M: solve_ss(F0, M, v1_rms(VDC, np.pi), R, R)["P"] - P_TARGET, 20e-6, 160e-6)

# ------------------------------------------------ figures
def label_last(ax, x, y, text, color):
    ax.annotate(text, (x[-1], y[-1]), xytext=(4, 0), textcoords="offset points", color="#333", fontsize=8, va="center")

# A
fig, ax = plt.subplots(1, 4, figsize=(15, 3.6))
for (lab, _), c in zip(nominal.items(), (BLUE, ORANGE)):
    rr = [r for r in rowsA if r["case"] == lab]; g = [r["gap_cm"] for r in rr]
    for a, key, yl in zip(ax, ("k", "Pout_W", "I1_A", "eff_pct"), ("coupling k", "Pout [W]", "primary current [A rms]", "efficiency [%]")):
        a.plot(g, [r[key] for r in rr], "-o", color=c, lw=2, ms=5, label=lab.split(" (")[0].replace("R = ", "R="))
        a.set_xlabel("air gap [cm]"); a.set_ylabel(yl)
ax[1].axhline(P_TARGET, color="#888", ls="--", lw=1); ax[1].text(10, P_TARGET * 1.02, "7.96 kW rating", color="#555", fontsize=8)
ax[3].legend(frameon=False, fontsize=8)
fig.suptitle("Experiment A - air-gap sweep (open loop: inverter command fixed at the 15 cm design point)", y=1.02); fig.tight_layout(); fig.savefig(f"{OUT}/A_air_gap.png", bbox_inches="tight"); plt.close(fig)
# B
fig, ax = plt.subplots(1, 4, figsize=(15, 3.6))
for (lab, _), c in zip(nominal.items(), (BLUE, ORANGE)):
    rr = [r for r in rowsB if r["case"] == lab]; x = [r["lateral_mm"] for r in rr]
    for a, key, yl in zip(ax, ("k", "Pout_W", "I1_A", "eff_pct"), ("coupling k", "Pout [W]", "primary current [A rms]", "efficiency [%]")):
        a.plot(x, [r[key] for r in rr], "-o", color=c, lw=2, ms=5, label=lab.split(" (")[0].replace("R = ", "R=")); a.set_xlabel("lateral displacement [mm]"); a.set_ylabel(yl)
ax[3].legend(frameon=False, fontsize=8)
fig.suptitle("Experiment B - lateral misalignment at 15 cm gap (open loop)", y=1.02); fig.tight_layout(); fig.savefig(f"{OUT}/B_misalignment.png", bbox_inches="tight"); plt.close(fig)
# C
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.6))
for (lab, _), c in zip(nominal.items(), (BLUE, ORANGE)):
    rr = [r for r in rowsC if r["case"] == lab]; f = [r["f_kHz"] for r in rr]
    for a, key, yl in zip(ax, ("Pout_W", "eff_pct", "I1_A"), ("Pout [W]", "efficiency [%]", "primary current [A rms]")):
        a.plot(f, [(np.nan if (key == "eff_pct" and not r["conducting"]) else r[key]) for r in rr], color=c, lw=2, label=lab.split(" (")[0].replace("R = ", "R=")); a.set_xlabel("frequency [kHz]"); a.set_ylabel(yl); a.axvline(30, color="#aaa", lw=1)
ax[1].legend(frameon=False, fontsize=8)
fig.suptitle("Experiment C - frequency sweep, nominal coupling (open loop, 30 kHz marked)", y=1.02); fig.tight_layout(); fig.savefig(f"{OUT}/C_frequency.png", bbox_inches="tight"); plt.close(fig)
# D
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.6))
for topo, c in zip(design, COL):
    rr = [r for r in rowsD if r["topology"] == topo]; g = [r["gap_cm"] for r in rr]
    for a, key, yl in zip(ax, ("Pout_W", "eff_pct", "I_source_A"), ("Pout [W]", "efficiency [%]", "inverter output current [A rms]")):
        a.plot(g, [(np.nan if r["Pout_W"] <= 0 else r[key]) for r in rr], "-o", color=c, lw=2, ms=4, label=topo); a.set_xlabel("air gap [cm]"); a.set_ylabel(yl)
ax[1].legend(frameon=False, fontsize=8, ncol=2)
fig.suptitle("Experiment D - compensation topologies, each tuned for 7.96 kW + zero input phase at 15 cm (R = 0.81 ohm)", y=1.02); fig.tight_layout(); fig.savefig(f"{OUT}/D_topologies.png", bbox_inches="tight"); plt.close(fig)
# E
for (name, (op, cl)), tag in zip(E.items(), ("E1", "E2")):
    fig, ax = plt.subplots(1, 4, figsize=(15, 3.4))
    for a, key, yl, sc in zip(ax, ("M", "P", "I1", "delta"), ("coupling k", "Pout [W]", "primary current [A rms]", "phase shift [deg]"), (1 / LAV, 1, 1, 180 / np.pi)):
        if key != "M":
            a.plot(op["t"], op[key] * sc, color=ORANGE, lw=2, label="open loop"); a.plot(cl["t"], cl[key] * sc, color=BLUE, lw=2, label="PI closed loop")
        else: a.plot(op["t"], op[key] * sc, color="#444", lw=2)
        a.set_xlabel("time [s]"); a.set_ylabel(yl)
    ax[1].axhline(P_TARGET, color="#888", ls="--", lw=1); ax[1].legend(frameon=False, fontsize=8)
    fig.suptitle(name + "  (quasi-static FHA plant, R = 0.81 ohm)", y=1.02); fig.tight_layout(); fig.savefig(f"{OUT}/{tag}_control.png", bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------ console summary
print(f"coil-pair surrogate: loop radius {R_LOOP*100:.1f} cm, bundle radius {A_BUNDLE*100:.0f} mm; rated power is reachable at full DC-bus drive only up to M = {Mreach()*1e6:.1f} uH (k <= {Mreach()/LAV:.3f}); tighter coupling needs more bus voltage")
for lab, (Rr, d, V1) in nominal.items(): print(f"nominal [{lab}]: delta={np.degrees(d):.1f} deg  V1={V1:.1f} V")
def show(rows, cols):
    print(" | ".join(f"{c:>11}" for c in cols))
    for r in rows: print(" | ".join(f"{r[c]:>11.2f}" if isinstance(r[c], (int, float, np.floating)) else f"{str(r[c])[:11]:>11}" for c in cols))
for lab in CASES:
    print("\nA", lab); show([r for r in rowsA if r["case"] == lab], ["gap_cm", "k", "M_uH", "Pout_W", "Iout_A", "I1_A", "I2_A", "eff_pct"])
for lab in CASES:
    print("\nB", lab); show([r for r in rowsB if r["case"] == lab], ["lateral_mm", "k", "M_uH", "Pout_W", "Iout_A", "I1_A", "eff_pct"])
for lab in CASES:
    rr = [r for r in rowsC if r["case"] == lab and abs((r["f_kHz"] * 1000) % 2500) < 1e-6]
    print("\nC", lab); show(rr, ["f_kHz", "Pout_W", "I1_A", "I2_A", "eff_pct"])
    best = max([r for r in rowsC if r["case"] == lab], key=lambda r: r["eff_pct"]); print(f"   peak efficiency {best['eff_pct']:.2f}% at {best['f_kHz']:.2f} kHz")
print("\nD nominal"); show(rowsDn, ["topology", "Cp_nF", "Lf_uH", "V1_V", "Pout_W", "eff_pct", "I1_coil_A", "I_source_A", "input_phase_deg"])
for topo in design:
    rr = [r for r in rowsD if r["topology"] == topo]
    P = np.array([r["Pout_W"] for r in rr]); eta = np.array([r["eff_pct"] for r in rr]); Is = np.array([r["I_source_A"] for r in rr])
    print(f"D {topo}: P range {P.min():.0f}-{P.max():.0f} W, eff {eta.min():.1f}-{eta.max():.1f}%, source current max {np.nanmax(Is):.1f} A; no-conduction gaps: {[int(g*100) if g*100==int(g*100) else g*100 for g,p in zip(gaps,P) if p<=0]}")
    print("   P by gap:", [round(float(p)) for p in P])
for name, (op, cl) in E.items():
    print("\n", name)
    if name.startswith('E2'):
        for tag, lg in (("open", op), ("closed", cl)):
            print(f"  {tag:6} step response (peak deviation %, time to stay within +/-2% ms) at t=0.3/0.8/1.3 s:", [(round(a,1), round(b)) for a,b in CT.metrics(lg['t'], lg['P'])])
    for tag, lg in (("open", op), ("closed", cl)):
        mask = lg["t"] > 0.1
        print(f"  {tag:6}: P min/max {lg['P'][mask].min():.0f}/{lg['P'][mask].max():.0f} W   I1 max {lg['I1'].max():.1f} A   eff min {lg['eff'].min()*100:.1f}%   delta range {np.degrees(lg['delta'].min()):.0f}-{np.degrees(lg['delta'].max()):.0f} deg")
    # settled values at end of each segment
    for tt in (0.55, 0.75, 1.25, 1.75):
        j = int(tt / 2e-4); print(f"   t={tt}: k={cl['M'][j]/LAV:.3f} open P={op['P'][j]:.0f} closed P={cl['P'][j]:.0f} W, closed I1={cl['I1'][j]:.1f} A eff={cl['eff'][j]*100:.1f}%  delta={np.degrees(cl['delta'][j]):.0f}")
