# Robust Inductive Wireless Electric Vehicle Charging

A design-driven MATLAB Simulink and Simscape Electrical study of resonant inductive wireless charging for an electric vehicle. The project combines a working switching-level simulation with first-principles resonant design, magnetic coupling analysis, loss budgeting, compensation-topology comparison, disturbance studies, and closed-loop output-power regulation.

## Project in one sentence

**A resonant inductive wireless charging system was designed around a 30 kilohertz operating point, implemented as a complete Simulink and Simscape Electrical model, and then evaluated for air-gap variation, lateral displacement, frequency sensitivity, compensation topology, efficiency, and closed-loop power regulation.**

## What I actually engineered

This project was developed to understand **why each part of a wireless charging system is designed the way it is**, rather than treating the simulation as a collection of preselected blocks.

The work covers two complementary layers:

1. **Switching-level implementation:** a complete Simulink and Simscape Electrical model demonstrates contactless power transfer from the source through a high-frequency inverter, resonant transmitter and receiver coils, rectification, filtering, and a battery model.
2. **Engineering design and robustness analysis:** the resonant components, magnetic coupling, equivalent loss resistance, compensation choices, operating frequency, air-gap behavior, lateral displacement, and proportional-integral power regulation were calculated and tested systematically.

The result is therefore both a working wireless charging simulation and an engineering study of how the design behaves when real operating conditions change.

## System architecture

```text
Electrical source
      │
      ▼
High-frequency full-bridge inverter
      │
      ▼
Primary series resonant compensation network
      │
      ▼
Transmitter coil  ))))))  magnetic air gap  ((((((  Receiver coil
                                                │
                                                ▼
                               Secondary series resonant network
                                                │
                                                ▼
                                      Diode bridge rectifier
                                                │
                                                ▼
                                         direct-current filter stage
                                                │
                                                ▼
                                         Battery model
```

There is no direct electrical connection between the transmitter and receiver. Energy crosses the air gap through magnetic coupling.

## Why these design choices were made

### 1. Thirty kilohertz operating frequency

The operating point was selected around 30 kilohertz so that the resonant networks can be tuned to the inverter switching frequency. Resonance reduces the reactive burden of the inductive coils and allows substantial power to be transferred through the magnetic coupling at a practical switching rate for the simulated power stage.

### 2. Series-series compensation

The transmitter and receiver are both compensated with series capacitors. This arrangement was selected as the principal architecture because it gives a direct series resonant path on both sides, keeps the coil currents well defined, and provides a useful balance between power transfer and current stress at the selected coupling level.

The topology study also compared series-parallel, parallel-series, and parallel-parallel compensation. The comparison showed that the selected series-series architecture is the strongest baseline for this design point: it reaches the rated operating point with moderate coil current and approximately 90 percent efficiency under the equivalent loss model.

### 3. Resonant component sizing

The transmitter and receiver inductances were taken from the implemented model and the compensation capacitances were calculated from the resonance relationship:

**f = 1 / (2π√(LC))**

The resulting values place both resonant networks very close to the 30 kilohertz operating frequency.

| Design quantity | Value |
|---|---:|
| Transmitter inductance | 266 microhenry |
| Transmitter compensation capacitance | 106 nanofarad |
| Receiver inductance | 257 microhenry |
| Receiver compensation capacitance | 110 nanofarad |
| Mutual inductance | 85.46 microhenry |
| Nominal coupling coefficient | 0.327 |
| Operating frequency | 30 kilohertz |
| Nominal battery-side voltage | approximately 390 volt |
| Nominal battery-side current | approximately 20.4 ampere |
| Nominal output power | approximately 7.96 kilowatt |
| Design efficiency target | 90 percent |

### 4. Why the loss resistance was studied

The original switching model uses nearly ideal coil resistance, which is useful for demonstrating the power-transfer mechanism but does not represent a realistic loss budget. A separate engineering calculation therefore allocated the 90 percent efficiency target and solved for an **equivalent 0.81 ohm resistance per coil**.

