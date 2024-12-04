import pandas as pd
import numpy as np
import math
from GSHP import GSHP


# Optimses BH configuration based on FD approximations and BH-specific calculations.


optim_df = pd.DataFrame(columns=['L', 'n', 'k_s', 'alpha_s', 'capacity'])
for L in np.arange(10, 210, 10):
    k_s_max = 3.2
    if L < 17:
        k_s_min = 2.3
    elif L < 44:
        k_s_min = ((L-17)*1.7 + 17*2.3)/(L)
    elif L < 150:
        k_s_min = ((L-44)*0.22 + (44-17)*1.7 + 17*2.3)/(L)
    elif L < 200:
        k_s_min = ((L-150)*1.7 + (150-44)*0.22 + (44-17)*1.7 + 17*2.3)/(L)

    row = {}
    for k_s in [k_s_min, k_s_max]:
        bh_array = GSHP(
            num_boreholes=25,  # This is not used when optimising
            depth=L, 
            radius=0.06,
            soil_density=2200,
            soil_heat_capacity=710,
            soil_thermal_conductivity=k_s,
            grout_density=1400,
            grout_heat_capacity=800,
            grout_thermal_conductivity=1.4
        )
        Q_max = -GSHP.get_building_load(t=0)
        cop = 3.5
        Q_g_max = bh_array.get_instantaneous_ground_load(Q_max, cop, True)
        Q_allowable_per_bh = -50*L
        safety_factor = 1.5
        num_bhs = math.ceil((Q_g_max/Q_allowable_per_bh)*safety_factor)
        row = {
            'L': L,
            'n': num_bhs,
            'k_s': k_s,
            'alpha_s': bh_array.alpha_s,
            'capacity': num_bhs*50*L,
        }
        optim_df.loc[len(optim_df)+1] = row

    for k_s in [k_s_min, k_s_max]:
        bh_array = GSHP(
            num_boreholes=25,
            depth=L, 
            radius=0.06,
            soil_density=2200,
            soil_heat_capacity=800,
            soil_thermal_conductivity=k_s,
            grout_density=2000,
            grout_heat_capacity=900,
            grout_thermal_conductivity=1.4, 
            pipe_conduction_resistance=5E-7,
            grout_conduction_resistance=1E-6,
            pipe_convection_resistance=5E-4
        )
        for fd in [False]:
            if fd:
                time_step = 3600*12
            else:
                time_step = seconds_in_year/900
            r_crit, num_bhs = bh_array.optimise_borehole_config(
                max_heat_per_metre=50, 
                T_ground=288,
                time_step=time_step,
                is_heating=True,
                fd=fd,
            )
            row = {
                'L': L,
                'n': num_bhs,
                'k_s': k_s,
                'alpha_s': bh_array.alpha_s,
                'capacity': num_bhs*50*L,
                'fd': fd,
                'r_crit': r_crit
            }
            optim_df.loc[len(optim_df)+1] = row

print(optim_df)
optim_df.to_csv('borehole_optim_new_load_prof.csv')