import iapws.iapws97 as steam
import steam_3_pressure_with_reheat as cycle
import numpy as np
import collections
from matplotlib import pyplot as plt
import gas_turbine as gt
import csv


class HeatExchanger:
    def __init__(self, t_c_in, t_c_out, m_h_in, m_c_in, exchanger_type, operating_pressure, t_h_in=0, quality_in=0, quality_out=1):
        self.t = {
            'hot in': t_h_in,
            'cold in': t_c_in,
            'cold out': t_c_out
        }
        self.m = {
            'hot': m_h_in,
            'cold': m_c_in
        }
        self.cp = {
            'hot': 1.004,
            'cold': 2.1
        }
        self.h = {}
        self.operating_pressure = operating_pressure
        self.type = exchanger_type  # determine whether economiser, evaporator or superheater
        self.quality_in = quality_in
        self.quality_out = quality_out

    def set_h_in(self, t_h_in):
        self.t['hot in'] = t_h_in

    def set_condition(self, exchanger_type: str):
        self.type = exchanger_type

    def set_name(self, name: str):
        self.name = name

    def Calculate(self):
        if self.type == 'economiser':
            self.cp['cold'] = 4.2
            self.h['cold in'] = steam._Region1(self.t['cold in'], self.operating_pressure)['h']
            self.h['cold out'] = steam._Region1(self.t['cold out'], self.operating_pressure)['h']
            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        elif self.type == 'superheater':
            self.cp['cold'] = 2.1
            self.h['cold in'] = steam._Region2(self.t['cold in'], self.operating_pressure)['h']
            self.h['cold out'] = steam._Region2(self.t['cold out'], self.operating_pressure)['h']
            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        elif self.type == 'evaporator':  # liquid-vapor mixture then we need to work out enthalpies
            self.h['cold in'] = steam._Region4(self.operating_pressure, self.quality_in)['h']
            self.h['cold out'] = steam._Region4(self.operating_pressure, self.quality_out)['h']
            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        # heat usage
        self.Q = self.m['cold'] * (self.h['cold out'] - self.h['cold in'])

#TODO

class HRSG:
    # an HRSG is assumed to be a chain of heat exchnagers whose outputs feed into the input of the next exchanger in the array
    def __init__(self, exchanger_list=[], inlet_temp=273):
        self.exchangers = exchanger_list
        self.inlet_temp = inlet_temp
        self.outlet_temp = None  # will be worked out using the calculate function
        self.name = ''
        self.calculated = False

    def AddExchanger(self, exchanger: HeatExchanger):  # add exchanger to end of exchnager array
        self.exchangers.append(exchanger)
        self.calculated = False

    def Calculate(self):
        self.heatDuty = 0
        for index, exchanger in enumerate(self.exchangers):
            if index == 0:  # first exchanger will have hot inlet temp of hrsg nlet temp
                exchanger.set_h_in(self.inlet_temp)
            else:   # else inlet temp is outlet of previous exchanger
                inlet = self.exchangers[index-1].t['hot out']
                exchanger.set_h_in(inlet)
            exchanger.Calculate()
            self.heatDuty += exchanger.Q

        #now we've run calculate on each exchanger it's time to get the output temp of the HRSG
        self.outlet_temp = self.exchangers[-1].t['hot out']
        self.calculated = True

    def SaveResults(self, hrsg_filename):
        if not self.calculated:
            print("Unable to save hrsg results as hrsg has not been calculated.\nTry running the Calculate function of the HRSG object")
            return False
        # generate HRSG table
        # HE, FGin, FGout, STEAMin, STEAM,out, Heat Duty
        hrsgsOutputTableRows = [0]*(len(self.exchangers)+1)
        hrsgsOutputTableRows[0] = ["Heat Exchanger Surface", "Flue Gas In [K]", "Flue Gas Out [K]", "Water/Steam In [K]", "Water/Steam Out [K]", "Steam/Water Mass Flow [kg/s]", "Heat Duty [kW]"]

        for index, exchanger in enumerate(self.exchangers):
            name = exchanger.name

            hrsgsOutputTableRows[index+1] = [name, exchanger.t['hot in'], exchanger.t['hot out'], exchanger.t['cold in'], exchanger.t['cold out'], exchanger.m['cold'], exchanger.Q]
        try:
            with open(hrsg_filename+".csv", 'w') as csvfile:
                writer = csv.writer(csvfile)

                writer.writerows(hrsgsOutputTableRows)
                return True
        except IOError:
            print("I/O error")
            return False


    def PlotPinchgraph(self, axes, padding=5, title="pinch plot", difference_threshold=50,unit="c"):
        # check calculated
        if not self.calculated:
            print("Cannot Plot results as HRSG has not been calculated\nPlease run the Calculate method on the HRSG\nE.g. your_hrsg.Calculate()")

        # create x axis
        array_of_exchangers = self.exchangers
        no_of_exchangers = len(array_of_exchangers)
        x = np.zeros((no_of_exchangers, 2))  # array to hold heat limits per exchanger
        labels = []
        # populate array by iterating through exchngers and grabbing heat duties

        for i in range(0, no_of_exchangers):
            exchanger = array_of_exchangers[no_of_exchangers - 1 - i]
            name = exchanger.name

            labels.append(name)
            if i > 0:
                x[i][0] = x[i-1][1]
            x[i][1] = (exchanger.Q) / 1000 + x[i][0]  # Convert to MW

            cold_temps = [exchanger.t['cold in'], exchanger.t['cold out']]
            hot_temps = [exchanger.t['hot out'], exchanger.t['hot in']]
            if unit == "c":  # convert to celcius if unit is specififed as celcius
                hot_temps = np.subtract(hot_temps, 273.15)
                cold_temps = np.subtract(cold_temps, 273.15)

            diff_1 = np.round(hot_temps[0] - cold_temps[0])
            diff_2 = np.round(hot_temps[1] - cold_temps[1])
            if diff_1 < difference_threshold:  # only plot difference on graph if less that 50 K
                axes.text(x[i][0], cold_temps[0] + padding, str(diff_1))
            if diff_2 < difference_threshold:
                axes.text(x[i][1], cold_temps[1] + padding, str(diff_2))
            axes.plot(x[i], cold_temps)

        # add flue gas temperature
        x = [0, self.heatDuty / 1000]  # convert to MW
        T_fg = [array_of_exchangers[-1].t['hot out'], array_of_exchangers[0].t['hot in']]
        if unit == "c":
            T_fg = np.subtract(T_fg, 273.15)  # Another conversion to Celcius

        axes.plot(x, T_fg, linestyle="dashed", color='r')
        labels.append("Fluegas Temperature")
        axes.legend(labels)
        axes.set_xlabel("Heat Consumption [MW]")
        axes.set_ylabel("Temperature [C]" if unit == "c" else "Temperature [K]")
        axes.set_title(title)
