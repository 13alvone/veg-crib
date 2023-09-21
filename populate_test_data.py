import time
import math
import random
import string
from datetime import timedelta, datetime

from veg_crib_manage import Plant, ContainerEnvironment, Chemical, Backend  # Import your existing classes

# Global Variables
backend = None
plants = []
container_environments = []

# Initialize constants
PLANT_NAME_LENGTH = 10
TOTAL_MONTHS = 36  # For 3 years
TOTAL_YEARS = round(TOTAL_MONTHS/12, 1)
GENERAL_RANDOM_POOL_SIZE = 10
BATCH_INTERVAL = 1.5  # 1.5 months
N_CONTAINER_ENVS = 5
MAX_LIFE_WEEKS = int(16 * 1.2)  # 16 weeks + 20% longer
MAX_WEIGHT_VARIANCE = 0.3  # 30% variance in weight


def generate_random_epochs(count_of_epoch_vals, years, direction="future"):
    """
    Generate a list of count_of_epoch_vals randomized epoch float values spread over years into the past or future.

    Parameters:
    count_of_epoch_vals (int): The number of epoch values you want.
    years (float): The number of years you want to look into the past or future.
    direction (str): "past" or "future" to indicate the direction of time.

    Returns:
    list: A list of count_of_epoch_vals epoch float values.
    """

    # Input Sanitization
    if not isinstance(count_of_epoch_vals, int) or not (
            isinstance(years, int) or isinstance(years, float)) or not isinstance(direction, str):
        raise TypeError("Invalid input types.")

    if count_of_epoch_vals <= 0 or years <= 0:
        raise ValueError("count_of_epoch_vals and years must be greater than zero.")

    if direction not in ["past", "future"]:
        raise ValueError("direction must be either 'past' or 'future'.")

    # Calculate the event_ratio
    event_ratio = count_of_epoch_vals / years

    # Initialize the list to store epoch values
    epoch_list = []

    # Get the current epoch time
    current_epoch = time.time()

    # Calculate the epoch time for years into the past or future
    time_offset = years * 365 * 24 * 60 * 60
    future_epoch = current_epoch + time_offset if direction == "future" else current_epoch - time_offset

    if event_ratio <= 1:
        # No two events can happen in the same year
        for i in range(count_of_epoch_vals):
            year_start = current_epoch + (i * 365 * 24 * 60 * 60) if direction == "future" else current_epoch - (
                        i * 365 * 24 * 60 * 60)
            year_end = year_start + (365 * 24 * 60 * 60)
            random_epoch = random.uniform(year_start, year_end)
            epoch_list.append(random_epoch)
    else:
        # All years should have at least one event
        for i in range(int(years)):
            year_start = current_epoch + (i * 365 * 24 * 60 * 60) if direction == "future" else current_epoch - (
                        i * 365 * 24 * 60 * 60)
            year_end = year_start + (365 * 24 * 60 * 60)
            random_epoch = random.uniform(year_start, year_end)
            epoch_list.append(random_epoch)

        # Generate additional events
        additional_events = count_of_epoch_vals - int(years)
        for _ in range(additional_events):
            random_epoch = random.uniform(current_epoch, future_epoch)
            epoch_list.append(random_epoch)

    # Sort the epoch list
    epoch_list.sort()

    return [round(x, 2) for x in epoch_list]


def generate_plant_name():  # Generate random alphanumeric plant name
    return ''.join(random.choices(string.ascii_letters + string.digits, k=PLANT_NAME_LENGTH))


