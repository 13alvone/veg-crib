import os
import re
import json
import time
import datetime
from pathlib import Path

import jsonpickle
import pandas as pd

next_plant_id = 0
completed_dict = {
    'last_updated': 'Unknown',
    'chemicals': {},
    'plants': {},
    'container_environments': {},
}
chemicals = {
    'canopy_boost': {
        'description':
            "Increases plant metabolism and photosynthesis;\nImproves root growth and water uptake;\n"
            "Enhances plant responses to transition shock;\nBoosts plant's resistance to stressors",
        'week_ml_assignments': {
            '0': 0, '1': 5, '2': 5, '3': 10, '4': 15, '5': 15, '6': 20, '7': 20, '8': 20,
            '9': 20, '10': 20, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 0
        }
    },
    'root_boost': {
        'description':
            "Improves root growth and increases root mass;\nEnhances water and nutrient uptake;\n"
            "Actively stabilizes soil chemistry and buffers pH;\nStimulates beneficial bacterial and fungal growth",
        'week_ml_assignments': {
            '0': 0, '1': 1, '2': 1, '3': 1, '4': 1, '5': 1, '6': 1, '7': 1, '8': 1,
            '9': 1, '10': 1, '11': 1, '12': 0, '13': 0, '14': 0, '15': 0, '16': 0
        }
    },
    'n_primer': {
        'description':
            "Stimulates lush green canopy growth;\nReduces nitrogen burns and soil leaching;\n"
            "Improves microbial and fungal diversity;\nEnhances plant vigor and strength",
        'week_ml_assignments': {
            '0': 0, '1': 1, '2': 1, '3': 2, '4': 2, '5': 2, '6': 2, '7': 2, '8': 2,
            '9': 2, '10': 2, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0, '16': 0
        }
    },
    'organic_calmag_oac': {
        'description':
            "Thickens stems, leaves, and root systems;\nPromotes strong, vigorous vegetative growth;\n"
            "Increases trichome development in flowers;\nAmplifies soil health and sustains plant health",
        'week_ml_assignments': {
            '0': 0, '1': 0, '2': 1, '3': 1, '4': 1, '5': 1, '6': 1, '7': 1, '8': 1,
            '9': 1, '10': 1, '11': 1, '12': 1, '13': 1, '14': 1, '15': 1, '16': 1
        }
    },
    'bloom': {
        'description':
            "Maximizes flower growth and total yield;\nReduces transition stress and shock;\n"
            "Improves root activity and increases water uptake;\nEnhances early flower growth and terpene production",
        'week_ml_assignments': {
            '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0,
            '9': 1, '10': 1, '11': 2, '12': 2, '13': 2, '14': 1, '15': 1, '16': 0
        }
    },
    'signal': {
        'description':
            "Increases flower density and hardness;\nEnhances terpene synthesis;\n"
            "Actively flushes salts away from root hairs",
        'week_ml_assignments': {
            '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0,
            '9': 0, '10': 1, '11': 1, '12': 1, '13': 1, '14': 2, '15': 2, '16': 2
        }
    },
    'base_ab': {
        'description':
            "Ideal during vegetative and flowering period;\nExcellent compatibility with all grow mediums;\n"
            "Prevents salt buildup in irrigation systems;\nContains the full spectrum of macro and micro nutrients",
        'week_ml_assignments': {
            '0': 0, '1': 3, '2': 3, '3': 4, '4': 4, '5': 4, '6': 4, '7': 4, '8': 5,
            '9': 5, '10': 6, '11': 6, '12': 6, '13': 6, '14': 5, '15': 4, '16': 4
        }
    },
    'silica_gold': {
        'description':
            "Increases cell wall strength and stem thickness;\nTightens internodal spacing in vegetative growth;\n"
            "Enhances flower density and hardness;\nRelieves environmental stress",
        'week_ml_assignments': {
            '0': 0, '1': 1, '2': 1, '3': 1, '4': 1, '5': 1, '6': 1, '7': 2, '8': 2,
            '9': 2, '10': 2, '11': 2, '12': 2, '13': 2, '14': 1, '15': 1, '16': 0
        }
    },
}


class Chemical:
    def __init__(self, chemical_name):
        global chemicals
        valid_chemicals = chemicals.keys()
        valid_chemicals_readable = '\n'.join(valid_chemicals)
        self.name = chemical_name.lower()
        while self.name not in valid_chemicals:
            msg = f'[!] Veg Crib (r) requires one of the following chemical names be entered' \
                  f'exactly as it in the list below;\n{valid_chemicals_readable}\n\n'
            self.name = input(msg).lower()
        self.description = chemicals[self.name]['description']
        self.week_ml_assignments = chemicals[self.name]['week_ml_assignments']

    def get_description(self, chemical_name):
        global chemicals
        valid_chemicals = chemicals.keys()
        while chemical_name.lower() not in valid_chemicals:
            valid_chemicals_readable = '\n'.join(valid_chemicals)
            msg = f'[!] Veg Crib (r) requires one of the following chemical names be entered' \
                  f'exactly as it in the list below:\n{valid_chemicals_readable}\n'
            chemical_name = input(msg)
        return self.description


