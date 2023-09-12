from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta, date
import math

from veg_crib_manage import Backend, ContainerEnvironment, Plant

app = Flask(__name__)
app.secret_key = 'F2419C26-71EF-495E-ACCE-A5C615C675B2@@C4BD86FF-D8B4-4955-9D4C-68D70FBF4A23'  # Required for flash
backend = Backend()


@app.route('/')
def index():
    # Clear any existing flash messages
    session.pop('_flashes', None)
    return render_template('index.html')


@app.route('/global_settings', methods=['GET'])
def global_settings():
    return render_template('global_settings.html')

@app.route('/update_global_settings', methods=['POST'])
def update_global_settings():
    global backend
    water_day = request.form.get('globalWaterDay')
    water_period = int(request.form.get('globalWaterPeriod', 7))  # Default to 7 if not provided

    # Convert water_day to datetime object
    water_day = datetime.strptime(water_day, '%Y-%m-%d')


@app.route('/enter_water_day_values', methods=['GET'])
def enter_water_day_values():
    week_monday_date = calculate_week_monday_date()  # Implement this function
    plants = get_all_plants_with_chemicals()  # Implement this function
    return render_template('enter_water_day_values.html', week_monday_date=week_monday_date, plants=plants)


@app.route('/submit_water_day_values', methods=['POST'])
def submit_water_day_values():
    for plant in get_all_plants_with_chemicals():  # Implement this function
        actual_value = request.form.get(f"actualValue_{plant.id}_{plant.chemical_name}")
        if actual_value:
            record_actual_chemical_usage(plant.id, calculate_current_week_number(), plant.chemical_name, float(actual_value))


@app.route('/record_chemical_usage', methods=['POST'])
def record_chemical_usage():
    plant_id = request.form.get('plantId')
    week_number = calculate_current_week_number()  # Implement this function
    chemical_name = request.form.get('chemicalName')
    actual_value = float(request.form.get('actualValue'))  # Type validation
    record_actual_chemical_usage(plant_id, week_number, chemical_name, actual_value)


@app.route('/check_email_credentials', methods=['GET'])
def check_email_credentials():
    missing = backend.check_email_credentials()
    show_alert = backend.check_show_alert()
    return jsonify({'missing': missing, 'show_alert': show_alert})


@app.route('/add_environment', methods=['GET', 'POST'])
def add_environment():
    # Clear any existing flash messages
    session.pop('_flashes', None)
    if request.method == 'POST':
        x_dim = int(request.form['x_dim'])
        y_dim = int(request.form['y_dim'])
        name = request.form['name']
        new_environment = ContainerEnvironment(name, {'row_count': x_dim, 'column_count': y_dim})
        backend.completed_dict['container_environments'][name] = new_environment
        backend.update_database()
        backend.record_history(container_environment=new_environment, action='CREATE ENVIRONMENT')
        return redirect(url_for('index'))
    return render_template('add_environment.html')


