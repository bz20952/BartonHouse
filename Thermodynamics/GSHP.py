import math
import scipy
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import rcParams
import numpy as np

seconds_in_year = 3600*24*365.2

class GSHP:

    """
    Model a single borehole. Assess potential heat output.
    """

    def __init__(
            self,
            num_boreholes: int,
            depth: float, 
            radius: float, 
            soil_density: float,
            soil_heat_capacity: float,
            soil_thermal_conductivity: float,
            grout_density: float,
            grout_heat_capacity: float,
            grout_thermal_conductivity: float,
        ) -> None:
        self.num_boreholes = num_boreholes
        self.L = depth
        self.r = radius
        self.k_s = soil_thermal_conductivity
        self.alpha_s = GSHP.calc_thermal_diffusivity(self.k_s, soil_density, soil_heat_capacity)
        self.k_g = grout_thermal_conductivity
        self.alpha_g = GSHP.calc_thermal_diffusivity(self.k_g, grout_density, grout_heat_capacity)
        self.pipe_thickness = self.r/4
        self.R_p = self.calc_conduction_resistance(self.pipe_thickness, 54)
        self.R_g = self.calc_conduction_resistance(self.r*2-2*self.pipe_thickness, self.k_g)
        self.R_con = self.calc_convection_resistance(self.pipe_thickness, 500)

    def plot(self, system_props: pd.DataFrame, y1: list[str], y2: list[str]):

        """Plot a given property of the system over time."""

        rcParams['font.size'] = 18

        fig, ax1 = plt.subplots()

        ax1.set_xlabel('Month')
        ax1.set_ylabel('Power [W]')
        for prop in y1:
            ax1.plot(system_props['Time (s)']/(seconds_in_year/12), [i for i in system_props[prop]], linestyle='--', label=prop[:-3].replace('temp', ''))
        ax1.tick_params(axis='y')

        if y2:
            ax2 = ax1.twinx()
            ax2.set_xlabel('Month')
            ax2.set_ylabel('COP')
            for prop in y2:
                ax2.plot(system_props['Time (s)']/(seconds_in_year/12), system_props[prop], color='g', label=prop)
            ax2.tick_params(axis='y')

        fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.87))
        plt.grid(True)
        plt.show()

    def get_building_load(t):

        """Calc building load at time t where t is seconds since 00:00 on 01/01."""

        years_passed = t//seconds_in_year
        t -= seconds_in_year*years_passed

        Q_b = 1.8E-10*(2.6E6*6-t)**2+53056

        return Q_b

    def model_single_bh(self, t_n: float, time_step: float, T_ground: float, is_heating: bool):

        '''
        1. Building's temporal distribution of heating/cooling load
        2. Calculate instantaneous borehole load for a single borehole -> OUTPUT borehole temporal distribution of heating/cooling load
        3. Calculate borehole soil interface temperature
        3.1 Linear source equation (Temp distribution around a source)
        4. Calculate water temperature at borehole outlet
        4.1 Calculate total heat resistance 
        5. Calculate heat pump COP
        5.1 Get COP from temp vs COP curve
        6. RETURN TO STEP 2
        '''

        # Define initial conditions
        Q_history = [0]
        cop = GSHP.graph_cop(T_w = self.get_outlet_water_temperature(T_ground, 0))

        n = math.floor(t_n/time_step)
        system_props = pd.DataFrame(columns=['Time (s)', 'Building load per BH (W)', 'Interface temp (K)', 'Borehole outlet/heat pump inlet temp (K)', 'COP', 'Ground load per BH (W)', 'Elec per BH (W)'])

        for i in range(n+1):
            t = i*time_step
            Q_b = GSHP.get_building_load(t)/self.num_boreholes
            Q_g = self.get_instantaneous_ground_load(Q_b, cop, is_heating)
            Q_history.append(Q_g)
            Q_hp = GSHP.get_elec_consumption(cop, Q_b)
            T_interface = T_ground + self.get_change_in_temperature(self.r, time_step, i, Q_history, self.k_g, self.alpha_g)
            T_w = self.get_outlet_water_temperature(T_interface, Q_g)
            system_props.loc[len(system_props)] = [t, Q_b, T_interface, T_w, cop, Q_g, Q_hp]
            cop = GSHP.graph_cop(T_w)
            
        print(system_props)
        return system_props

    def get_instantaneous_ground_load(self, Q_b: float, cop: float, is_heating: bool):

        """
        Returns heat absorbed from ground.
        
        Q_b = building load (W)
        cop = coefficient of performance
        """

        if is_heating:
            return (Q_b*(cop-1))/cop
        else:
            return (Q_b*(cop+1))/cop
        
    def get_change_in_temperature(self, r: float, time_step: float, n: int, Q: list, k: float, alpha: float):

        """
        Returns change in ground temperature at given position and time.
        """

        delta_T = 0
        for j in range(1, n+1):
            delta_T += ((Q[j]-Q[j-1])/(4*math.pi*k*self.L))*scipy.special.expi((r**2)/(4*alpha*(time_step*n-time_step*(j-1))))
       
        return delta_T
    
    def get_outlet_water_temperature(self, T_interface: float, Q_g: float):

        """Use formula from paper to calc outlet temperature."""

        R_tot = self.R_con + self.R_p + self.R_g

        T_w = T_interface - Q_g*R_tot

        return T_w

    def get_elec_consumption(cop: float, Q_b: float) -> float:

        return Q_b/cop
    
    def graph_cop(T_w: float) -> float:

        m = 1.3/15
        c = 3.75

        T_w -= 273

        return m*T_w + c

    def get_drilling_cost(self) -> float:

        """Returns drilling costs based on Dom's estimations."""

        print('Min: £', 40*self.L)
        print('Avg: £', 50*self.L)
        print('Max: £', 60*self.L)

        return 40*self.L, 50*self.L, 60*self.L
    
    def calc_thermal_diffusivity(k, rho, c_p):

        alpha = k/(rho*c_p)

        return alpha
    
    def calc_conduction_resistance(self, thickness, k):

        R = thickness/(k*(2*math.pi*self.r*self.L))

        return R
    
    def calc_convection_resistance(self, thickness, h):

        R = thickness/(h*(2*math.pi*self.r*self.L))

        return R

    def optimise_borehole_config(self, max_heat_per_metre: float, T_ground: float, time_step: float, is_heating: bool, fd: bool, epsilon: float = 1E-5):

        """Returns optimal borehole spacing. Assumes the ground gains zero solar energy over the time period, t_n."""

        Q_max = -GSHP.get_building_load(t=0)
        cop = 3.5
        Q_g_max = self.get_instantaneous_ground_load(Q_max, cop, is_heating)
        Q_allowable_per_bh = -max_heat_per_metre*self.L
        safety_factor = 1.5
        num_boreholes = math.ceil((Q_g_max/Q_allowable_per_bh)*safety_factor)
        print('Num boreholes:', num_boreholes)

        t_n = seconds_in_year
        n = int(t_n//time_step)

        mesh_size = 0.1

        if fd:
            Fo = self.alpha_s*(time_step/mesh_size**2)  # Fourier number
            if Fo > 0.5:
                print(f'WARNING: Fourier number of {Fo} will make this solution unstable.')

        t_init = 0
        radii = [i*mesh_size for i in range(100)]
        T_init = [288]*len(radii)
        temporal_temp_dist = [T_init]
        Q_history = [0]
        cop = GSHP.graph_cop(self.get_outlet_water_temperature(T_ground, 0))
        for i in range(n+1):
            t = i*time_step
            Q_b = GSHP.get_building_load(t_init+t)/num_boreholes  # Negative indicates heat leaving ground
            Q_g = self.get_instantaneous_ground_load(Q_b, cop, is_heating)   # Heat extracted from ground
            if abs(Q_g) > abs(Q_allowable_per_bh):
                print('WARNING: Ground load has exceeded theoretical maximum.')
            Q_history.append(Q_g)
            T_interface = self.get_change_in_temperature(self.r, time_step, i, Q_history, self.k_g, self.alpha_g)
            T_w = self.get_outlet_water_temperature(T_interface, Q_g)
            cop = GSHP.graph_cop(T_w)

            # Calculate ground temp at varying radii
            T_new = np.zeros(len(T_init))
            if fd:
                q_g = Q_g/(2*math.pi*self.r*self.L)  # Heat flux per unit surface area
                T_new[0] = 0.25*(2*T_init[0] + T_init[1] + 2*q_g*mesh_size/self.k_s)  # Known heat flux BC
                T_new[-1] = T_ground
                for j in range(1, len(T_init)-1):
                    T_new[j] = Fo*(T_init[j+1]+T_init[j-1]) + (1-2*Fo)*T_init[j]
            else:
                for j, r in enumerate(radii):
                    T_new[j] = T_ground + self.get_change_in_temperature(r, time_step, i, Q_history, self.k_s, self.alpha_s)

            temporal_temp_dist.append(T_new)
            T_init = T_new

        # # Plot the final ground temp at varying radii
        # plt.scatter(radii, temporal_temp_dist[-1])
        # # for p in range(len(temporal_temp_dist)):
        # #     plt.plot(radii, temporal_temp_dist[p])
        # plt.axhline(T_ground, color='r', linestyle='--')
        # plt.xlabel('Radial distance from BH [m]')
        # plt.ylabel('Ground temp [K]')
        # plt.title(f't={t_n}s')
        # plt.show()

        # Find critical radius by radius at which diff between ground temp and undisturbed ground temp is less than epsilon
        min_loss = 1E2
        r_crit = None
        for index, temp in enumerate(temporal_temp_dist[-1]):
            loss = abs(temp - T_ground)
            if loss < min_loss:
                min_loss = loss
                r_crit = radii[index]

        print('Critical radius: ', r_crit)

        return r_crit, num_boreholes