class Plant:
    def __init__(self, _name, _harvest_type, _environment, _id, _grow_type='standard', _thc_percentage=0, _cure='',
                 _cbd_percentage=0, _birth_date=datetime.date.today(), _container_rxd='12x14'):
        self.id = _id
        self.name = f'{_name}'  # User-Defined plant name
        self.harvest_type = _harvest_type  # Sativa, Indica, Hybrid
        self.environment = _environment  # Plant's current container environment
        self.grow_type = _grow_type  # Standard, Auto, or Unknown
        self.thc_percentage = _thc_percentage  # THC Percentage
        self.cbd_percentage = _cbd_percentage  # CBD Percentage
        self.birth_date = f'{_birth_date}'  # Seed Plant Date
        self.harvest_date = f'{(_birth_date + datetime.timedelta(days=112)).strftime("%x")}'
        self.bottle_date = f'{(_birth_date + datetime.timedelta(days=119)).strftime("%x")}'
        self.low_cure_date = f'{(_birth_date + datetime.timedelta(days=140)).strftime("%x")}'  # Decent Results
        self.mid_cure_date = f'{(_birth_date + datetime.timedelta(days=168)).strftime("%x")}'  # Better Results
        self.high_cure_date = f'{(_birth_date + datetime.timedelta(days=196)).strftime("%x")}'  # Best Results
        self.cure_date = self.low_cure_date  # Actual cure date which defaults to low
        self.age_in_weeks = self.calculate_week_count()  # Week count compared to today
        self.container = PlantContainer(self, _container_rxd, self.environment)  # Create New Container for Plant
        self.fully_complete = True

        # Update cure date if provided
        if _cure != '':
            self.cure_date = _cure

        # Add the new container holding the plant to the virtual environment set
        if not self.environment.add_container(self.container):
            print(f'[!] Container Full: Unable to seat container for plant `{self.container.plant.name}`')
            self.fully_complete = False
            return

    def update_plant_cure(self, _new_cure):
        self.cure_date = f'{_new_cure}'

    def calculate_week_count(self):
        today = datetime.date.today()
        return abs(today - datetime.datetime.strptime(self.birth_date, '%Y-%m-%d').date()).days // 7

    def update_environment(self, _environment_obj):
        self.environment = _environment_obj


class PlantContainer:
    def __init__(self, _plant, _container_rxd, _environment):
        self.plant = _plant
        self.dimensions = _container_rxd
        self.id = self.plant.id
        self.environment = _environment
        while not re.match(r'\d+x\d+', self.dimensions):
            msg = f'[!] Plant containers require both a radius and depth formatted as: `rxd`.'
            self.dimensions = input(msg)


class ContainerEnvironment:
    def __init__(self, _environment_name, _dimensions):  # All initialized environments assume square or rectangle
        self.dimensions = _dimensions
        self.grid = self.create_grid_matrix()
        self.name = _environment_name
        self.max_size = _dimensions['row_count'] * _dimensions['column_count']

        while not isinstance(self.dimensions, dict):
            msg = f'[!] Container environments must be instantiated as a dictionary object that contains both ' \
                  f'`row_count` and `column_count` keys with corresponding integer values.'
            self.dimensions = input(msg)

    def create_grid_matrix(self):
        output_grid = {}
        rows = int(self.dimensions['row_count'])
        columns = int(self.dimensions['column_count'])
        if rows != 0 and columns != 0:
            for row in range(1, rows + 1):
                for column in range(1, columns + 1):
                    output_grid[f'{row}x{column}'] = None
        return output_grid

    def add_container(self, _container_obj):
        for position in self.grid:
            if not self.grid[position]:
                self.grid[position] = _container_obj
                return True
        return False

    def remove_container(self, _container_obj):
        for position in self.grid:
            if self.grid[position]:
                if self.grid[position].plant.name == _container_obj.plant.name:
                    self.grid[position] = None
                    return True
        return False


