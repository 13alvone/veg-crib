import sqlite3
import jsonpickle
from datetime import datetime, date, timedelta
import time
import smtplib

next_plant_id = 1  # Initialize the ID counter
water_day = datetime.now()  # Initialize with the current date
water_period = 7  # Default to 7 days
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


def calculate_next_water_day():
    """Calculate the next water day based on the water period."""
    global water_day
    water_day += timedelta(days=water_period)


def generate_new_id():
    global next_plant_id  # Declare the variable as global so we can modify it
    new_id = next_plant_id  # Use the current value of next_plant_id as the new ID
    next_plant_id += 1  # Increment the counter for the next ID
    return new_id


def date_to_epoch(date_or_datetime):
    if isinstance(date_or_datetime, float):
        return date_or_datetime
    if not isinstance(date_or_datetime, (date, datetime)):
        raise TypeError("Input must be a date or datetime object.")
    if isinstance(date_or_datetime, date) and not isinstance(date_or_datetime, datetime):
        date_or_datetime = datetime.combine(date_or_datetime, datetime.min.time())

    return int(date_or_datetime.timestamp())


class Chemical:
    def __init__(self, chemical_name):
        global chemicals
        self.name = chemical_name.lower()
        self.description = chemicals[self.name]['description']
        self.week_ml_assignments = chemicals[self.name]['week_ml_assignments']

    def get_description(self):
        return self.description


