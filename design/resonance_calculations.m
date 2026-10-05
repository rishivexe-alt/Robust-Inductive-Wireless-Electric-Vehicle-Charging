%% resonance_calculations.m
% Reproduces the resonant-tuning check, coupling-coefficient calculation,
% and 90% efficiency loss-budget derivation documented in
% Resonant_Efficiency_Loss_Budget.pdf / .docx
%
% All parameters below are taken directly from the Mutual Inductance and
% Series RLC Branch blocks in simulation/Resonant_Power_Transfer.slx.

clear; clc;

%% 1. Model parameters (from the Simulink model)
Lp  = 266e-6;      % Primary inductance [H]
Cp  = 106e-9;      % Primary compensation capacitance [F]
Ls  = 257e-6;      % Secondary inductance [H]
Cs  = 110e-9;      % Secondary compensation capacitance [F]
M   = 85.46e-6;    % Mutual inductance [H]
Fsw = 30000;        % Switching / target resonant frequency [Hz]

Vout = 390;         % Output DC voltage plateau [V]
Iout = 20.4;         % Output DC current plateau [A]
eta_target = 0.90;  % Target overall efficiency
Psem = 35.5;         % Semiconductor conduction-loss allowance [W]

%% 2. Resonant frequency check
fr_p = 1 / (2*pi*sqrt(Lp*Cp));
fr_s = 1 / (2*pi*sqrt(Ls*Cs));

fprintf('--- Resonant Compensation Check ---\n');
fprintf('Primary resonant frequency:   %.1f Hz\n', fr_p);
fprintf('Secondary resonant frequency: %.1f Hz\n', fr_s);
fprintf('Switching frequency:          %.1f Hz\n\n', Fsw);

%% 3. Coupling coefficient
k = M / sqrt(Lp*Ls);
fprintf('--- Magnetic Coupling ---\n');
fprintf('Coupling coefficient k = %.3f\n\n', k);

%% 4. Target efficiency loss budget
Pout = Vout * Iout;
Pin_target = Pout / eta_target;
Ploss_total = Pin_target - Pout;
Pcoil_budget = Ploss_total - Psem;

fprintf('--- 90%% Efficiency Loss Budget ---\n');
fprintf('Pout               = %.1f W\n', Pout);
fprintf('Pin (target)        = %.1f W\n', Pin_target);
fprintf('Total loss budget   = %.1f W\n', Ploss_total);
fprintf('Coil loss budget    = %.1f W\n\n', Pcoil_budget);

%% 5. Equivalent AC load
Rdc = Vout / Iout;
Rac = (8/pi^2) * Rdc;
fprintf('--- Equivalent AC Load ---\n');
fprintf('Rdc = %.2f Ohm,  Rac = %.2f Ohm\n\n', Rdc, Rac);

%% 6. Solve for equivalent per-coil resistance R (Rp = Rs = R)
w = 2*pi*Fsw;
wM = w * M;
fprintf('--- Reflected Impedance ---\n');
fprintf('omega*M = %.2f Ohm\n\n', wM);

% Link output power basis (DC output + output-bridge loss estimate)
Plink_out = Pout + 33.5;
Is = sqrt(Plink_out / Rac);

% Pcoil(R) = R*(Ip(R)^2 + Is^2), with Ip(R) = Is*(R+Rac)/(wM)
Pcoil_fun = @(R) R .* ( (Is.*(R+Rac)./wM).^2 + Is.^2 ) - Pcoil_budget;

R_solution = fzero(Pcoil_fun, 0.5);
Ip_solution = Is * (R_solution + Rac) / wM;

fprintf('--- Equivalent Coil Resistance Solution ---\n');
fprintf('R (per coil)        = %.3f Ohm\n', R_solution);
fprintf('Primary current Ip  = %.2f A RMS\n', Ip_solution);
fprintf('Secondary current Is= %.2f A RMS\n\n', Is);

%% 7. Verification at R = 0.81 Ohm
R = 0.81;
R_reflected = (wM)^2 / (R + Rac);
eta_primary = R_reflected / (R + R_reflected);
eta_secondary = Rac / (R + Rac);
eta_link = eta_primary * eta_secondary;

Ip = 22.98; Is_v = 22.70; % rounded currents from the design note
Pcoil = R * (Ip^2 + Is_v^2);
Ploss_total_check = Pcoil + Psem;
eta_overall = Pout / (Pout + Ploss_total_check);

fprintf('--- Verification at R = 0.81 Ohm ---\n');
fprintf('eta_primary   = %.2f %%\n', eta_primary*100);
fprintf('eta_secondary = %.2f %%\n', eta_secondary*100);
fprintf('eta_link      = %.2f %%\n', eta_link*100);
fprintf('Pcoil         = %.1f W\n', Pcoil);
fprintf('Ploss_total   = %.1f W\n', Ploss_total_check);
fprintf('eta_overall   = %.2f %%\n', eta_overall*100);

fprintf(['\nNOTE: This 90%% figure is an analytical design-budget target.\n', ...
    'The Simulink model currently uses 1 mOhm per-coil self-impedance\n', ...
    '(near-ideal), so simulated link efficiency is presently ~99.99%%.\n', ...
    'Entering R = %.2f Ohm into each coil''s SelfImpedance and measuring\n', ...
    'average input/output power in simulation is required to validate\n', ...
    'this target. See simulation_results/Results_Summary.md.\n'], R_solution);