class Backend:
    def __init__(self, run_test_model=False):
        self.run_root_path = f"{'/'.join(os.path.abspath(__file__).split('/')[:-1])}"
        self.logfile_root = f"{self.run_root_path}/logs"
        self.logfile_path = f'{Path(self.logfile_root).absolute()}/{int(time.time())}_veg_crib.json'
        self.completed_dict = completed_dict
        self.initialize_logfile()
        # self.record_complete()
        self.space = " "
        self.tab = 4 * self.space

        if run_test_model:
            self.run_example_full_model()

        self.df_plant = self.create_plant_df()
        self.df_chemical = self.create_chemical_df()

    @staticmethod
    def is_utf8(_plant_name):
        try:
            _plant_name.decode('utf-8')
            return True
        except UnicodeError:
            return False

    @staticmethod
    def extract_epoch(filename: str):
        return int(filename.split("_")[0])

    @staticmethod
    def get_recent_monday_datetime():
        today = datetime.date.today()
        return today - datetime.timedelta(days=today.weekday())

    def print_current_plant_stats(self):
        print_counter = 1
        for plant_id, plant_obj in self.completed_dict['plants'].items():
            msg = f'[{print_counter}] PLANT: `{plant_obj.name}`\n' \
                  f'{self.tab}{vars(plant_obj)}\n\n'

            print(msg)
            print_counter += 1

    def create_chemical_df(self):
        global chemicals
        df_row_count = 17
        chemical_keys = self.get_chemical_set_for_week(0).keys()
        df = pd.DataFrame(index=[f'{x}' for x in range(1, df_row_count)], columns=chemical_keys)

        for chemical_name, chemical_info in chemicals.items():
            for week_number, ml_value in chemical_info['week_ml_assignments'].items():
                df.at[week_number, chemical_name] = f'{ml_value}'

        df.drop('0', axis=0, inplace=True)

        return df

    def plant_count(self):
        global next_plant_id
        current_plant_id = len(self.completed_dict['plants'].keys())
        next_plant_id = current_plant_id + 1
        return current_plant_id

    @staticmethod
    def print_chemical_descriptions():
        global chemicals
        for chemical_name, chemical_data in chemicals.items():
            print(f'[+] `{chemical_name}`\n{chemical_data["description"]}\n')

    @staticmethod
    def get_chemical_set_for_week(_week):
        global chemicals
        output = {
            'canopy_boost': chemicals['canopy_boost']['week_ml_assignments'][f'{_week}'],
            'root_boost': chemicals['root_boost']['week_ml_assignments'][f'{_week}'],
            'n_primer': chemicals['n_primer']['week_ml_assignments'][f'{_week}'],
            'organic_calmag_oac': chemicals['organic_calmag_oac']['week_ml_assignments'][f'{_week}'],
            'bloom': chemicals['bloom']['week_ml_assignments'][f'{_week}'],
            'signal': chemicals['signal']['week_ml_assignments'][f'{_week}'],
            'base_ab': chemicals['base_ab']['week_ml_assignments'][f'{_week}'],
            'silica_gold': chemicals['silica_gold']['week_ml_assignments'][f'{_week}']
        }
        return output

    def initialize_logfile(self):
        global completed_dict
        new_file_path = f'{self.logfile_root}/{int(time.time())}_veg_crib.json'  # New log filename
        files = []  # Shell for storing file paths

        for filename in os.listdir(self.logfile_root):
            if filename.endswith(".json") and re.search("^([0-9]+)_", filename):
                files.append(filename)

        files.sort(key=self.extract_epoch, reverse=True)

        test_length = len(files)
        if 1 <= test_length <= 4:
            self.logfile_path = os.path.join(self.logfile_root, files[0])

        elif test_length > 4:
            self.logfile_path = os.path.join(self.logfile_root, files[0])
            for i, file in enumerate(files[4:]):
                if file.lower() != self.logfile_path.split('/')[-1].lower():
                    old_log_file = os.path.join(self.logfile_root, file)
                    try:
                        os.remove(old_log_file)
                        print(f'[+] Successfully removed old log file `{old_log_file}`')
                    except Exception as e:
                        print(f'[!] Failed to removed old log file `{old_log_file}`\n\tError: {e}\n')

        elif not files:
            self.logfile_path = new_file_path
            with open(os.path.join(self.logfile_root, new_file_path), 'w') as file_in:
                json.dump(completed_dict, file_in)
            file_in.close()
            files.append(new_file_path)
            return

        if os.path.isfile(self.logfile_path) and os.stat(self.logfile_path).st_size != 0:
            self.completed_dict = json.load(open(self.logfile_path, 'r'))
            self.thaw_custom_objects()

        self.logfile_path = new_file_path

    def thaw_custom_objects(self):
        for domain, domain_dict in self.completed_dict.items():
            if domain != 'last_updated':
                for key, json_frozen_custom_object in domain_dict.items():
                    domain_dict[key] = jsonpickle.decode(json_frozen_custom_object)

    def freeze_custom_objects(self):
        for domain, domain_dict in self.completed_dict.items():
            if domain != 'last_updated':
                for key, custom_object in domain_dict.items():
                    domain_dict[key] = jsonpickle.encode(custom_object)

    def record_complete(self):
        self.completed_dict['last_updated'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.freeze_custom_objects()
        with open(self.logfile_path, "w") as out_file:
            try:
                json.dump(self.completed_dict, out_file)
            except Exception as e:
                print(f'[!] Error writing json file:\n\t Error:\n\t`{e}`')
        out_file.close()
        self.thaw_custom_objects()

    def run_example_full_model(self, print_plants=False):
        # Define and initialize an empty container environment. This is a collection of plants + respective containers.
        test_environments = {
            'yellow_tub': ContainerEnvironment('yellow_tub', {'row_count': 2, 'column_count': 3}),
            'three_bucket': ContainerEnvironment('3_bucket', {'row_count': 1, 'column_count': 3}),
            'starter_tub': ContainerEnvironment('starter_tub', {'row_count': 2, 'column_count': 3}),
            'tent': ContainerEnvironment('tent', {'row_count': 2, 'column_count': 3})
        }

        # Define plant containers and which plant objects will be placed within them, including plant details.
        test_plants = {
            'afgooey':
                Plant('afgooey', 'hybrid', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2022, 12, 10),
                      _grow_type='auto',
                      _thc_percentage=28,
                      _container_rxd='4x3'),
            'white_widow':
                Plant('white_widow', 'indica', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2022, 12, 10),
                      _grow_type='standard',
                      _thc_percentage=19,
                      _container_rxd='4x3'),
            'banana_cush':
                Plant('banana_cush', 'hybrid', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2022, 12, 10),
                      _grow_type='standard',
                      _thc_percentage=25,
                      _container_rxd='4x3'),
            'blueberry_cbd':
                Plant('blueberry_cbd', 'cbd', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2022, 12, 10),
                      _grow_type='auto',
                      _cbd_percentage=7,
                      _container_rxd='4x3'),
            'walk_on_smol':
                Plant('walk_on_smol', 'indica', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2022, 12, 10),
                      _grow_type='unknown',
                      _thc_percentage=-1,
                      _container_rxd='4x3'),
            'afgooey2':
                Plant('afgooey2', 'hybrid', test_environments['tent'], self.plant_count(),
                      _birth_date=datetime.date(2023, 1, 11),
                      _grow_type='auto',
                      _thc_percentage=28,
                      _container_rxd='4x3'),
            'white_widow2':
                Plant('white_widow2', 'indica', test_environments['yellow_tub'], self.plant_count(),
                      _birth_date=datetime.date(2023, 1, 11),
                      _grow_type='standard',
                      _thc_percentage=19),
            'trained_unknown':
                Plant('trained_unknown', 'unknown', test_environments['yellow_tub'], self.plant_count(),
                      _birth_date=datetime.date(2022, 8, 1),
                      _grow_type='standard',
                      _thc_percentage=-1),
        }

        for environment_name, environment_obj in test_environments.items():
            self.completed_dict['container_environments'][environment_name] = environment_obj

        for plant_name, plant_obj in test_plants.items():
            self.completed_dict['plants'][plant_name] = plant_obj

        for chemical_name, _ in chemicals.items():
            self.completed_dict['chemicals'][chemical_name] = Chemical(chemical_name)

        # Record the completed events to file.
        self.record_complete()

        # Print all current plant data to screen.
        if print_plants:
            self.print_current_plant_stats()

    def create_plant_df(self):

        plant_keys = list(self.completed_dict['plants'].keys())
        _columns = ['name', 'harvest_type', 'environment', 'grow_type', 'thc_percentage', 'cbd_percentage',
                    'birth_date', 'harvest_date', 'bottle_date', 'cure_date', 'low_cure_date', 'mid_cure_date',
                    'high_cure_date', 'age_in_weeks', 'container']

        df = pd.DataFrame(index=plant_keys, columns=_columns)

        for _, plant in self.completed_dict['plants'].items():
            _plant = vars(plant)
            for _column in _columns:
                if _column == 'environment':
                    df.at[_plant['name'], _column] = f'{_plant[_column].name}'
                elif _column == 'container':
                    df.at[_plant['name'], _column] = f'{_plant[_column].dimensions}'
                elif _column == 'plant_counter':
                    pass
                else:
                    try:
                        df.at[_plant['name'], _column] = f'{_plant[_column]}'
                    except KeyError as e:
                        print(f'[!] Key: `{_column}` missing, but expected: `{e}`')

        return df
