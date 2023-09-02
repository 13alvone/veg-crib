import re
from datetime import datetime

import wx
import wx.grid
import pandas as pd
from dateutil import parser
from veg_crib_manage import Backend, Plant, PlantContainer, ContainerEnvironment


class MainFrame(wx.Frame):
    def __init__(self):
        msg = f'[i] This program utilizes the company `TPS Plant Foods` for all plant nutrient needs.\n' \
              f'> Information regarding TPS Methodology found here: `https://tpsnutrients.com/pages/about-us`\n>' \
              f'`TPS Plant Foods` feed charts found directly from: https://tpsnutrients.com/pages/feedcharts\n' \
              f'**Disclaimer** This is an educational program only, and in no way affiliated with `TPS Plant Foods`.\n'
        wx.MessageBox(msg, 'Info', wx.OK)
        self.title_font = wx.Font(24, wx.ROMAN, wx.ITALIC, wx.NORMAL, wx.ALIGN_CENTRE)
        self.style = wx.EVT_SET_FOCUS and wx.EVT_KILL_FOCUS
        self.backend = Backend()
        self.known_error = False
        self.standard_spacer = 5
        self.initial_plants = [f'{x}' for x, _ in self.backend.completed_dict['plants'].items()]
        self.initial_containers = [f'{x}' for x, _ in self.backend.completed_dict['container_environments'].items()]

        # *************************
        # Main Program Frame
        # *************************

        wx.Frame.__init__(self, None, -1, 'Hydroponic Plant and Chemical Management System')
        self.notebook = wx.Notebook(self)  # Create a notebook control
        self.veg_crib_icon = 'veg_crib_icon.png'

        self.notebook_panel_summary = wx.Panel(self.notebook)
        self.notebook_panel_add_plant = wx.Panel(self.notebook)
        self.notebook_panel_remove_plant = wx.Panel(self.notebook)
        self.notebook_panel_move_plant = wx.Panel(self.notebook)
        self.notebook_panel_create_env = wx.Panel(self.notebook)
        self.notebook_panel_remove_env = wx.Panel(self.notebook)

        self.notebook.AddPage(self.notebook_panel_summary, 'Weekly Chemical Schedule')
        self.notebook.AddPage(self.notebook_panel_add_plant, 'Add Plant')
        self.notebook.AddPage(self.notebook_panel_remove_plant, 'Remove Plant')
        self.notebook.AddPage(self.notebook_panel_move_plant, 'Move Plant')
        self.notebook.AddPage(self.notebook_panel_create_env, 'Create Environment')
        self.notebook.AddPage(self.notebook_panel_remove_env, 'Remove Environment')

        self.current_plants_title = wx.StaticText(self, label="Current Plants:")
        self.current_plants_title.SetFont(self.title_font)
        self.plant_grid = self.generate_grid(self.backend.df_plant, lock_grid=True)
        self.resize_grid_to_fix_text(self.plant_grid, self.backend.df_plant)

        self.root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.root_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.root_sizer.Add(self.current_plants_title, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.root_sizer.Add(self.plant_grid, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.SetSizer(self.root_sizer)

        self.rename_columns(self.plant_grid, {'thc_percentage': 'THC%',  # Rename and format column names
                                              'cbd_percentage': 'CBD%',
                                              'age_in_weeks,': 'Weeks'})

        # *************************
        # Summary Page
        # *************************

        self.chemical_grid = self.generate_grid(self.backend.df_chemical, lock_grid=True)
        self.chemical_grid.Reparent(self.notebook_panel_summary)
        self.chemical_grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.pre_post_fix_rows(self.chemical_grid, self.backend.df_chemical, prefix='Week ', postfix=':')
        self.resize_grid_to_fix_text(self.chemical_grid, self.backend.df_chemical)

        self.summary_sizer = wx.BoxSizer(wx.VERTICAL)
        self.summary_sizer.Add(self.chemical_grid, 1, wx.EXPAND)
        self.summary_sizer.AddSpacer(self.standard_spacer * 4)
        self.notebook_panel_summary.SetSizer(self.summary_sizer)

        # *************************
        # Add Plant Page
        # *************************

        self.plant_env_name = wx.StaticText(self.notebook_panel_add_plant, label="Environment Name:\t\t")
        self.env_choices = [f'{x}' for x in self.backend.completed_dict['container_environments']]
        self.add_plant_dropdown_environment = wx.ComboBox(self.notebook_panel_add_plant, choices=self.env_choices)

        self.add_plant_name = wx.StaticText(self.notebook_panel_add_plant, label="Plant Name:\t")
        self.add_plant_name_in = wx.TextCtrl(self.notebook_panel_add_plant, size=(250, -1))
        self.add_plant_name_in.Bind(self.style, self.validate_all_add_plant)
        self.add_plant_name_in.Bind(self.style, self.validate_plant_name_unique)

        self.add_plant_type = wx.StaticText(self.notebook_panel_add_plant, label="Harvest Type:\t\t\t\t")
        self.plant_types = ['unknown', 'indica', 'sativa', 'cbd', 'hybrid']
        self.add_plant_type_in_dropdown = wx.ComboBox(self.notebook_panel_add_plant, choices=self.plant_types)

        self.add_plant_grow_type = wx.StaticText(self.notebook_panel_add_plant, label="Grow Type:\t\t\t\t")
        self.plant_types = ['unknown', 'standard', 'auto']
        self.add_plant_grow_type_in_dropdown = wx.ComboBox(self.notebook_panel_add_plant, choices=self.plant_types)

        self.add_plant_thc = wx.StaticText(self.notebook_panel_add_plant, label="THC Percentage:\t\t\t")
        self.add_plant_thc_in = wx.TextCtrl(self.notebook_panel_add_plant, size=(100, -1))
        self.add_plant_thc_in.Bind(self.style, self.validate_all_add_plant)

        self.add_plant_cbd = wx.StaticText(self.notebook_panel_add_plant, label="CBD Percentage:\t\t\t")
        self.add_plant_cbd_in = wx.TextCtrl(self.notebook_panel_add_plant, size=(100, -1))
        self.add_plant_cbd_in.Bind(self.style, self.validate_all_add_plant)

        self.add_plant_birthday = wx.StaticText(self.notebook_panel_add_plant, label="Plant Birthday:\t\t\t")
        self.add_plant_birthday_in = wx.TextCtrl(self.notebook_panel_add_plant, size=(150, -1),
                                                 value=datetime.now().strftime('%m/%d/%Y'))
        self.add_plant_birthday_in.Bind(self.style, self.validate_all_add_plant)

        _label_msg = f'Container Dimensions:\t\t'
        self.add_plant_container_name = wx.StaticText(self.notebook_panel_add_plant, label=_label_msg)
        self.add_plant_container_name_in = wx.TextCtrl(self.notebook_panel_add_plant, size=(100, -1), value='4x3')
        self.add_plant_container_name_in.Bind(self.style, self.validate_all_add_plant)

        self.add_plant_execute_button = wx.Button(self.notebook_panel_add_plant, label="Add Plant")
        self.add_plant_execute_button.Bind(wx.EVT_BUTTON, self.click_add_plant)

        self.add_plant_sizer = wx.BoxSizer(wx.VERTICAL)
        self.add_plant_sizer.AddSpacer(self.standard_spacer * 2)
        self.add_adjacent_to_sizer(self.plant_env_name,
                                   self.add_plant_dropdown_environment,
                                   self.add_plant_sizer,
                                   tab_over=False)
        self.add_plant_sizer.Add(self.add_plant_name, 1)
        self.add_plant_sizer.Add(self.add_plant_name_in, 1)
        self.add_plant_sizer.AddSpacer(self.standard_spacer * 2)
        self.add_adjacent_to_sizer(self.add_plant_type, self.add_plant_type_in_dropdown, self.add_plant_sizer)
        self.add_adjacent_to_sizer(self.add_plant_grow_type, self.add_plant_grow_type_in_dropdown, self.add_plant_sizer)
        self.add_adjacent_to_sizer(self.add_plant_thc, self.add_plant_thc_in, self.add_plant_sizer)
        self.add_adjacent_to_sizer(self.add_plant_cbd, self.add_plant_cbd_in, self.add_plant_sizer)
        self.add_adjacent_to_sizer(self.add_plant_birthday, self.add_plant_birthday_in, self.add_plant_sizer)
        self.add_adjacent_to_sizer(self.add_plant_container_name,
                                   self.add_plant_container_name_in,
                                   self.add_plant_sizer)
        self.add_plant_sizer.Add(self.add_plant_execute_button, 1)
        self.add_plant_sizer.AddSpacer(self.standard_spacer * 10)
        self.notebook_panel_add_plant.SetSizer(self.add_plant_sizer)

        # *************************
        # Remove Plant Page
        # *************************

        self.remove_plant_name = wx.StaticText(self.notebook_panel_remove_plant, label="Existing Plants:")
        self.remove_plant_name_in = wx.ComboBox(self.notebook_panel_remove_plant, choices=self.initial_plants)
        self.remove_plant_name_in.Bind(wx.EVT_COMBOBOX, self.plookup_remove_page)

        self.remove_plant_env_name = wx.StaticText(self.notebook_panel_remove_plant, label="Environment Name:\t\t")
        self.remove_plant_env_name_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(300, -1),
            value=self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'environment').name)
        self.remove_plant_env_name_in.SetEditable(False)

        self.remove_plant_type = wx.StaticText(self.notebook_panel_remove_plant, label="Harvest Type:\t\t\t\t")
        self.remove_plant_type_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(300, -1),
            value=self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'harvest_type'))
        self.remove_plant_type_in.SetEditable(False)

        self.remove_plant_grow_type = wx.StaticText(self.notebook_panel_remove_plant, label="Grow Type:\t\t\t\t")
        self.remove_plant_grow_type_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(200, -1),
            value=self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'grow_type'))
        self.remove_plant_grow_type_in.SetEditable(False)

        self.remove_plant_thc = wx.StaticText(self.notebook_panel_remove_plant, label="THC Percentage:\t\t\t")
        self.remove_plant_thc_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(200, -1),
            value=str(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'thc_percentage')))
        self.remove_plant_thc_in.SetEditable(False)

        self.remove_plant_cbd = wx.StaticText(self.notebook_panel_remove_plant, label="CBD Percentage:\t\t\t")
        self.remove_plant_cbd_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(100, -1),
            value=str(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'cbd_percentage')))
        self.remove_plant_cbd_in.SetEditable(False)

        self.remove_plant_birthday = wx.StaticText(self.notebook_panel_remove_plant, label="Plant Birthday:\t\t\t")
        self.remove_plant_birthday_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(150, -1),
            value=str(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'birth_date')))
        self.remove_plant_birthday_in.SetEditable(False)

        _label_msg = f'Container Dimensions:\t\t'
        self.remove_plant_container_name = wx.StaticText(self.notebook_panel_remove_plant, label=_label_msg)
        self.remove_plant_container_name_in = wx.TextCtrl(
            self.notebook_panel_remove_plant, size=(100, -1),
            value=vars(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'container'))['dimensions'])
        self.remove_plant_container_name_in.SetEditable(False)

        # Create `Execute` button object and dynamically fill values based on action choice:
        self.remove_plant_execute_button = wx.Button(self.notebook_panel_remove_plant, label="Remove Plant")
        self.remove_plant_execute_button.Bind(wx.EVT_BUTTON, self.click_remove_plant)

        self.remove_plant_sizer = wx.BoxSizer(wx.VERTICAL)
        self.remove_plant_sizer.Add(self.remove_plant_name, 1)
        self.remove_plant_sizer.Add(self.remove_plant_name_in, 1)
        self.add_adjacent_to_sizer(self.remove_plant_env_name, self.remove_plant_env_name_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(self.remove_plant_type, self.remove_plant_type_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(self.remove_plant_grow_type, self.remove_plant_grow_type_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(self.remove_plant_thc, self.remove_plant_thc_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(self.remove_plant_cbd, self.remove_plant_cbd_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(self.remove_plant_birthday, self.remove_plant_birthday_in, self.remove_plant_sizer)
        self.add_adjacent_to_sizer(
            self.remove_plant_container_name, self.remove_plant_container_name_in, self.remove_plant_sizer)
        self.remove_plant_sizer.Add(self.remove_plant_execute_button, 1)
        self.notebook_panel_remove_plant.SetSizer(self.remove_plant_sizer)

        # *************************
        # Move Plant Page
        # *************************

        self.move_plant_name = wx.StaticText(self.notebook_panel_move_plant, label="Plant to move:\t")
        self.move_plant_name_in = wx.ComboBox(self.notebook_panel_move_plant,  value='', choices=self.initial_plants)
        self.move_plant_name_in.Bind(wx.EVT_COMBOBOX, self.elookup_move_page)
        # self.move_plant_name_in.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, on_tab_click)

        self.move_plant_env_name = wx.StaticText(self.notebook_panel_move_plant, label="\t\tCurrent Environment:\t")
        self.move_plant_env_name_in = wx.TextCtrl(
            self.notebook_panel_move_plant, size=(200, -1),
            value=self.elookup(f'{self.move_plant_name_in.GetValue()}'))
        self.move_plant_env_name_in.SetEditable(False)

        self.move_plant_env_dest = wx.StaticText(self.notebook_panel_move_plant, label="\t\tMove to Environment:\t")
        self.move_plant_env_dest_in = wx.ComboBox(self.notebook_panel_move_plant,
                                                  value='', choices=self.initial_containers)

        self.move_plant_button = wx.Button(self.notebook_panel_move_plant, label="Move Plant")
        self.move_plant_button.Bind(wx.EVT_BUTTON, self.click_move_plant)

        # Sizer Schema
        self.change_plant_sizer = wx.BoxSizer(wx.VERTICAL)
        self.change_plant_sizer.AddSpacer(self.standard_spacer * 5)
        self.change_plant_sizer.Add(self.move_plant_name, 1, flag=wx.TOP)
        self.change_plant_sizer.Add(self.move_plant_name_in, 1, flag=wx.TOP)
        self.add_adjacent_to_sizer(self.move_plant_env_name, self.move_plant_env_name_in, self.change_plant_sizer)
        self.add_adjacent_to_sizer(self.move_plant_env_dest, self.move_plant_env_dest_in, self.change_plant_sizer)
        self.change_plant_sizer.AddSpacer(self.standard_spacer * 20)
        self.change_plant_sizer.Add(self.move_plant_button)
        self.change_plant_sizer.AddSpacer(self.standard_spacer * 10)
        self.notebook_panel_move_plant.SetSizer(self.change_plant_sizer)

        # *************************
        # Create Plant Environment Page
        # *************************

        self.create_env_name = wx.StaticText(self.notebook_panel_create_env, label="New Environment Name:\t\t")
        self.create_env_name_in = wx.TextCtrl(self.notebook_panel_create_env, size=(300, -1))
        self.create_env_name_in.Bind(self.style, self.validate_env_name_unique_create)

        _label_msg = 'Environment Dimensions (rxd):\t'
        self.create_env_dimensions = wx.StaticText(self.notebook_panel_create_env, label=_label_msg)
        self.create_env_dimensions_in = wx.TextCtrl(self.notebook_panel_create_env, size=(100, -1))
        self.create_env_dimensions_in.Bind(self.style, self.validate_all_create_env)

        self.create_env_button = wx.Button(self.notebook_panel_create_env, label="Create Environment")
        self.create_env_button.Bind(wx.EVT_BUTTON, self.click_create_environment)

        self.create_env_sizer = wx.BoxSizer(wx.VERTICAL)
        self.create_env_sizer.AddSpacer(self.standard_spacer)
        self.create_env_sizer.Add(self.create_env_name, 1)
        self.create_env_sizer.AddSpacer(self.standard_spacer)
        self.create_env_sizer.Add(self.create_env_name_in, 1)
        self.create_env_sizer.AddSpacer(self.standard_spacer * 10)
        self.add_adjacent_to_sizer(self.create_env_dimensions, self.create_env_dimensions_in, self.create_env_sizer)
        self.create_env_sizer.AddSpacer(self.standard_spacer * 10)
        self.create_env_sizer.AddSpacer(self.standard_spacer)
        self.create_env_sizer.AddSpacer(self.standard_spacer * 10)
        self.create_env_sizer.Add(self.create_env_button)
        self.create_env_sizer.AddSpacer(self.standard_spacer * 20)
        self.notebook_panel_create_env.SetSizer(self.create_env_sizer)

        # *************************
        # Remove Container Environment Page
        # *************************

        environment_choices = list(self.backend.completed_dict['container_environments'].keys())
        self.remove_env_name = wx.StaticText(self.notebook_panel_remove_env, label="Existing Environment to Remove:\t")
        self.remove_env_name_in = wx.ComboBox(self.notebook_panel_remove_env, choices=environment_choices)
        # self.remove_env_name_in.Bind(wx.EVT_COMBOBOX, self.elookup_move_page)
        # self.move_plant_name_in.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, on_tab_click)

        # self.remove_env_name = wx.StaticText(self.notebook_panel_remove_env, label="New Environment Name:\t\t")
        # self.remove_env_name_in = wx.TextCtrl(self.notebook_panel_remove_env, size=(300, -1))
        # self.remove_env_name_in.Bind(self.style, self.validate_env_name_unique_remove)

        # _label_msg = 'Environment Dimensions (rxd):\t'
        # self.remove_env_dimensions = wx.StaticText(self.notebook_panel_remove_env, label=_label_msg)
        # self.remove_env_dimensions_in = wx.TextCtrl(self.notebook_panel_remove_env, size=(100, -1))
        # self.remove_env_dimensions_in.Bind(self.style, self.validate_all_create_env)

        self.remove_env_button = wx.Button(self.notebook_panel_remove_env, label="Remove Environment")
        self.remove_env_button.Bind(wx.EVT_BUTTON, self.click_remove_environment)

        self.remove_env_sizer = wx.BoxSizer(wx.VERTICAL)
        self.remove_env_sizer.AddSpacer(self.standard_spacer)
        self.remove_env_sizer.Add(self.remove_env_name, 1)
        self.remove_env_sizer.Add(self.remove_env_name_in, 1)
        self.remove_env_sizer.AddSpacer(self.standard_spacer * 10)
        self.remove_env_sizer.Add(self.remove_env_button)
        self.remove_env_sizer.AddSpacer(self.standard_spacer * 60)
        self.notebook_panel_remove_env.SetSizer(self.remove_env_sizer)

        # *************************

        self.Fit()  # Fit the full frame
        self.Maximize()

    def click_add_plant(self, _):
        plant_id = self.backend.plant_count()
        plant_name = self.add_plant_name_in.GetValue()
        if not plant_name or plant_name == '':
            msg = f'Blank plant names are not allowed. Please try again.'
            self.add_plant_name_in.SetValue('')
            wx.MessageBox(msg, 'Info',  wx.OK)
            return
        elif not self.validate_plant_name_unique(plant_name):
            self.add_plant_name_in.SetValue('')
            return
        current_env = self.add_plant_dropdown_environment.GetValue()
        target_env = self.backend.completed_dict['container_environments'][current_env]
        new_plant = Plant(plant_name,
                          _harvest_type=self.add_plant_type_in_dropdown.GetValue(),
                          _environment=target_env,
                          _id=plant_id,
                          _birth_date=self.parse_date(self.add_plant_birthday_in.GetValue()),
                          _grow_type=self.add_plant_grow_type_in_dropdown.GetValue(),
                          _thc_percentage=self.add_plant_thc_in.GetValue(),
                          _cbd_percentage=self.add_plant_cbd_in.GetValue(),
                          _container_rxd=self.add_plant_container_name_in.GetValue())
        if new_plant.fully_complete:
            self.backend.completed_dict['plants'][plant_name] = new_plant
            self.update_plant_grid_add()
            self.plant_combobox_fix()
            self.env_combobox_fix()

    def click_remove_plant(self, _):
        plant_name = self.remove_plant_name_in.GetValue()
        if plant_name == '':
            return

        if plant_name in self.backend.completed_dict['plants'].keys():
            plant_obj = self.backend.completed_dict['plants'][plant_name]
            plant_container_obj = plant_obj.container
            plant_obj.environment.remove_container(plant_container_obj)
            del self.backend.completed_dict['plants'][plant_name]

            self.backend.record_complete()
            self.delete_row_from_grid(self.plant_grid, plant_name)
            self.plant_combobox_fix()
            self.env_combobox_fix()

    def click_move_plant(self, event):
        # Remove plant from existing location
        plant_name = self.move_plant_name_in.GetValue()
        if plant_name == '':
            return
        target_container_obj = self.backend.completed_dict['plants'][plant_name].container
        from_env_name = self.move_plant_env_name_in.GetValue()
        self.backend.completed_dict['container_environments'][from_env_name].remove_container(target_container_obj)

        # Move plant container object
        to_env_name = self.move_plant_env_dest_in.GetValue()
        to_env_obj = self.backend.completed_dict['container_environments'][to_env_name]
        self.backend.completed_dict['container_environments'][to_env_name].container = target_container_obj
        self.backend.completed_dict['plants'][plant_name].environment = to_env_obj
        self.update_plant_grid_change_env()
        self.plant_combobox_fix()
        self.env_combobox_fix()

    def click_create_environment(self, event):
        new_env_name = self.create_env_name_in.GetValue()
        input_dimensions = self.create_env_dimensions_in.GetValue()
        self.validate_item(input_dimensions, 'rxd')
        numbers = re.findall(r'^(\d+)(x|X)(\d+)$', input_dimensions)
        if not numbers:
            msg = f'Container dimensions must be in the following format `rxd` (Ex. `3x4`). Please try again.'
            self.create_env_dimensions_in.SetValue('')
            wx.MessageBox(msg, 'Info', wx.OK)
            self.create_env_name_in.SetValue('')
            self.create_env_dimensions_in.SetValue('')
            return

        numbers = [x for x in numbers[0]]
        if not new_env_name or new_env_name == '':
            msg = f'Blank plant names are not allowed. Please try again.'
            wx.MessageBox(msg, 'Info',  wx.OK)
            self.create_env_name_in.SetValue('')
            self.create_env_dimensions_in.SetValue('')
            return
        elif not self.validate_environment_name_unique(new_env_name):
            return
        elif self.known_error or len(numbers) != 3:
            msg = f'Container dimensions must be in the following format `rxd` (Ex. `3x4`). Please try again.'
            wx.MessageBox(msg, 'Info',  wx.OK)
            self.create_env_name_in.SetValue('')
            self.create_env_dimensions_in.SetValue('')
            return

        new_env_obj = ContainerEnvironment(new_env_name,
                                           {'row_count': int(numbers[0]), 'column_count': int(numbers[2])})
        self.backend.completed_dict['container_environments'][new_env_name] = new_env_obj
        self.backend.record_complete()
        self.plant_combobox_fix()
        self.env_combobox_fix()
        msg = f'Successfully added environment `{self.create_env_name_in.GetValue()}` with dimensions ' \
              f'`{self.create_env_dimensions_in.GetValue()}`.'
        wx.MessageBox(msg, 'Info', wx.OK)
        self.create_env_name_in.SetValue('')
        self.create_env_dimensions_in.SetValue('')

    def click_remove_environment(self, _):
        env_name = self.remove_env_name_in.GetValue()
        if env_name == '':
            return

        filled_positions = []
        for position, container_obj in self.backend.completed_dict['container_environments'][env_name].grid.items():
            if container_obj:
                filled_positions.append(f'- {container_obj.plant.name} --> ({position})')
        if filled_positions:
            printable_filled_positions = '\n'.join(filled_positions)
            msg = f'Environment `{self.remove_env_name_in.GetValue()}` could not be removed because the following' \
                  f'grid positions are still occupied by the following plants:\n{printable_filled_positions}\n\n' \
                  f'Please remove the plant(s) from the container environment by navigating to the `Remove Plant` ' \
                  f'tab. Return to this tab and try again once said plants have been successfully removed.'
            self.create_env_name_in.SetValue('')
            wx.MessageBox(msg, 'Info',  wx.OK)
            return

        if env_name in self.backend.completed_dict['container_environments'].keys():
            del self.backend.completed_dict['container_environments'][env_name]
            self.backend.record_complete()
            self.plant_combobox_fix()
            self.env_combobox_fix()

    def plant_combobox_fix(self):
        current_options = list(self.backend.completed_dict['plants'].keys())
        self.remove_plant_name_in.Set(current_options)
        self.move_plant_name_in.Set(current_options)

    def env_combobox_fix(self):
        current_options = list(self.backend.completed_dict['container_environments'].keys())
        self.add_plant_dropdown_environment.Set(current_options)
        self.move_plant_env_dest_in.Set(current_options)
        self.remove_env_name_in.Set(current_options)

    def validate_env_name_unique_create(self, _):
        env_name = self.create_env_name_in.GetValue().lower()
        if env_name in [x.lower() for x in self.backend.completed_dict['container_environments'].keys()]:
            msg = f'Environment name `{self.add_plant_name_in.GetValue()}` already exists. Please try again.'
            self.create_env_name_in.SetValue('')
            wx.MessageBox(msg, 'Info',  wx.OK)

    def validate_plant_name_unique(self, _plant_name):
        if _plant_name in [x.lower() for x in self.backend.completed_dict['plants'].keys()]:
            msg = f'Plant name `{_plant_name}` already exists. Please try again.'
            wx.MessageBox(msg, 'Info', wx.OK)
            return False
        return True

    def validate_environment_name_unique(self, _environment_name):
        if _environment_name in list(self.backend.completed_dict['container_environments'].keys()):
            msg = f'Environment name `{_environment_name}` already exists. Please try again.'
            wx.MessageBox(msg, 'Info', wx.OK)
            return False
        return True

    def populate_envs(self):
        envs = list(self.backend.completed_dict['container_environments'].keys())
        envs.remove(self.move_plant_env_name_in.GetValue())
        self.move_plant_env_dest_in.SetItems(envs)

    @staticmethod
    def pre_post_fix_rows(grid: wx.grid.Grid, df: pd.DataFrame, prefix='', postfix=''):
        for row in range(df.shape[0]):
            grid.SetRowLabelValue(row, f'{prefix}{df.index[row]}{postfix}')

    def elookup_move_page(self, _):
        self.move_plant_env_name_in.SetValue(self.elookup(f'{self.move_plant_name_in.GetValue()}'))
        self.move_plant_env_name_in.SetEditable(False)
        self.populate_envs()

    def plookup_remove_page(self, _):
        self.remove_plant_env_name_in.SetEditable(True)
        self.remove_plant_env_name_in.SetValue(
            vars(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'environment'))['name'])
        self.remove_plant_env_name_in.SetEditable(False)

        self.remove_plant_type_in.SetEditable(True)
        self.remove_plant_type_in.SetValue(
            self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'harvest_type'))
        self.remove_plant_type_in.SetEditable(False)

        self.remove_plant_grow_type_in.SetEditable(True)
        self.remove_plant_grow_type_in.SetValue(
            self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'grow_type'))
        self.remove_plant_grow_type_in.SetEditable(False)

        self.remove_plant_thc_in.SetEditable(True)
        self.remove_plant_thc_in.SetValue(str(
            self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'thc_percentage')))
        self.remove_plant_thc_in.SetEditable(False)

        self.remove_plant_cbd_in.SetEditable(True)
        self.remove_plant_cbd_in.SetValue(
            str(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'cbd_percentage')))
        self.remove_plant_cbd_in.SetEditable(False)

        self.remove_plant_birthday_in.SetEditable(True)
        self.remove_plant_birthday_in.SetValue(
            str(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'birth_date')))
        self.remove_plant_birthday_in.SetEditable(False)

        self.remove_plant_container_name_in.SetEditable(True)
        self.remove_plant_container_name_in.SetValue(
            vars(self.plookup(f'{self.remove_plant_name_in.GetValue()}', 'container'))['dimensions'])
        self.remove_plant_container_name_in.SetEditable(False)

    @staticmethod
    def parse_date(_date_string):
        date_object = parser.parse(_date_string).date()
        return date_object

    @staticmethod
    def get_df_dimensions(df: pd.DataFrame) -> tuple:
        return df.shape[0], df.shape[1]

    @staticmethod
    def rename_columns(grid: wx.grid.Grid, rename_dict: dict):  # Rename column headers
        for col in range(grid.GetNumberCols()):
            current_col_name = grid.GetColLabelValue(col)
            if current_col_name in rename_dict:
                grid.SetColLabelValue(col, rename_dict[current_col_name])

    @staticmethod
    def resize_grid_to_fix_text(grid: wx.grid.Grid, df: pd.DataFrame):
        for col in range(df.shape[1]):
            grid.SetColLabelValue(col, df.columns[col])
            grid.AutoSizeColumn(col)

    @staticmethod
    def add_adjacent_to_sizer(_obj0, _obj1, _vertical_sizer, tab_over=True):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if tab_over:
            sizer.Add((150, 0))
            sizer.Add(_obj0, 0)
            sizer.Add(_obj1, 0)
        else:
            sizer.AddMany([_obj0, _obj1])

        _vertical_sizer.Add(sizer, 1)

    def plookup(self, _plant_name, _parameter):
        return vars(self.backend.completed_dict['plants'][_plant_name])[_parameter]

    def elookup(self, _plant_name):
        decoded_data = vars(self.backend.completed_dict['plants'][_plant_name])
        return vars(decoded_data['environment'])['name']

    def validate_item(self, _in_obj, evaluation_type='string'):
        regex = None
        evaluation_type = evaluation_type.lower()
        types = [str, float, int]
        break_early = True

        if not _in_obj:
            self.known_error = False
            return

        for _type in types:
            if isinstance(_in_obj, _type):
                break_early = False

        if break_early:
            self.known_error = True
            return

        if evaluation_type == 'date':
            if self.validate_date(_in_obj):
                self.known_error = False
            else:
                self.known_error = True
            return

        if evaluation_type == 'string':
            regex = r'^[\w\d\s]{1,250}$'  # Default to string evaluation
        elif evaluation_type == 'percent':
            regex = r'^(100(\.0{1,2})?|[0-9]{1,2}(\.\d{1,2})?)$'
        elif evaluation_type == 'rxd':
            regex = r'(?i)\d+x\d+$'

        if re.match(regex, _in_obj):
            self.known_error = False
        else:
            self.known_error = True

    def validate_all_add_plant(self, _):
        self.known_error = False

        targets = {'add_plant_name': {'value': self.add_plant_name_in, 'type': 'string'},
                   'add_plant_type': {'value': self.add_plant_type_in_dropdown, 'type': 'string'},
                   'add_plant_grow_type': {'value': self.add_plant_grow_type_in_dropdown, 'type': 'string'},
                   'add_plant_thc': {'value': self.add_plant_thc_in, 'type': 'percent'},
                   'add_plant_cbd': {'value': self.add_plant_cbd_in, 'type': 'percent'},
                   'add_plant_birthday': {'value': self.add_plant_birthday_in, 'type': 'date'},
                   'add_plant_container_name': {'value': self.add_plant_container_name_in, 'type': 'rxd'}
                   }

        for _, target_textctrl_obj in targets.items():
            self.validate_item(target_textctrl_obj['value'].GetValue(), target_textctrl_obj['type'])
            if self.known_error:
                self.set_textctrl_background(target_textctrl_obj, set_to_bad=True)
            else:
                self.set_textctrl_background(target_textctrl_obj)

    def validate_all_create_env(self, _):
        self.known_error = False

        targets = {'create_env_name': {'value': self.create_env_name_in, 'type': 'string'},
                   'create_env_dimensions': {'value': self.create_env_dimensions_in, 'type': 'rxd'}
                   }

        for _, target_textctrl_obj in targets.items():
            self.validate_item(target_textctrl_obj['value'].GetValue(), target_textctrl_obj['type'])
            if self.known_error:
                self.set_textctrl_background(target_textctrl_obj, set_to_bad=True)
            else:
                self.set_textctrl_background(target_textctrl_obj)

    @staticmethod
    def validate_date(_date_string):
        try:
            date = parser.parse(_date_string)
            min_date = datetime(2023, 1, 1)  # Can't be older than 2023, even though it is considered a valid date.
            if date >= min_date:
                return True
            else:
                return False
        except ValueError:
            return False

    @staticmethod
    def set_textctrl_background(textctrl_obj, set_to_bad=False):
        textctrl_obj['value'].Refresh()
        textctrl_obj['value'].SetForegroundColour('white')
        if set_to_bad:
            textctrl_obj['value'].SetBackgroundColour('red')
        else:
            textctrl_obj['value'].SetBackgroundColour('clear')

    @staticmethod
    def delete_row_from_grid(_grid, plant_name):
        for row in range(_grid.GetNumberRows()):
            if _grid.GetCellValue(row, 0) == plant_name:
                _grid.DeleteRows(row)
                break

    @staticmethod
    def add_row_to_grid(_grid, values_list):
        current_rows = _grid.GetNumberRows()
        _grid.InsertRows(pos=current_rows)
        for col, value in enumerate(values_list):
            _grid.SetCellValue(current_rows, col, str(value))

    def update_plant_grid_add(self):
        self.backend.record_complete()
        plant_name = self.add_plant_name_in.GetValue()
        prefix = self.backend.completed_dict['plants'][plant_name]
        values = [plant_name, prefix.harvest_type, prefix.environment.name, prefix.grow_type,
                  prefix.thc_percentage, prefix.cbd_percentage, prefix.birth_date, prefix.harvest_date,
                  prefix.bottle_date, prefix.cure_date, prefix.low_cure_date, prefix.mid_cure_date,
                  prefix.high_cure_date, prefix.age_in_weeks, prefix.container.dimensions]
        self.add_row_to_grid(self.plant_grid, values)

    def get_grid_row_index(self, plant_name):
        for row in range(self.plant_grid.GetNumberRows()):
            if self.plant_grid.GetCellValue(row, self.column_index_by_name('name')) == plant_name:
                return row
        return -1

    def column_index_by_name(self, column_name):
        for col in range(self.plant_grid.GetNumberCols()):
            if self.plant_grid.GetColLabelValue(col) == column_name:
                return col
        return -1

    def replace_row_in_grid(self, row_index, values_list):
        for col, value in enumerate(values_list):
            self.plant_grid.SetCellValue(row_index, col, str(value))

    def update_plant_grid_change_env(self):
        self.backend.record_complete()
        plant_name = self.move_plant_name_in.GetValue()
        grid_row_index = self.get_grid_row_index(plant_name)
        prefix = self.backend.completed_dict['plants'][plant_name]
        values = [plant_name, prefix.harvest_type, prefix.environment.name, prefix.grow_type,
                  prefix.thc_percentage, prefix.cbd_percentage, prefix.birth_date, prefix.harvest_date,
                  prefix.bottle_date, prefix.cure_date, prefix.low_cure_date, prefix.mid_cure_date,
                  prefix.high_cure_date, prefix.age_in_weeks, prefix.container.dimensions]
        self.replace_row_in_grid(grid_row_index, values)

    def generate_grid(self, target_df, lock_grid=False):
        out_grid = wx.grid.Grid(self, -1)
        row_size, column_size = self.get_df_dimensions(target_df)
        out_grid.CreateGrid(row_size, column_size)

        for row in range(row_size):  # Populating the created grid with data
            for col in range(column_size):
                out_grid.SetCellValue(row, col, f'{target_df.iloc[row, col]}')
                if lock_grid:
                    out_grid.SetReadOnly(row, col, isReadOnly=True)

        return out_grid


app = wx.App()
frame = MainFrame()
frame.Show()
app.MainLoop()