This value is explicitly an equivalent design resistance used to reproduce the planned loss budget. It is not claimed to be the physical winding resistance of a manufactured coil. Real high-frequency coil resistance depends on conductor geometry, skin effect, proximity effect, winding arrangement, and magnetic materials.

### 5. Why air-gap variation was studied

The vehicle will not remain at one exact vertical separation from the charging pad. The project therefore varies the coil separation and recalculates the magnetic coupling. This directly tests whether a fixed inverter command can maintain the desired charging power.

### 6. Why lateral displacement and frequency were studied

Vertical separation is not the only disturbance. Lateral displacement changes the magnetic field overlap, while frequency detuning moves the system away from its resonant operating point. Both were therefore included to identify practical operating limits and sensitive regions.

### 7. Why closed-loop regulation was added

A fixed inverter command cannot maintain constant battery-side power when the magnetic coupling changes. A proportional-integral controller was therefore evaluated as a feedback mechanism. The controller changes inverter phase shift so that the measured charging power returns toward the 7.96 kilowatt reference.

An important result of the study is that the controller regulates power successfully, but it does **not** eliminate the current and efficiency penalty caused by weak coupling. This distinction is important in a real charging system: power regulation and efficiency optimization are related but different control objectives.

## Key results

### Working wireless charging model

The Simulink and Simscape Electrical model implements the complete conversion chain and demonstrates contactless transfer into a battery model. The repository contains the original model file and captured waveforms at the source, primary resonant network, secondary resonant network, rectifier, filtered output, and battery terminals.

### Resonant design

The calculated primary resonant frequency is approximately 29,973 hertz and the calculated secondary resonant frequency is approximately 29,933 hertz. Both are close to the 30 kilohertz switching frequency, confirming the intended resonant design.

### Nominal operating point

At the selected design point, the target battery-side operating condition is approximately 390 volt, 20.4 ampere, and 7.96 kilowatt.

### Air-gap behavior

The analytical robustness study shows that, under the selected series-series architecture and fixed inverter voltage, increasing the air gap can increase the calculated output power in the fundamental-harmonic model. This is counterintuitive but physically consistent with the chosen constant-voltage excitation and the way reflected impedance changes with mutual inductance. The result is exactly why a controller is needed: the charging system must regulate the transferred power rather than assume that larger separation always means less power.

For the equivalent 0.81 ohm coil-resistance case:

| Air gap | Coupling coefficient | Output power |
|---:|---:|---:|
| 10 centimetre | 0.452 | 5.84 kilowatt |
| 12.5 centimetre | 0.382 | 6.86 kilowatt |
| 15 centimetre | 0.327 | 7.96 kilowatt |
| 17.5 centimetre | 0.283 | 9.13 kilowatt |
| 20 centimetre | 0.246 | 10.38 kilowatt |
| 25 centimetre | 0.190 | 13.16 kilowatt |

These values are from the analytical fundamental-harmonic robustness model, not direct switching-level Simulink measurements.

### Lateral displacement

At a 15 centimetre nominal air gap, an 80 millimetre lateral displacement changes the modeled coupling coefficient from 0.327 to approximately 0.302 and increases the calculated output power from approximately 7.96 to 8.57 kilowatt in the open-loop equivalent-loss model.

### Frequency sensitivity

The frequency sweep shows a useful operating region around resonance and identifies off-resonant high-current regions that should be avoided. The calculated efficiency remains close to its best value around 30 to 31 kilohertz, supporting the selected 30 kilohertz operating point.

### Compensation topology comparison

The study compares four compensation arrangements using the same coils and battery condition. The series-series arrangement provides the strongest combination of efficiency and moderate coil current at the selected design point. Parallel-secondary arrangements require substantially higher primary-side current in the studied low-coupling condition, reducing efficiency.

### Closed-loop power regulation

The proportional-integral controller was evaluated for two disturbance cases. For a 15 centimetre to 20 centimetre to 12.5 centimetre to 15 centimetre air-gap sequence, open-loop output varies from approximately 6.86 to 10.38 kilowatt, while the regulated case returns to the 7.96 kilowatt reference after each disturbance.