class Plant:
    global water_day, water_period

    def __init__(self, name, harvest_type, environment, grow_type, thc, cbd, birth_date, harvest_date, bottle_date,
                 low_cure_date, mid_cure_date, high_cure_date, age_in_weeks, _container_rxd='3x5', id=None,
                 harvest_amount=0.0):
        self.id = id if id else generate_new_id()  # Assuming you have a function to generate new IDs
        self.name = name
        self.water_day = datetime.now()  # Initialize with the current date
        self.water_period = 7  # Default to 7 days
        self.harvest_type = harvest_type
        self.environment = environment
        self.grow_type = grow_type  # Auto or Standard
        self.thc = thc
        self.cbd = cbd
        self.birth_date = birth_date
        self.harvest_date = harvest_date
        self.bottle_date = bottle_date
        self.low_cure_date = low_cure_date
        self.mid_cure_date = mid_cure_date
        self.high_cure_date = high_cure_date
        self.age_in_weeks = age_in_weeks
        self.harvest_amount = harvest_amount
        self.container = PlantContainer(self, "3x5", self.environment)
        self.fully_complete = True

    def get_current_week_ml_values(self):
        return self.get_chemical_schedule_for_week(self.calculate_week_count())

    def calculate_next_water_day(self):
        """Calculate the next water day based on the water period."""
        self.water_day += timedelta(days=self.water_period)

    def calculate_week_count(self):
        today = date.today()
        return abs(today - self.birth_date).days // 7

    def update_environment(self, _environment_obj):
        self.environment = _environment_obj

    def get_chemical_schedule_for_week(self, week_number):
        global chemicals
        chemical_schedule = {}

        # Iterate through each chemical to get its week_ml_assignment for the given week
        for chemical_name, chemical_data in chemicals.items():
            week_ml_assignments = chemical_data['week_ml_assignments']
            chemical_schedule[chemical_name] = week_ml_assignments.get(str(week_number), 0)

        return chemical_schedule


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

    def add_container(self, _plant):
        for position in self.grid:
            if not self.grid[position]:
                self.grid[position] = _plant
                return True
        return False

    def remove_container(self, plant_id):
        for position, container in self.grid.items():
            if container:
                if isinstance(container, Plant):
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
    def __init__(self, db_path="database/veg_crib.db"):
        global chemicals
        self.db_path = db_path
        self.completed_dict = completed_dict
        self.initialize_database()
        self.alerts_enabled = True
        self.last_visit_date = None
        self.visit_count = 0
        self.chemicals = chemicals

    def get_chemical_names(self):
        return list(self.chemicals.keys())

    def check_show_alert(self):
        today = datetime.now().date()
        if self.last_visit_date != today:
            self.last_visit_date = today
            self.visit_count = 0
        self.visit_count += 1
        return self.alerts_enabled and self.visit_count <= 2

    def initialize_database(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS chemical_values (event_epoch REAL, plant_id INTEGER, 
                              chemical_name TEXT, ml_value REAL, gallons INTEGER, 
                              PRIMARY KEY (plant_id, chemical_name, event_epoch))''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS plant_history
                              (event_epoch REAL, name TEXT, harvest_type TEXT, environment_name TEXT, 
                              environment_max_size NUMBER, environment_grid TEXT, grow_type TEXT, thc REAL, 
                              cbd REAL, birth_date REAL, harvest_date REAL, bottle_date REAL, low_cure_date REAL, 
                              mid_cure_date REAL, high_cure_date REAL, age_in_weeks NUMBER, container_name TEXT, 
                              container_dimensions TEXT, action TEXT, harvest_amount REAL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS chemical_schedule_override 
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, week_number INTEGER, chemical_name TEXT, 
                              override_value REAL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS completed_dict
                              (last_updated REAL, chemicals TEXT, plants TEXT, container_environments TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS email_credentials
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, 
                              encrypted_app_password TEXT NOT NULL)''')
            cursor.execute("SELECT COUNT(*) FROM completed_dict")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO completed_dict VALUES (?, ?, ?, ?)",
                               (datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                jsonpickle.encode(self.completed_dict['chemicals']),
                                jsonpickle.encode(self.completed_dict['plants']),
                                jsonpickle.encode(self.completed_dict['container_environments'])))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def save_chemical_values(self, plant_id, chemical, ml_value, gallons, event_epoch=time.time()):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            sql_query = '''
                INSERT INTO chemical_values (event_epoch, plant_id, chemical_name, ml_value, gallons)
                VALUES (?, ?, ?, ?, ?)'''
            cursor.execute(sql_query, (event_epoch, plant_id, chemical, ml_value, gallons))
            conn.commit()

        except Exception as e:
            print(f"An error occurred while saving chemical values: {e}")
            conn.rollback()

    def update_database(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            self.completed_dict['last_updated'] = datetime.now() #.strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute('''UPDATE completed_dict SET last_updated = ?, chemicals = ?, plants = ?, 
                           container_environments = ?''',
                           (date_to_epoch(self.completed_dict['last_updated']),
                            jsonpickle.encode(self.completed_dict['chemicals']),
                            jsonpickle.encode(self.completed_dict['plants']),
                            jsonpickle.encode(self.completed_dict['container_environments'])))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def get_chemical_schedule(self):
        conn = None
        chemical_schedule = {}
        try:
            """Fetch the chemical schedule for all weeks, applying any overrides."""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            max_week_number = 52  # Assuming a maximum of 52 weeks in a year

            # Fetch the base chemical schedule for all weeks
            global chemicals  # Access the global chemicals dictionary
            for week_number in range(1, max_week_number + 1):
                chemical_schedule[week_number] = {}
                for chemical_name, chemical_data in chemicals.items():
                    week_ml_assignments = chemical_data['week_ml_assignments']
                    chemical_schedule[week_number][chemical_name] = week_ml_assignments.get(str(week_number), 0)

            # Fetch any overrides
            cursor.execute("SELECT week_number, chemical_name, override_value FROM chemical_schedule_override")
            overrides = cursor.fetchall()

            last_override_week = -1
            for week_number, chemical_name, override_value in overrides:
                if week_number >= last_override_week:
                    # Apply the override to this week and all future weeks
                    for future_week in range(week_number, max_week_number + 1):
                        chemical_schedule[future_week][chemical_name] = override_value
                    last_override_week = week_number

        except sqlite3.Error as e:
            print(f"get_chemical_schedule() Error: {e}")
        finally:
            if conn:
                conn.close()
            return chemical_schedule

    def load_from_database(self):
        conn = None
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

    def record_actual_chemical_usage(self, plant_id, week_number, chemical_name, actual_value):
        """Record the actual chemical usage for a plant."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""INSERT INTO actual_chemical_usage (plant_id, week_number, chemical_name, actual_value)
                VALUES (?, ?, ?, ?)""", (plant_id, week_number, chemical_name, actual_value))

            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def set_chemical_override(self, week_number, chemical_name, override_value):
        """Set the override value for a chemical in a specific week."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO chemical_schedule_override (week_number, chemical_name, override_value)
                VALUES (?, ?, ?)""", (week_number, chemical_name, override_value))

            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def check_email_credentials(self):
        conn = None
        count = 1
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM email_credentials")
            count = cursor.fetchone()[0]
            conn.close()
            return count == 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if conn:
                conn.close()
                return count == 0

    def record_history(self, action='', plant=None, container_environment=None, chemical=None, ingest_epoch=time.time(),
                       delete_plant=False, delete_container=False):
        conn = None
        try:
            ingest_epoch = float(ingest_epoch)
            if not isinstance(ingest_epoch, float):
                print(f'[!] record_history() failed: Incorrect type being passed to it. ({type(ingest_epoch)} passed)')
        except Exception as e:
            print(f'[!] record_history() failed: python details `{e}`')
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if not plant and not container_environment and not chemical:
                return
            elif plant and not container_environment:
                container_environment = plant.environment
            elif not plant and container_environment:
                pass

            plant_name_with_birth_date = f"{plant.name}_{date_to_epoch(plant.birth_date)}" if plant else None
            parsed_ce_max_size = None
            parsed_aiw_size = None

            if delete_container:
                updated_container_environment_name = f'DELETE_{container_environment.name}'
                action = 'DELETE ENVIRONMENT'
            else:
                updated_container_environment_name = container_environment.name if container_environment else None

            if delete_plant:
                updated_plant_name = f'DELETE_{plant_name_with_birth_date}'
                action = 'HARVEST PLANT'
            else:
                updated_plant_name = plant_name_with_birth_date if plant else None

            if container_environment:
                try:
                    parsed_ce_max_size = int(container_environment.max_size)
                except Exception as e:
                    print(f'[!] record_history() Error {e}.')
                    parsed_ce_max_size = container_environment.max_size if container_environment else None

            if plant:
                try:
                    parsed_aiw_size = int(plant.age_in_weeks)
                except Exception as e:
                    print(f'[!] record_history() Error. {e}')
                    parsed_aiw_size = plant.age_in_weeks if container_environment else None

            cursor.execute('''INSERT INTO plant_history 
                              (event_epoch, name, harvest_type, environment_name, environment_max_size, 
                              environment_grid, grow_type, thc, cbd, birth_date, harvest_date, bottle_date, 
                              low_cure_date, mid_cure_date, high_cure_date, age_in_weeks, container_name, 
                              container_dimensions, action, harvest_amount) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (ingest_epoch,
                            updated_plant_name,
                            plant.harvest_type if plant else None,
                            updated_container_environment_name,
                            parsed_ce_max_size,
                            f'{container_environment.grid}' if container_environment else None,
                            plant.grow_type if plant else None,
                            plant.thc if plant else None,
                            plant.cbd if plant else None,
                            date_to_epoch(plant.birth_date) if plant else None,
                            date_to_epoch(plant.harvest_date) if plant else None,
                            date_to_epoch(plant.bottle_date) if plant else None,
                            date_to_epoch(plant.low_cure_date) if plant else None,
                            date_to_epoch(plant.mid_cure_date) if plant else None,
                            date_to_epoch(plant.high_cure_date) if plant else None,
                            parsed_aiw_size,
                            container_environment.name if container_environment else None,
                            f'{container_environment.dimensions}' if container_environment else None,
                            action,
                            plant.harvest_amount if plant else 0))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def get_all_plants(self):
        return self.completed_dict['plants']

    def add_plant(self, plant):
        self.completed_dict['plants'][plant.id] = plant
        self.update_database()
        self.record_history(plant=plant, action='CREATE PLANT')

    def delete_plant(self, plant_id, _harvest_amount, event_epoch=time.time()):
        plant = self.completed_dict['plants'].get(int(plant_id))
        plant = self.completed_dict['plants'].get(plant_id) if not plant else plant
        plant.harvest_amount = _harvest_amount
        if not isinstance(plant, Plant):
            print(f"[!] The 'delete_plant' backend requires a 'Plant' object. `{type(plant)}` type was passed.")
            return False
        src_container_environment = self.completed_dict['container_environments'].get(plant.environment.name)
        if plant_id in self.completed_dict['plants']:
            src_container_environment.remove_container(int(plant_id))
            del self.completed_dict['plants'][plant_id]
            self.update_database()
            self.record_history(plant=plant, delete_plant=True, ingest_epoch=event_epoch)
            self.record_history(container_environment=src_container_environment, action='DELETE PLANT',
                                ingest_epoch=event_epoch)
            return True
        return False

    def delete_container_environment(self, container_name):
        container_env = self.completed_dict['container_environments'].get(container_name, None)
        if container_env:
            # Check if all grid positions are empty (None)
            if container_env.is_grid_empty():
                del self.completed_dict['container_environments'][container_name]
                self.update_database()
                self.record_history(container_environment=container_env, delete_container=True)
                return True
            else:
                print("Cannot delete environment: Grid is not empty. Please move or delete plant(s) first.")
                return False
        return False

    def move_plant(self, plant_id, new_container_env_name, event_time=time.time()):
        plant = self.completed_dict['plants'].get(int(plant_id))
        plant = self.completed_dict['plants'].get(plant_id) if not plant else plant
        src_container_environment = self.completed_dict['container_environments'].get(plant.environment.name)
        dest_container_environment = self.completed_dict['container_environments'].get(new_container_env_name)
        if plant and dest_container_environment:
            # Remove the plant's container from the current environment's grid
            if src_container_environment.remove_container(plant.id):
                plant.update_environment(None)
                self.update_database()
                self.record_history(plant=plant, action='MOVE PLANT (REMOVE)', ingest_epoch=event_time)
                # Try to add the plant's container to the new environment's grid
                if dest_container_environment.add_container(plant):
                    # Update the plant's environment
                    plant.update_environment(dest_container_environment)
                    self.update_database()
                    self.record_history(plant=plant, action='MOVE PLANT (ADD)', ingest_epoch=event_time)
                    return True
                else:
                    # If adding to the new environment fails, add it back to the old environment
                    src_container_environment.add_container(plant)
                    plant.update_environment(src_container_environment)
                    self.update_database()
                    self.record_history(plant=plant, action='MOVE FAILED (PUTTING BACK)', ingest_epoch=event_time)
                    return False
            else:
                return False  # Failed to remove from old environment
        return False  # Plant or new environment not found

    def get_available_containers(self):
        return list(self.completed_dict['container_environments'].keys())

    def send_email_notification(self, email_address):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("cspeakesinfo@gmail.com", os.environ.get('GMAIL_EMAIL_APP_PASSWORD'))
        message = "Subject: Water Day Reminder\n\nIt's time to water your plants! Be sure to update the app!"
        server.sendmail("cspeakes@gmail.com", email_address, message)
        server.quit()

    def get_current_week_chemical_schedule(self):
        current_week_schedule = {}

        # Iterate through each plant in the completed_dict
        for plant_id, plant in self.completed_dict['plants'].items():
            if plant.age_in_weeks == 0:
                msg = 'Plant must be at least 1 week old before chemical schedule applies.'
                current_week_schedule[plant.name] = {'week': 0, 'chemicals': {'chemical': '0 ', 'Note': msg},
                                                     'environment': plant.environment.name}
                continue
            current_week = plant.age_in_weeks  # Assuming age_in_weeks is up-to-date
            current_week_schedule[plant.name] = {
                'week': current_week,
                'chemicals': plant.get_chemical_schedule_for_week(current_week),
                'environment': plant.environment.name
            }

        return current_week_schedule
