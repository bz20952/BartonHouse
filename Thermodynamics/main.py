from GSHP import GSHP, seconds_in_year

# Work out estimated usage statistics

elec_price_per_kwh = 0.10
# gas_price_per_kwh = 0.024
# gas_efficiency = 0.94
num_bhs = 11

# New (referenced) values
bh_array = GSHP(
    num_boreholes=num_bhs,
    depth=190, 
    radius=0.06,
    soil_density=2200,
    soil_heat_capacity=710,
    soil_thermal_conductivity=2.3,
    grout_density=1400,
    grout_heat_capacity=800,
    grout_thermal_conductivity=1.4
)

# print(bh_array.calc_conduction_resistance(0.015, 54))  # 54 W/(mK) is thermal cond of steel (Eng toolbox)
# print(bh_array.calc_conduction_resistance(0.09, 1.4))  # 1.4 is grout thermal conductivity
# print(bh_array.calc_convection_resistance(0.015, 500))  # 500 is forced convective heat transfer coefficient of air

system_props = bh_array.model_single_bh(
    t_n=seconds_in_year,
    time_step=8*3600,
    T_ground=288,
    is_heating=True
)
bh_array.plot(system_props, ['Ground load per BH (W)', 'Elec per BH (W)'], ['COP'])
# bh_array.plot(system_props, ['Interface temp (K)', 'Borehole outlet/heat pump inlet temp (K)'], [])

annual_heating_demand = (sum(system_props['Building load per BH (W)'].values)/1000)*8*num_bhs
annual_elec_consumption = (sum(system_props['Elec per BH (W)'].values)/1000)*8*num_bhs
max_elec_consumption = max(system_props['Elec per BH (W)'].values)/1000*num_bhs
avg_elec_comsumption = ((sum(system_props['Elec per BH (W)'].values)/len(system_props['Elec per BH (W)'].values)))/1000*num_bhs
avg_ground_load = ((sum(system_props['Ground load per BH (W)'].values)/len(system_props['Ground load per BH (W)'].values)))/1000*num_bhs
max_ground_load = max(system_props['Ground load per BH (W)'].values)/1000*num_bhs
print('Annual heating demand:', annual_heating_demand, 'kWh')
print('Annual HP elec demand:', annual_elec_consumption, 'kWh')
print('Max HP elec demand:', max_elec_consumption, 'kW')
print('Avg HP elec demand:', avg_elec_comsumption, 'kW')
print('Max ground load:', max_ground_load, 'kW')
print('Avg ground load:', avg_ground_load, 'kW')
# print('Month by month avg HP elec demand:', system_props['Elec per BH (W)'].values[45::92]/1000*num_bhs)

print('Current annual elec bill: £', annual_heating_demand*elec_price_per_kwh)
print('Projected annual elec bill: £', annual_elec_consumption*elec_price_per_kwh)
print('Projected annual saving (£):', annual_heating_demand*elec_price_per_kwh - annual_elec_consumption*elec_price_per_kwh)
print('Projected annual saving (%):', (annual_heating_demand - annual_elec_consumption)/(annual_heating_demand)*100)