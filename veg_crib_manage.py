import os
import re
import json
import time
import datetime
from pathlib import Path
import sqlite3
import jsonpickle

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
        self.name = chemical_name.lower()
        self.description = chemicals[self.name]['description']
        self.week_ml_assignments = chemicals[self.name]['week_ml_assignments']

    def get_description(self, chemical_name):
        global chemicals
        valid_chemicals = chemicals.keys()
        return self.description

class Plant:
    def __init__(self, _name, _harvest_type, _environment, _id, _grow_type='standard', _thc_percentage=0, _cure='',
                 _cbd_percentage=0, _birth_date=datetime.date.today(), _container_rxd='12x14'):
        self.id = _id
        self.name = f'{_name}'
        self.harvest_type = _harvest_type
        self.environment = _environment
        self.grow_type = _grow_type
        self.thc_percentage = _thc_percentage
        self.cbd_percentage = _cbd_percentage
        self.birth_date = f'{_birth_date}'
        self.harvest_date = f'{(_birth_date + datetime.timedelta(days=112)).strftime("%x")}'
        self.bottle_date = f'{(_birth_date + datetime.timedelta(days=119)).strftime("%x")}'
        self.low_cure_date = f'{(_birth_date + datetime.timedelta(days=140)).strftime("%x")}'
        self.mid_cure_date = f'{(_birth_date + datetime.timedelta(days=168)).strftime("%x")}'
        self.high_cure_date = f'{(_birth_date + datetime.timedelta(days=196)).strftime("%x")}'
        self.cure_date = self.low_cure_date
        self.age_in_weeks = self.calculate_week_count()
        self.container = PlantContainer(self, _container_rxd, self.environment)
        self.fully_complete = True

        if _cure != '':
            self.cure_date = _cure

        if not self.environment.add_container(self.container):
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

class ContainerEnvironment:
    def __init__(self, _environment_name, _dimensions):
        self.dimensions = _dimensions
        self.grid = self.create_grid_matrix()
        self.name = _environment_name
        self.max_size = _dimensions['row_count'] * _dimensions['column_count']

    def create_grid_matrix(self):
        output_grid = {}
        rows = int(self.dimensions['row_count'])
        columns = int(self.dimensions['column_count'])
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
    def __init__(self, run_test_model=False, db_path="database/veg_crib.db"):
        self.db_path = db_path
        self.completed_dict = completed_dict
        self.initialize_database()

        if run_test_model:
            self.run_example_full_model()

    def initialize_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS completed_dict
                              (last_updated TEXT, chemicals TEXT, plants TEXT, container_environments TEXT)''')
            cursor.execute("SELECT COUNT(*) FROM completed_dict")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO completed_dict VALUES (?, ?, ?, ?)",
                               (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                jsonpickle.encode(self.completed_dict['chemicals']),
                                jsonpickle.encode(self.completed_dict['plants']),
                                jsonpickle.encode(self.completed_dict['container_environments'])))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def update_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            self.completed_dict['last_updated'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute("UPDATE completed_dict SET last_updated = ?, chemicals = ?, plants = ?, container_environments = ?",
                           (self.completed_dict['last_updated'],
                            jsonpickle.encode(self.completed_dict['chemicals']),
                            jsonpickle.encode(self.completed_dict['plants']),
                            jsonpickle.encode(self.completed_dict['container_environments'])))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def load_from_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM completed_dict")
            row = cursor.fetchone()
            self.completed_dict['chemicals'] = jsonpickle.decode(row[1])
            self.completed_dict['plants'] = jsonpickle.decode(row[2])
            self.completed_dict['container_environments'] = jsonpickle.decode(row[3])
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

