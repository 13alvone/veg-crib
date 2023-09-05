import datetime
import sqlite3
import jsonpickle
import copy

next_plant_id = 1  # Initialize the ID counter
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


def generate_new_id():
    global next_plant_id  # Declare the variable as global so we can modify it
    new_id = next_plant_id  # Use the current value of next_plant_id as the new ID
    next_plant_id += 1  # Increment the counter for the next ID
    return new_id


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
    def __init__(self, name, harvest_type, environment, grow_type, thc, cbd, birth_date,
             harvest_date, bottle_date, low_cure_date, mid_cure_date, high_cure_date, age_in_weeks, 
             _container_rxd='3x5', id=None):
        self.id = id if id else generate_new_id()  # Assuming you have a function to generate new IDs
        self.name = name
        self.harvest_type = harvest_type
        self.environment = environment
        self.grow_type = grow_type
        self.thc = thc
        self.cbd = cbd
        self.birth_date = birth_date
        self.harvest_date = harvest_date
        self.bottle_date = bottle_date
        self.low_cure_date = low_cure_date
        self.mid_cure_date = mid_cure_date
        self.high_cure_date = high_cure_date
        self.age_in_weeks = age_in_weeks
        default_container_rxd = "3x5"  # Default container dimensions
        self.container = PlantContainer(self, default_container_rxd, self.environment)
        self.fully_complete = True

        # if not self.environment.add_container(self):
        #     self.fully_complete = False
        #     return

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
        self.name = "_".join([x.capitalize() for x in _environment_name.strip().split(" ")])
        self.max_size = _dimensions['row_count'] * _dimensions['column_count']

    def create_grid_matrix(self):
        output_grid = {}
        rows = int(self.dimensions['row_count'])
        columns = int(self.dimensions['column_count'])
        for row in range(1, rows + 1):
            for column in range(1, columns + 1):
                output_grid[f'{row}x{column}'] = None
        return output_grid

    def add_container(self, _plant):
        for position in self.grid:
            if not self.grid[position]:
                self.grid[position] = _plant
                return self
        return False

    def remove_container(self, plant_id):
        for position, container in self.grid.items():
            if container:
                if container.id == plant_id:
                    self.grid[position] = None
                    return True
        return False

    def move_container(self, container, new_position):
        if new_position not in self.grid:
            return False  # Invalid position
        if self.grid[new_position] is not None:
            return False  # Position already occupied
        for position, existing_container in self.grid.items():
            if existing_container and existing_container.id == container.id:
                self.grid[position] = None  # Remove from old position
                self.grid[new_position] = container  # Place in new position
                return True
        return False  # Container not found

    def is_grid_empty(self):  # Return True if Empty, False Else
        return all(value is None for value in self.grid.values())


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

            if row[2]:
                try:
                    self.completed_dict['plants'] = jsonpickle.decode(row[2])
                except Exception as e:
                    print(f"Failed to decode plants from database: {e}")
            else:
                print("row[2] is empty or None")

            self.completed_dict['container_environments'] = jsonpickle.decode(row[3])
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def add_plant(self, plant):
        self.completed_dict['plants'][plant.id] = plant
        plant.environment.add_container(plant)
        self.update_database()

    def delete_plant(self, plant_id):
        plant = self.completed_dict['plants'].get(plant_id)
        if plant_id in self.completed_dict['plants']:
            del self.completed_dict['plants'][plant_id]
            plant[plant_id].environment.remove_container(plant)
            self.update_database()
            return True
        return False

    def delete_container_environment(self, container_name):
        container_env = self.completed_dict['container_environments'].get(container_name, None)
        if container_env:
            # Check if all grid positions are empty (None)
            if container_env.is_grid_empty():
                del self.completed_dict['container_environments'][container_name]
                self.update_database()
                return True
            else:
                print("Cannot delete environment: Grid is not empty. Please move or delete plant(s) first.")
                return False
        return False

    def move_plant(self, plant_id, new_container_env_name):
        plant = self.completed_dict['plants'].get(plant_id)
        dest_container_environment = self.completed_dict['container_environments'].get(new_container_env_name)
        src_container_environment = self.completed_dict['container_environments'].get(plant.environment.name.lower())
        if plant and dest_container_environment:
            # Remove the plant's container from the current environment's grid
            if src_container_environment.remove_container(plant.id):
                self.update_database()
                # Try to add the plant's container to the new environment's grid
                if dest_container_environment.add_container(plant):
                    self.update_database()
                    # Update the plant's environment
                    plant.update_environment(dest_container_environment)
                    self.update_database()
                    return True
                else:
                    # If adding to the new environment fails, add it back to the old environment
                    plant.environment.add_container(plant.container)
                    self.update_database()
                    return False
            else:
                return False  # Failed to remove from old environment
        return False  # Plant or new environment not found

    def get_available_containers(self):
        return list(self.completed_dict['container_environments'].keys())
