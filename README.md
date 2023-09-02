# Hydroponic Vegetable, Garden, and Chemical Manager

## Introduction

`Veg Crib (r)` is a program that allows the user to manage a vegetable garden by creating and managing plants, container environments, and chemicals.

## Class Definitions
The following classes are defined within the code and can be interacted with via CLI or Graphical User Interface:

### PlantContainer
> This class represents a container for a plant, which is initialized with a plant object, container dimensions in the format 'rxd' (radius x depth), and an environment object.

### ContainerEnvironment
> This class represents a container environment in which plants can be placed. It is initialized with a name and a dictionary containing the dimensions of the environment in the format 'row_count' and 'column_count'

### Plant
> This class represents a plant and it is initialized with a name and a dictionary of chemical assignments for different weeks.

### Chemical
> This class represents a chemical and it is initialized with a name and a description.

## Global Variables

### plant_counter
> This variable holds the number of plants that have been created.

### global_indent
> This variable holds the indentation level for the print statements.

### args
> This variable holds the command-line arguments passed to the program.

### run_root_path
> This variable holds the path to the file that the program is currently running from.

### logfile_path
> This variable holds the path to the file where the program logs are stored.

### completed_dict
> This variable holds the dictionary containing the last updated time, chemicals, plants, container environments, and completed plant IDs.

### chemicals
> This variable holds a dictionary containing the chemical names and their descriptions.

## Functions

### parse_args()
> This function parses the command-line arguments passed to the program.

### initialize_logfile()
> This function initializes the logfile by creating an empty file if it does not exist and loading the contents of the file if it does exist.

### record_complete()
> This function records the completion of the program by saving the state of all class instances to the logfile.

### print_chemical_descriptions()
> This function prints the description of all chemicals.

### get_chemical_set_for_week()
> This function returns the set of chemicals to be used for a specific week.

## Running the code

To run the code, you will need to have python3 installed on your machine. 
You can run the code by navigating to the directory where the code is saved and running the command `python3 veg_crib_manage.py` 
You can pass command-line arguments to the program to control its behavior.
You can pass `-w` or `--week` followed by a week number to print the details of that week.
You can pass `-d` or `--describe` to print the details of all the chemicals.

Please make sure that the code is compatible with your python version and that you have all the required packages before running the code

Please also make sure to review the code again and make sure that you understand how it works, as well as its limitations and assumptions, before attempting to use it in any real-world scenario.

## Full Usage
```shell
usage: veg_crib_manage.py [-h] [-w WEEK] [-d]

options:
  -h, --help            show this help message and exit
  -w WEEK, --week WEEK  Print Details of current week.
  -d, --describe        Print Details of chemicals purposes
```