For the lateral displacement case from zero to 80 millimetres and back to zero, the regulated output remains within approximately ±0.1 percent of the reference in the analytical control model.

For the air-gap step test, the analytical controller returns inside a ±2 percent power band within approximately 9, 16, and 12 milliseconds for the three disturbances tested.

## What the simulation and the design study each prove

It is important to distinguish the two parts of the work.

**The Simulink and Simscape Electrical model proves the complete switching-level wireless power-transfer architecture and battery charging path.**

**The Python engineering study provides systematic parametric and control analysis of coupling, air gap, lateral displacement, frequency, compensation topology, and power regulation.**

The analytical study uses a fundamental-harmonic approximation and therefore does not replace a switching-level validation of every control result.

The current switching-level model uses nearly ideal coil resistance. Consequently, it should not be presented as experimental proof of 90 percent efficiency. The 90 percent figure is a design target validated by the equivalent-loss analytical model. The next physical-model improvement is to insert the equivalent coil resistance into the switching-level model and measure averaged input and output power directly.

## Engineering approach

As an Electronics and Communication Engineering student, I approached the project by focusing on the reasoning behind every implementation choice. Rather than treating the simulation as a collection of blocks, I worked backward from the required charging power, resonant frequency, magnetic coupling, loss budget, and control objective. This led to a workflow of **derive, implement, simulate, compare, identify limitations, and refine**.

That approach is reflected in the repository structure: the switching model is accompanied by resonance calculations, design parameters, a complete robustness analysis, captured waveforms, and a report that explains the engineering decisions and their consequences.

## Repository structure

```text
Robust-Inductive-Wireless-Electric-Vehicle-Charging/
├── README.md
├── LICENSE
├── simulation/
│   ├── Resonant_Power_Transfer.slx
│   └── simulation_parameters.m
├── design/
│   └── resonance_calculations.m
├── analysis/
│   ├── wireless_power_transfer_model.py
│   ├── compensation_topologies.py
│   ├── control_tuning.py
│   ├── run_experiments.py
│   ├── run_log.txt
│   └── results/
├── figures/
│   ├── simulink/
│   ├── waveforms/
│   └── robustness/
└── Robust_Inductive_Wireless_Electric_Vehicle_Charging_Report.pdf
```

## Running the project

### Simulink model

1. Open MATLAB with Simulink and Simscape Electrical installed.
2. Open `simulation/Resonant_Power_Transfer.slx`.
3. Run `simulation/simulation_parameters.m` if the workspace parameters are not already loaded.
4. Run the model and inspect the captured measurement points.
5. Use the figures in `figures/waveforms` to compare the major stages of the power-transfer chain.

### Engineering analysis

From the `analysis` directory:

```bash
python run_experiments.py
```

The analysis requires NumPy, SciPy, and Matplotlib. It regenerates the air-gap, lateral-displacement, frequency, compensation-topology, and closed-loop control results.

## Known limitations and next engineering steps

- The switching-level model currently uses nearly ideal coil resistance.
- The equivalent 0.81 ohm coil resistance should be inserted into the switching model for a direct efficiency validation.
- Real coil geometry should replace the calibrated circular-loop approximation used in the robustness study.
- Ferrite, shielding, conductor skin effect, proximity effect, thermal behavior, and detailed pad geometry are not yet modeled.
- The closed-loop study uses a quasi-static fundamental-harmonic plant with a measurement lag and assumes vehicle-side power feedback without communication delay.
- The controller should ultimately be tested against the full switching model with realistic sensing, sampling, phase-shift limits, and communication delay.

## Future extension

The natural next stage is a high-fidelity closed-loop implementation in the switching-level Simulink model, followed by thermal and magnetic-field constraints and a realistic transmitter and receiver coil geometry. This would connect the current analytical design study to a more physically representative charging-pad design.

## License

Released under the MIT License.