@app.route('/add_plant', methods=['GET', 'POST'])
def add_plant():
    # Clear any existing flash messages
    session.pop('_flashes', None)
    backend.load_from_database()
    # water_day = request.form.get('waterDay')
    # water_period = int(request.form.get('waterPeriod', 7))  # Default to 7 if not provided
    # water_day = datetime.strptime(water_day, '%Y-%m-%d')
    if request.method == 'POST':
        environment_name = request.form.get('environment', None)

        if not environment_name:
            flash('Error: No environment selected or available')
            return redirect(url_for('add_plant'))

        # Validate name
        name = request.form['name']
        if not name.isalnum():
            flash('Only alphanumeric entries are allowed for the name.')
            return redirect(url_for('add_plant'))

        # Validate THC
        thc = float(request.form['thc'])
        if thc < 0 or thc > 100:
            flash('THC percentages must be numeric values between 0 and 100.')
            return redirect(url_for('add_plant'))

        # Validate CBD
        cbd = float(request.form['cbd'])
        if cbd < 0 or cbd > 100:
            flash('CBD percentages must be numeric values between 0 and 100.')
            return redirect(url_for('add_plant'))

        # Validate birth_date
        birth_date_str = request.form['birth_date']
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        ten_years_ago = today - timedelta(days=3650)
        one_week_later = today + timedelta(days=7)

        if birth_date < ten_years_ago:
            flash('Dates older than 10 years from today are not applicable.')
            return redirect(url_for('add_plant'))

        if birth_date > one_week_later:
            flash('Date planning more than 7 days in the future are generally plans not followed.')
            return redirect(url_for('add_plant'))

        harvest_type = request.form['harvest_type']
        environment_name = request.form['environment']
        environment = backend.completed_dict['container_environments'].get(environment_name)
        grow_type = request.form['grow_type']

        # Calculations
        harvest_date = birth_date + timedelta(weeks=17)
        bottle_date = harvest_date  # Default to harvest_date
        low_cure_date = birth_date + timedelta(weeks=20)
        mid_cure_date = birth_date + timedelta(weeks=23, days=3)
        high_cure_date = birth_date + timedelta(weeks=27)
        age_in_weeks = math.ceil((datetime.now().date() - birth_date).days / 7)

        # Create Plant object and add to backend
        new_plant = Plant(name, harvest_type, environment, grow_type, thc, cbd, birth_date,
                          harvest_date, bottle_date, low_cure_date, mid_cure_date, high_cure_date,
                          age_in_weeks)
        environment.add_container(new_plant)
        backend.add_plant(new_plant)  # Add the new plant to the backend
        return redirect(url_for('view_plants'))

    # For GET request, just show the form
    environments = list(backend.completed_dict['container_environments'].keys())
    return render_template('add_plant.html', environments=environments)


@app.route('/view_environments')
def view_environments():
    session.pop('_flashes', None)
    backend.load_from_database()
    environments = backend.completed_dict['container_environments']
    return render_template('view_environments.html', environments=environments)


@app.route('/view_plants')
def view_plants():
    session.pop('_flashes', None)
    backend.load_from_database()
    plants = backend.completed_dict['plants']
    return render_template('view_plants.html', plants=plants)


@app.route('/delete_plant_page', methods=['GET'])
def delete_plant_page():
    session.pop('_flashes', None)
    backend.load_from_database()
    plants = backend.get_all_plants()  # Implement this function to fetch all plants
    _plant_info = {z.id: z.name for z in [y for x, y in plants.items()]}
    return render_template('delete_plant_page.html', plant_info=_plant_info)


@app.route('/delete_plant', methods=['POST'])
def delete_plant():
    session.pop('_flashes', None)
    backend.load_from_database()
    plant_id = request.form.get('plantId')
    harvest_amount = float(request.form.get('harvestAmount'))  # Type validation
    backend.delete_plant(plant_id, harvest_amount)
    return render_template(url_for('index'))


@app.route('/delete_environment/<environment_name>', methods=['POST'])
def delete_container_environment(environment_name):
    session.pop('_flashes', None)
    backend.load_from_database()
    if backend.delete_container_environment(environment_name):
        flash('Container deleted successfully.')
    else:
        flash('Failed to delete container.')
    return redirect(url_for('view_environments'))


@app.route('/move_plant/<plant_id>', methods=['GET', 'POST'])
def move_plant(plant_id):
    # Clear any existing flash messages
    session.pop('_flashes', None)
    backend.load_from_database()
    if request.method == 'POST':
        new_container_id = request.form['new_container_id']
        if backend.move_plant(plant_id, new_container_id):
            flash('Plant moved successfully.')
            print('[!] Debug: Plant Moved Successfully.')
        else:
            flash('Failed to move plant.')
        return redirect(url_for('view_plants'))
    # For GET request, show the form to select a new container
    available_containers = backend.get_available_containers()
    print("Debug: Plant ID is", plant_id)
    return render_template(f'move_plant.html', available_containers=available_containers, plant_id=plant_id)


@app.route('/chemical_schedule')
def chemical_schedule():
    backend.load_from_database()
    current_week_schedule = backend.get_current_week_chemical_schedule()
    return render_template('chemical_schedule.html', current_week_schedule=current_week_schedule)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
