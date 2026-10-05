%% simulation_parameters.m
% Workspace setup script for Resonant_Power_Transfer.slx
%
% Loads the coil, compensation-network, and simulation parameters used
% by the model into the base workspace. Run this before simulating if
% the parameters are not already defined inline in the model.

clear; clc;

%% Resonant tank parameters
Lp = 266e-6;       % Primary (transmitter) coil inductance [H]
Cp = 106e-9;       % Primary compensation capacitance [F]
Ls = 257e-6;       % Secondary (receiver) coil inductance [H]
Cs = 110e-9;       % Secondary compensation capacitance [F]
M  = 85.46e-6;     % Mutual inductance [H]

% Present coil self-resistance (near-ideal baseline).
% Set to ~0.81 Ohm per coil to test the 90% efficiency design budget
% documented in engineering_analysis/Resonant_Efficiency_Loss_Budget.pdf
Rp = 1e-3;         % Primary coil self-resistance [Ohm]
Rs = 1e-3;         % Secondary coil self-resistance [Ohm]

%% Switching / control parameters
Fsw = 30e3;        % PWM switching frequency [Hz]
Tsw = 1/Fsw;       % Switching period [s]
DutyCycle = 0.5;   % Inverter duty cycle

%% Semiconductor parameters
Vf_diode = 0.8;    % Output-bridge diode forward voltage [V]
Ron = 1e-3;        % Switch / diode on-resistance [Ohm]

%% Load / output target operating point
Vout_target = 390;   % Target DC output voltage [V]
Iout_target = 20.4;  % Target DC output current [A]

%% Solver configuration
StopTime = 2;        % Simulation stop time [s]
SampleTime = 1e-6;   % Discrete powergui sample time [s]

fprintf('Simulation parameters loaded into base workspace.\n');
fprintf('Resonant frequency (primary):   %.1f Hz\n', 1/(2*pi*sqrt(Lp*Cp)));
fprintf('Resonant frequency (secondary): %.1f Hz\n', 1/(2*pi*sqrt(Ls*Cs)));
fprintf('Coupling coefficient k:          %.3f\n', M/sqrt(Lp*Ls));
