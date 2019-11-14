# HRSG

## Python modeller for triple pressure Steam plant and it's corresponding Heat recovery steam generator (HRSG)
### Dependencies:
- numpy
- matplotlib
- iapws
- CoolProp

Run program from within HRSG file. It's hacked together atm, but will eventually have at least _some_ degree of intuition
Program generates csv files for the steam cycle thermodynamic conditions at each point as well as each component's required work or heat.
Also calculates efficiency of the cycle and well as total energy produced.

Performs HRSG calculations to create a pinch graph of the entire heat exchanger
