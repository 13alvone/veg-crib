from flask import Flask, render_template, request, redirect, url_for
from veg_crib_manage import Backend, Chemical, ContainerEnvironment, Plant, PlantContainer

app = Flask(__name__)
backend = Backend()

# Create a default environment for demonstration purposes
default_environment = ContainerEnvironment("Default", {'row_count': 5, 'column_count': 5})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return "Welcome to Veg Crib!"

@app.route('/add_environment', methods=['GET', 'POST'])
def add_environment():
    if request.method == 'POST':
        x_dim = int(request.form['x_dim'])
        y_dim = int(request.form['y_dim'])
        name = request.form['name']
        new_environment = ContainerEnvironment(name, {'row_count': x_dim, 'column_count': y_dim})
        backend.completed_dict['container_environments'][name] = new_environment
        backend.update_database()
        return redirect(url_for('index'))
    return render_template('add_environment.html')

@app.route('/add_plant', methods=['GET', 'POST'])
def add_plant():
    if request.method == 'POST':
        name = request.form['name']
        harvest_type = request.form['harvest_type']
        environment_name = request.form['environment']
        environment = backend.completed_dict['container_environments'].get(environment_name)
        new_plant = Plant(name, harvest_type, environment, id)
        backend.completed_dict['plants'][id] = new_plant
        backend.update_database()
        return redirect(url_for('index'))
    environments = list(backend.completed_dict['container_environments'].keys())
    return render_template('add_plant.html', environments=environments)

#@app.route('/view_environments')
#def view_environments():
#    backend.load_from_database()  # Replacing thaw_custom_objects with load_from_database
#    environments = backend.completed_dict['container_environments']
#    return render_template('view_environments.html', environments=environments)

@app.route('/view_environments')
def view_environments():
    backend.load_from_database()
    environments = backend.completed_dict['container_environments']
    print(type(environments))  # Debugging line
    print(environments)  # Debugging line
    return render_template('view_environments.html', environments=environments)

@app.route('/view_plants')
def view_plants():
    backend.load_from_database()  # Replacing thaw_custom_objects with load_from_database
    plants = backend.completed_dict['plants']
    return render_template('view_plants.html', plants=plants)


if __name__ == '__main__':
    app.run(debug=True)

