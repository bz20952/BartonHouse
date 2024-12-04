import numpy as np
import pandas as pd
import math

# Input Variables
monthly_consumption = [16360, 14138, 13848, 12497, 11046, 9787, 
                       9376, 9374, 9826, 11628, 13108, 15018]  # kWh
daily_generation = [180, 280, 420, 562, 664, 706, 686, 605, 474, 325, 204, 150]  # kWh/day
days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Days in each month
battery_efficiency = 0.85  # Adjusted efficiency for aged batteries (85%)
depth_of_discharge = 0.8  # Conservative DoD for aged batteries
battery_capacity = 32.6 * (1 - 0.15)  # Capacity after 15% degradation
safety_margin = 0.1  # 10% Safety Margin

# Hourly consumption and generation profiles (as % of daily total)
hourly_consumption_profile = [5, 4, 3, 3, 4, 5, 8, 10, 12, 10, 8, 5, 5, 4, 3, 3, 4, 5, 8, 10, 12, 10, 8, 5]
hourly_generation_profile = [0, 0, 0, 0, 2, 5, 10, 15, 20, 20, 15, 10, 5, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Normalize profiles to sum to 1
hourly_consumption_profile = np.array(hourly_consumption_profile) / sum(hourly_consumption_profile)
hourly_generation_profile = np.array(hourly_generation_profile) / sum(hourly_generation_profile)

# Initialize storage requirements
results = []

for i in range(12):  # Iterate over each month
    daily_consumption = monthly_consumption[i] / days_in_month[i]
    daily_gen = daily_generation[i]
    
    # Hourly consumption and generation
    hourly_consumption = daily_consumption * hourly_consumption_profile
    hourly_generation = daily_gen * hourly_generation_profile
    
    # Simulate battery operation
    battery_soc = 0  # State of charge (kWh)
    required_storage = 0  # Total storage required (kWh)
    
    for hour in range(24):
        net_energy = hourly_generation[hour] - hourly_consumption[hour]
        if net_energy > 0:  # Surplus, charge the battery
            battery_soc += net_energy * battery_efficiency
            if battery_soc > battery_capacity:
                battery_soc = battery_capacity  # Cap at max capacity
        else:  # Deficit, discharge the battery
            battery_soc += net_energy  # Net energy is negative
            if battery_soc < 0:  # If battery can't meet demand
                required_storage += abs(battery_soc)  # Track unmet demand
                battery_soc = 0  # Battery is depleted

    # Adjust for depth of discharge and safety margin
    adjusted_storage = required_storage / (depth_of_discharge * battery_efficiency)
    adjusted_storage *= (1 + safety_margin)
    total_batteries = math.ceil(adjusted_storage / battery_capacity)
    
    # Store results
    results.append({
        "Month": i + 1,
        "Daily Consumption (kWh)": round(daily_consumption, 2),
        "Daily Generation (kWh)": daily_gen,
        "Required Storage (kWh)": round(adjusted_storage, 2),
        "Batteries Required": total_batteries
    })

# Convert results to a DataFrame for better visualization
df = pd.DataFrame(results)

# Print the results
print("Monthly Battery Storage Requirements:")
print(df.to_string(index=False))

# Calculate and print capacity after degradation and total BESS capacity
actual_battery_capacity = battery_capacity
total_bess_capacity = actual_battery_capacity * df["Batteries Required"].max()

print(f"Capacity After Degradation (kWh): {actual_battery_capacity:.2f}")
print(f"Total BESS Capacity (kWh): {total_bess_capacity:.2f}")