def generate_initial_data():  # Generate initial data
    global plants, container_environments
    container_names = [f"Container_{i+1}" for i in range(N_CONTAINER_ENVS)]

    for container_name in container_names:
        container_environment = ContainerEnvironment(container_name, {'row_count': random.choice([2, 3, 4, 5, 6, 7]),
                                                                      'column_count': random.choice([1, 2, 3])})

        container_environments.append(container_environment)
        backend.completed_dict['container_environments'][container_environment.name] = container_environment
        backend.update_database()
        backend.record_history(container_environment=container_environment,
                               action='CREATE ENVIRONMENT',
                               ingest_epoch=1600253921)

    # Loop until next_batch_date is within TOTAL_MONTHS months from the current date and time.
    next_batch_date = datetime.now()
    while (next_batch_date.year * 12 + next_batch_date.month) <= \
            (datetime.now().year * 12 + datetime.now().month) + TOTAL_MONTHS:
        n_plants_in_batch = random.randint(3, 6)
        for _ in range(n_plants_in_batch):
            harvest_type = random.choice(["indica", "sativa", "hybrid", "hybrid:indica", "hybrid:sativa"])
            grow_type = random.choice(["standard", "auto"])  # Assuming grow_types is an attribute or method
            thc_value = random.uniform(17.0, 32.0)
            cbd_value = random.uniform(0.1, 8.0)
            b_day = random.choice(generate_random_epochs(GENERAL_RANDOM_POOL_SIZE, TOTAL_YEARS, direction="past"))
            harvest_date = b_day + timedelta(weeks=16).total_seconds()

            plant = Plant(
                name=generate_plant_name(),
                environment=random.choice(container_environments),
                harvest_type=harvest_type,
                grow_type=grow_type,
                thc=thc_value,
                cbd=cbd_value,
                birth_date=b_day,
                harvest_date=harvest_date,
                bottle_date=harvest_date,  # Default to harvest_date
                low_cure_date=b_day + timedelta(weeks=20).total_seconds(),
                mid_cure_date=b_day + timedelta(weeks=23, days=3).total_seconds(),
                high_cure_date=b_day + timedelta(weeks=27).total_seconds(),
                age_in_weeks=math.ceil((datetime.now().date() - datetime.fromtimestamp(b_day).date()).days / 7)
            )

            backend.add_plant(plant)
            plants.append(plant)

        next_batch_date += timedelta(weeks=int(BATCH_INTERVAL * 4))

    return plants, container_environments


def random_other_env_name(plant):
    global container_environments
    return random.choice([obj.name for obj in container_environments if obj is not plant.environment])


def simulate_16_watering_sessions(plant):
    global backend
    task_times = [plant.birth_date + timedelta(days=random.choice([6, 7])).total_seconds()]
    for _ in range(2, 16):
        new_water_time = task_times[-1] + timedelta(days=random.choice([6, 7, 8])).total_seconds()
        task_times.append(new_water_time)

    for task_epoch in task_times:
        target_week = task_times.index(task_epoch) if task_times.index(task_epoch) <= 16 else 16
        x = plant.get_chemical_schedule_for_week(target_week)
        for chemical, ml_value in plant.get_chemical_schedule_for_week(target_week).items():
            # Save to SQLite database
            backend.save_chemical_values(plant.id, chemical, ml_value, 4, event_epoch=task_epoch)
            backend.update_database()
            backend.record_history(plant=plant,
                                   container_environment=plant.environment,
                                   action=f"WATER PLANT ({chemical})",
                                   ingest_epoch=task_epoch)


def simulate_all_plant_lifecycles():
    global backend, plants, container_environments
    for plant in plants:

        move_0 = plant.birth_date + timedelta(weeks=1).total_seconds()
        move_1 = plant.birth_date + \
                 timedelta(weeks=random.choice([6, 7, 8]), days=random.choice([1, 2, 3])).total_seconds()
        move_2 = plant.birth_date + \
                 timedelta(weeks=random.choice([16, 17, 18]), days=random.choice([1, 2, 3, 4])).total_seconds()
        x = random_other_env_name(plant)
        backend.move_plant(plant.id, random_other_env_name(plant), move_0)
        backend.move_plant(plant.id, random_other_env_name(plant), move_1)
        backend.move_plant(plant.id, random_other_env_name(plant), move_2)

        simulate_16_watering_sessions(plant)

        delete_epoch_test = plant.birth_date + timedelta(weeks=random.sample(range(16, 20), 1)[0],
                                                         days=random.sample(range(1, 6), 1)[0]).total_seconds()
        if delete_epoch_test <= time.time():
            backend.delete_plant(plant.id, random.randint(32, 80), event_epoch=delete_epoch_test)


def main():
    global backend, plants, container_environments
    backend = Backend()
    plants, container_environments = generate_initial_data()
    simulate_all_plant_lifecycles()


if __name__ == "__main__":
    main()
