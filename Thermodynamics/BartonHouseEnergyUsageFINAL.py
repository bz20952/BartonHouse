import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib.dates as mdates

# Path to the Excel file (replace with correct path)
file_path = 'ONS Data.xlsx'

# Load the ONS Data from the Excel file, specifically the "PyData" sheet
ons_data = pd.read_excel(file_path, sheet_name="PyData")

# Strip any leading/trailing spaces in column names (if necessary)
ons_data.columns = ons_data.columns.str.strip()

# Convert the 'Month' column to datetime format, assuming it's in format like "January 2021"
ons_data['Datetime'] = pd.to_datetime(ons_data['Month'], format='%B %Y')

# Extract month names (ignoring the year)
ons_data['Month'] = ons_data['Datetime'].dt.month_name().str.slice(stop=3)  # e.g., "Jan", "Feb"

# Convert the Domestic Sales [TWh] to kWh
ons_data['Domestic_Sales_kWh'] = ons_data['Domestic Sales [TWh]'] * 1e6  # Convert TWh to kWh

# Group by month and calculate the mean and standard deviation
monthly_avg = ons_data.groupby('Month')['Domestic_Sales_kWh'].mean()
monthly_std = ons_data.groupby('Month')['Domestic_Sales_kWh'].std()

# Known total annual demand for the block of flats
# total_annual_demand_flats = 526960  # kWh for the entire year
total_annual_demand_flats = 604921  # kWh for the entire year

# Scale the average profile to match the total annual demand of the flats
scaled_monthly_avg = (monthly_avg / monthly_avg.sum()) * total_annual_demand_flats
scaled_monthly_std = (monthly_std / monthly_avg.sum()) * total_annual_demand_flats

# Reorder the months to follow the calendar order (Jan, Feb, ..., Dec)
months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
scaled_monthly_avg = scaled_monthly_avg.reindex(months_order)
scaled_monthly_std = scaled_monthly_std.reindex(months_order)

# Set default font size
font = {'size': 15}
rc('font', **font)

# Plot average monthly energy usage with standard deviation error bars
plt.figure(figsize=(12, 6))
plt.errorbar(scaled_monthly_avg.index, scaled_monthly_avg, yerr=scaled_monthly_std, fmt='o-', capsize=5)
# plt.title("Estimated Barton House Energy Heating and Hot Water Energy Demand - Annual Profile")
plt.xlabel("Month")
plt.ylabel("Energy Use (kWh)")
plt.grid(True)
plt.legend()

# Set x-axis labels as abbreviated month names
plt.gca().set_xticks(np.arange(len(scaled_monthly_avg.index)))
plt.gca().set_xticklabels(scaled_monthly_avg.index)

# Set the y-axis limits (optional customization)
plt.ylim(30000, scaled_monthly_avg.max() + 10000)

# Display the plot
plt.show()

# Verify that the total energy across the year sums to 526960 kWh
print(f"Total annual energy (scaled, monthly): {scaled_monthly_avg.sum()} kWh")

# Plot average monthly energy usage with standard deviation error bars
plt.figure(figsize=(12, 6))
# plt.errorbar(scaled_monthly_avg.index, scaled_monthly_avg, yerr=scaled_monthly_std, fmt='o-', capsize=5, label="Average Monthly with Std Dev")
x = [i*2.6E6 for i in range(13)]
fitted = [1.8E-10*(2.6E6*6-i)**2+53056 for i in x]
print(min(scaled_monthly_avg/732E-3))
plt.plot(x[:-1], scaled_monthly_avg/732E-3, label='Annual month-to-month load profile')
# plt.plot(x, fitted, label=r'$Q_b = (1.6\text{E}-10)*(2.6\text{E}6*6-t)^2+46225$')
plt.plot(x, fitted, label=r'$Q_b = (1.8\text{E}-10)*(2.6\text{E}6*6-t)^2+53056$')
plt.xlabel("Time [s]")
plt.ylabel(r"$Q_b$ [W]")
plt.grid(True)
plt.legend()
plt.show()

# Print MSE for curve
diffs = np.array([((scaled_monthly_avg.values[i]/732E-3)-fitted[i])**2 for i in range(12)])
mse = np.mean(diffs)
spread = max(scaled_monthly_avg/732E-3) - min(scaled_monthly_avg/732E-3)
print("MSE:", mse)
print("Range squared:", spread**2)
print(r"MSE as % of range:", (mse/spread**2)*100, '%')