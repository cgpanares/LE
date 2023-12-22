import os
import sys
import time
import yaml
import requests
import traceback
import subprocess
from pandas import read_csv
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import * 

#####################IMPORTED FUNCTIONS##########################
from functions.createTemplate import createTemplate
from functions.create_Run_Template import create_Run_Template, findTemplateReport, checkCredentials
from functions.create_Run_Template_WhatIf import create_Run_Template_WhatIf, findTemplateReport_WhatIf, checkCredentials_WI

#####################GLOBAL VARIABLES############################

var_cost_centers = ["CC1", "CC2", "CC3"]
var_production = ["Yes", "No", "Both"]
var_deploy_type = ["2008", "2012", "Both"]
var_service = ["S1", "S2"]
var_account_acc1_region = ["us-east-1", "us-east-2", "us-west-2"]
var_account_acc2_region = ["eu-central-1","us-east-1", "us-east-2"]
var_account_acc3_region = ["ca-central-1", "eu-central-1", "eu-west-2" ,"us-east-1", "us-east-2"]
script_comment = """# Author:
# Script Name:
# Date:
# Jira:
# Action:
# Description:"""
lock = False


class MainWidget(QWidget):
	def __init__(self, parent=None):
		super(MainWidget, self).__init__(parent)
		self.setGeometry(200, 100, 800, 520)
		image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAABcElEQVR42mM4I61EU8QwMiw4K68BRppA9mkJuas2HldtPM/IqVPPAgXNs7Jqp0UlT4tJ347P+nbt5oPK5jPSitSzQE79tLjMOVX9J12T/37+8v////tFtWck5almwWkpxSu2Hu/3Hf4PBv+AFhTUnJFUoF4kS8o/KG34jwTuF9edkVKkqgXlTSgWlDZQ0wdnZVWuugc/65/5tHfas/7pz/pnXHMPOSujTM1UBPTECQHuEwK8EATkggSpmA/Oq+hd1Le6qGd1Sc8ayDinqntWToOKOVnxTmL21yvXP52//PnC5S+Xr91OzKZqUYERyUAuVZOplML9wlpIDvgHSUWgjEbVfHC/sAbFgsKaIWaBAhYLpGhrQS2ViwoaB5EUhg+GQSqibhxIDUgkUzWZKt4vqEa1oJrKqQi9sKugbmEnrXAntfDb7btfrt38ev3Wtxu3b6flU7XZIq9xTs3wsrkTEF0BIjOn82pGZ6nY8BrZjV8AtoThH2QTo+cAAAAASUVORK5CYII=
		"""
		self.icon = self.iconFromBase64(image_icon)
		self.setWindowIcon(self.icon)
		self.setWindowTitle("LE SSM Wrapper Template Creator")
		self.setFixedSize(800, 520)

		fontTitle = QtGui.QFont()
		fontTitle.setBold(True)
		fontTitle.setPointSize(14)

		self.timestr = time.strftime("%Y%m%d-%H%M%S")
		self.timestrlogs = time.strftime("%A, %d %B %Y %I:%M%p %Z")
		self.filename_log = self.timestr + "-attempt"

		try:
			os.mkdir("logs")
		except OSError:
			list_of_files = os.listdir('logs')
			full_path = ["logs/{0}".format(x) for x in list_of_files]
			if len(list_of_files) == 10:
				oldest_file = min(full_path, key=os.path.getctime)
				os.remove(oldest_file)
		sys.stdout = open("logs/" + self.filename_log + ".log", "w")
		print("SSM Wrapper UI - " + self.timestrlogs, flush=True)

	########################ELEMENTS#########################

		self.fn_prefix_lbl = QLabel("Filename Prefix")
		self.fn_prefix_lbl.adjustSize()
		self.fn_prefix_txt = QLineEdit()
		self.fn_prefix_txt.setPlaceholderText("sample1")

		if (self.loadConfigFile("Prefix")):
			value = self.loadConfigFile("Prefix")
			self.fn_prefix_txt.setText(value)

		self.script_path_lbl = QtGui.QLabel("Specify path of created script (Required)")
		self.script_path_lbl.adjustSize()
		self.script_path_txt = QtGui.QLineEdit()
		self.script_path_txt.setPlaceholderText("C:\\Users\\MyName\\MyScripts\\NewScript.ps1")
		self.browse_script = QtGui.QPushButton("Browse...", self)
		self.browse_script.clicked.connect(lambda: self.setLocationFile(self.script_path_txt))
		self.browse_script.resize(self.browse_script.minimumSizeHint())

		if (self.loadConfigFile("CreatedScript")):
			value = self.loadConfigFile("CreatedScript")
			self.script_path_txt.setText(value)

		self.ssm_wrapperloc_lbl = QtGui.QLabel("SSM wrapper location (Required)")
		self.ssm_wrapperloc_lbl.adjustSize()
		self.ssm_wrapperloc_txt = QtGui.QLineEdit()
		self.ssm_wrapperloc_txt.setPlaceholderText("C:\\ssm\\ExecuteSSMWrapper.ps1")
		self.browse_ssm = QtGui.QPushButton("Browse...", self)
		self.browse_ssm.clicked.connect(lambda: self.setLocationFile(self.ssm_wrapperloc_txt))
		self.browse_ssm.resize(self.browse_ssm.minimumSizeHint())

		if (self.loadConfigFile("SSMWrapperLocation")):
			value = self.loadConfigFile("SSMWrapperLocation")
			self.ssm_wrapperloc_txt.setText(value)

		self.output_loc_lbl = QtGui.QLabel("Output location folder")
		self.output_loc_lbl.adjustSize()
		self.output_loc_txt = QtGui.QLineEdit()
		self.output_loc_txt.setPlaceholderText("C:\\Users\\MyName\\Templates")
		self.browse_loc = QtGui.QPushButton("Browse...", self)
		self.browse_loc.clicked.connect(lambda: self.setLocationFolder(self.output_loc_txt))
		self.browse_loc.resize(self.browse_loc.minimumSizeHint())

		if (self.loadConfigFile("OutputLocation")):
			value = self.loadConfigFile("OutputLocation")
			self.output_loc_txt.setText(value)

		self.createBottomLeftGroupBox()
		self.createBottomRightGroupBox()
		self.createBottomGroupBox()

		script_loc_layout = QHBoxLayout()
		script_loc_layout.addWidget(self.script_path_txt)
		script_loc_layout.addWidget(self.browse_script)
		ssm_wrapper_layout = QHBoxLayout()
		ssm_wrapper_layout.addWidget(self.ssm_wrapperloc_txt)
		ssm_wrapper_layout.addWidget(self.browse_ssm)
		output_loc_layout = QHBoxLayout()
		output_loc_layout.addWidget(self.output_loc_txt)
		output_loc_layout.addWidget(self.browse_loc)

		topLeftLayout = QVBoxLayout()
		topLeftLayout.addWidget(self.fn_prefix_lbl)
		topLeftLayout.addWidget(self.fn_prefix_txt)
		topLeftLayout.addWidget(self.script_path_lbl)
		topLeftLayout.addLayout(script_loc_layout)
		topLeftLayout.addStretch(1)
		topRightLayout = QVBoxLayout()
		topRightLayout.addWidget(self.ssm_wrapperloc_lbl)
		topRightLayout.addLayout(ssm_wrapper_layout)
		topRightLayout.addWidget(self.output_loc_lbl)
		topRightLayout.addLayout(output_loc_layout)
		topRightLayout.addStretch(1)

		mainLayout = QGridLayout()
		mainLayout.addLayout(topLeftLayout, 0, 0, 1, 1)
		mainLayout.addLayout(topRightLayout, 0, 1, 1, 1)
		mainLayout.addWidget(self.bottomLeftGroupBox, 1, 0, 2, 1)
		mainLayout.addWidget(self.bottomRightGroupBox, 1, 1, 2, 1)
		mainLayout.addWidget(self.bottomGroupBox, 3, 0, 1, 2)
		mainLayout.setRowStretch(1, 1)
		mainLayout.setRowStretch(2, 1)
		mainLayout.setColumnStretch(0, 1)
		mainLayout.setColumnStretch(1, 1)
		self.setLayout(mainLayout)

	########################LAYOUT FUNCTIONS#########################

	def createBottomLeftGroupBox(self):
		self.bottomLeftGroupBox = QGroupBox("Options")
		self.AllowedInputRegex = QRegExp("^[A-Z0-9 ,]*$")
		self.UpperCaseValidator = QRegExpValidator(self.AllowedInputRegex)


		self.ServiceGroupBox = QGroupBox("Service")
		self.ServiceGroupBox.setLayout(QtGui.QVBoxLayout())

		self.CostCenterGroupBox = QGroupBox("Cost Centers")
		#self.CostCenterGroupBox.setCheckable(True)
		self.CostCenterGroupBox.toggled.connect(self.onToggled)
		self.CostCenterGroupBox.setLayout(QtGui.QVBoxLayout())

		self.instance_id_lbl = QtGui.QLabel("Instance IDs")
		self.instance_id_lbl.adjustSize()
		self.instance_id_txt = QtGui.QLineEdit()
		self.instance_id_txt.setPlaceholderText("i-03f324sd3, i-132erd32")
		self.instance_id_txt.textChanged.connect(self.disableTextBox2)

		self.mach_label_lbl = QtGui.QLabel("Machine Labels")
		self.mach_label_lbl.adjustSize()
		self.mach_label_txt = QtGui.QLineEdit()
		self.mach_label_txt.setPlaceholderText("INFOCOMP1, INFOCOMP2")
		self.mach_label_txt.setValidator(self.UpperCaseValidator)
		self.mach_label_txt.textChanged.connect(self.disableTextBox)

		self.cust_prefix_lbl = QtGui.QLabel("Customer Prefix")
		self.cust_prefix_lbl.adjustSize()
		self.cust_prefix_txt = QtGui.QLineEdit()
		self.cust_prefix_txt.setPlaceholderText("leopprd")
		self.cust_prefix_txt.textChanged.connect(self.disableTextBox)

		self.wrapper_timeout_lbl = QtGui.QLabel("Timeout/ExecutionTimeout")
		self.wrapper_timeout_lbl.adjustSize()
		self.wrapper_timeout_txt = QtGui.QLineEdit()
		self.wrapper_timeout_txt.setPlaceholderText("240")
		self.wrapper_timeout_txt.setValidator(QIntValidator())

		if (self.loadConfigFile("WrapperTimeout")):
			value = self.loadConfigFile("WrapperTimeout")
			self.wrapper_timeout_txt.setText(value)


		if (self.loadConfigFile("InstanceID")):
			value = self.loadConfigFile("InstanceID")
			self.instance_id_txt.setText(','.join(str(x) for x in value))
			self.mach_label_txt.setEnabled(False)
			self.cust_prefix_txt.setEnabled(False)
			self.ServiceGroupBox.setEnabled(False)
			self.CostCenterGroupBox.setEnabled(False)

		if (self.loadConfigFile("MachineLabel")):
			value = self.loadConfigFile("MachineLabel")
			self.mach_label_txt.setText(','.join(str(x) for x in value))
			self.instance_id_txt.setEnabled(False)
			self.ServiceGroupBox.setEnabled(False)

		if (self.loadConfigFile("CustomerPrefix")):
			value = self.loadConfigFile("CustomerPrefix")
			self.cust_prefix_txt.setText(','.join(str(x) for x in value))
			self.instance_id_txt.setEnabled(False)

		if (self.loadConfigFile("CostCenter")):
			var_cost_centers_selected = self.loadConfigFile("CostCenter")
			for i, v in enumerate(var_cost_centers):
				if (var_cost_centers[i] in var_cost_centers_selected):
					var_cost_centers[i] = QCheckBox(v)
					var_cost_centers[i].setChecked(True)
					self.CostCenterGroupBox.layout().addWidget(var_cost_centers[i])
				else:
					var_cost_centers[i] = QCheckBox(v)
					self.CostCenterGroupBox.layout().addWidget(var_cost_centers[i])
		else:
			for i, v in enumerate(var_cost_centers):
				var_cost_centers[i] = QCheckBox(v)
				self.CostCenterGroupBox.layout().addWidget(var_cost_centers[i])

		self.ProductionGroupBox = QGroupBox("Production")
		self.ProductionGroupBox.setLayout(QtGui.QVBoxLayout())

		if (self.loadConfigFile("Production")):
			var_production_selected = self.loadConfigFile("Production")
			for i, v in enumerate(var_production):
				if (var_production[i] in var_production_selected):
					var_production[i] = QRadioButton(v)
					var_production[i].setChecked(True)
					self.ProductionGroupBox.layout().addWidget(var_production[i])
				else:
					var_production[i] = QRadioButton(v)
					self.ProductionGroupBox.layout().addWidget(var_production[i])
		else:
			for i, v in enumerate(var_production):
				var_production[i] = QRadioButton(v)
				self.ProductionGroupBox.layout().addWidget(var_production[i])


		self.DeployTypeGroupBox = QGroupBox("Deployment Type")
		self.DeployTypeGroupBox.setLayout(QtGui.QVBoxLayout())

		if (self.loadConfigFile("DeploymentType")):
			var_deploy_type_selected = self.loadConfigFile("DeploymentType")
			for i, v in enumerate(var_deploy_type):
				if (var_deploy_type[i] in var_deploy_type_selected):
					var_deploy_type[i] = QRadioButton(v)
					var_deploy_type[i].setChecked(True)
					self.DeployTypeGroupBox.layout().addWidget(var_deploy_type[i])
				else:
					var_deploy_type[i] = QRadioButton(v)
					self.DeployTypeGroupBox.layout().addWidget(var_deploy_type[i])
		else:
			for i, v in enumerate(var_deploy_type):
				var_deploy_type[i] = QRadioButton(v)
				self.DeployTypeGroupBox.layout().addWidget(var_deploy_type[i])

		if (self.loadConfigFile("Service")):
			var_service_selected = self.loadConfigFile("Service")
			for i, v in enumerate(var_service):
				if (var_service[i] in var_service_selected):
					var_service[i] = QCheckBox(v)
					var_service[i].setChecked(True)
					self.ServiceGroupBox.layout().addWidget(var_service[i])
				else:
					var_service[i] = QCheckBox(v)
					self.ServiceGroupBox.layout().addWidget(var_service[i])
		else:
			for i, v in enumerate(var_service):
				var_service[i] = QCheckBox(v)
				self.ServiceGroupBox.layout().addWidget(var_service[i])

		layout = QGridLayout()
		layout.addWidget(self.instance_id_lbl)
		layout.addWidget(self.instance_id_txt)
		layout.addWidget(self.mach_label_lbl)
		layout.addWidget(self.mach_label_txt)
		layout.addWidget(self.cust_prefix_lbl)
		layout.addWidget(self.cust_prefix_txt)
		layout.addWidget(self.wrapper_timeout_lbl)
		layout.addWidget(self.wrapper_timeout_txt)
		layout.addWidget(self.CostCenterGroupBox, 8, 0, 15, 1)
		layout.addWidget(self.ProductionGroupBox, 0, 1, 5, 2)
		layout.addWidget(self.DeployTypeGroupBox, 5, 1, 6, 2)
		layout.addWidget(self.ServiceGroupBox, 11, 1, 12, 3)
		self.bottomLeftGroupBox.setLayout(layout)    

	def createBottomRightGroupBox(self):
		self.bottomRightGroupBox = QGroupBox("Accounts (Required at least one account with check)")

		self.Accountacc1GroupBox = QGroupBox("acc1")
		self.Accountacc1GroupBox.setLayout(QtGui.QVBoxLayout())

		if (self.loadConfigFile("acc1_region")):
			var_account_acc1_region_selected = self.loadConfigFile("acc1_region")
			for i, v in enumerate(var_account_acc1_region):
				if (var_account_acc1_region[i] in var_account_acc1_region_selected):
					var_account_acc1_region[i] = QCheckBox(v)
					var_account_acc1_region[i].setChecked(True)
					self.Accountacc1GroupBox.layout().addWidget(var_account_acc1_region[i])
				else:
					var_account_acc1_region[i] = QCheckBox(v)
					self.Accountacc1GroupBox.layout().addWidget(var_account_acc1_region[i])
		else:
			for i, v in enumerate(var_account_acc1_region):
				var_account_acc1_region[i] = QCheckBox(v)
				self.Accountacc1GroupBox.layout().addWidget(var_account_acc1_region[i])

		self.Accountacc2GroupBox = QGroupBox("acc2")
		self.Accountacc2GroupBox.setLayout(QtGui.QVBoxLayout())

		if (self.loadConfigFile("acc2_region")):
			var_account_acc2_region_selected = self.loadConfigFile("acc2_region")
			for i, v in enumerate(var_account_acc2_region):
				if (var_account_acc2_region[i] in var_account_acc2_region_selected):
					var_account_acc2_region[i] = QCheckBox(v)
					var_account_acc2_region[i].setChecked(True)
					self.Accountacc2GroupBox.layout().addWidget(var_account_acc2_region[i])
				else:
					var_account_acc2_region[i] = QCheckBox(v)
					self.Accountacc2GroupBox.layout().addWidget(var_account_acc2_region[i])
		else:
			for i, v in enumerate(var_account_acc2_region):
				var_account_acc2_region[i] = QCheckBox(v)
				self.Accountacc2GroupBox.layout().addWidget(var_account_acc2_region[i])

		self.Accountacc3GroupBox = QGroupBox("acc3")
		self.Accountacc3GroupBox.setLayout(QtGui.QVBoxLayout())

		if (self.loadConfigFile("acc3_region")):
			var_account_acc3_region_selected = self.loadConfigFile("acc3_region")
			for i, v in enumerate(var_account_acc3_region):
				if (var_account_acc3_region[i] in var_account_acc3_region_selected):
					var_account_acc3_region[i] = QCheckBox(v)
					var_account_acc3_region[i].setChecked(True)
					self.Accountacc3GroupBox.layout().addWidget(var_account_acc3_region[i])
				else:
					var_account_acc3_region[i] = QCheckBox(v)
					self.Accountacc3GroupBox.layout().addWidget(var_account_acc3_region[i])
		else:
			for i, v in enumerate(var_account_acc3_region):
				var_account_acc3_region[i] = QCheckBox(v)
				self.Accountacc3GroupBox.layout().addWidget(var_account_acc3_region[i])

		layout = QGridLayout()
		layout.addWidget(self.Accountacc1GroupBox)
		layout.addWidget(self.Accountacc2GroupBox)
		layout.addWidget(self.Accountacc3GroupBox, 0, 1, 2, 1)
		self.bottomRightGroupBox.setLayout(layout)

	def createBottomGroupBox(self):
		self.bottomGroupBox = QGroupBox()

		self.create_temp = QtGui.QPushButton("Create Template", self)
		self.create_temp.clicked.connect(self.ct)
		self.create_temp.resize(self.create_temp.minimumSizeHint())

		self.create_run_temp = QtGui.QPushButton("Create and Run Template", self)
		self.create_run_temp.clicked.connect(self.crt)
		self.create_run_temp.resize(self.create_run_temp.minimumSizeHint())

		self.create_run_temp_whatif = QtGui.QPushButton("Create and Run Template (What If)", self)
		self.create_run_temp_whatif.clicked.connect(self.crt_whatif)
		self.create_run_temp_whatif.resize(self.create_run_temp_whatif.minimumSizeHint())

		self.clr_all_fld = QtGui.QPushButton("Clear All Fields", self)
		self.clr_all_fld.clicked.connect(self.clear_all_fields)
		self.clr_all_fld.resize(self.clr_all_fld.minimumSizeHint())

		self.edit_headers = QtGui.QPushButton("Edit Headers", self)
		self.edit_headers.clicked.connect(self.commentWindow)
		self.edit_headers.resize(self.edit_headers.minimumSizeHint())

		self.import_csv = QtGui.QPushButton("Import CSV", self)
		self.import_csv.clicked.connect(lambda: self.importCSV(self.filename_log))
		self.import_csv.resize(self.import_csv.minimumSizeHint())

		self.hlp = QtGui.QPushButton("Help", self)
		self.hlp.clicked.connect(self.helpWindow)
		self.hlp.resize(self.hlp.minimumSizeHint())
		help_image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAABmJLR0QA/wD/AP+gvaeTAAABoElEQVRIie2WzU4CMRDHfxrjTQ8kxC8kfiS+ihEVMcSzD2DAiy/ikagX0Ys3DT6Cr2DwIDHgyZt4MFFYPLQbSoPtFIjxwD+Z7G53pr9Od7YtjPVHmgjwTQN7wDawAqR0+yvwAlSAW6AxqsEtASWgBXQ81gZu9MCGUg74EABtawLZQaHHqAxCoWb2xVBobkioCRdnnsI9vXUgD8xo2weqDv8msCgBX3igiT4xCVQ1/xZ35oOmcVdvXvtlNKgBbOm2A0dci+7v11cFR3AHNbVY2dV126wn9sgETVrgjGtUqO/VsUYf6eu0J7anbxu85gm29Qkc6vtNj++662WckcS+UMsnwDzu4oqreyTgEx0zBzwK/J3gpwBwUsc8CP2rJmjKAteADdfIDL0J/WI9mw92cd0HdhaiiuvlMvLtr6wtEvh/41lAAM4FHZUN/yuBf8kHBbXx+6o7BPwOLEjAoLYy17YYaeA17qluA7tSaKyiBy6pg0IoNFaWsEXFnN6dQaGxksApqjIlWV4i+KYhx9sU3ePtKr3H2xpqDbjTz2P9H/0AJ/xJq47cBwgAAAAASUVORK5CYII=
		"""
		self.help_icon = self.iconFromBase64(help_image_icon)
		self.hlp.setIcon(self.help_icon)

		layout = QGridLayout()
		layout.addWidget(self.create_temp, 0, 1)
		layout.addWidget(self.create_run_temp, 0, 2)
		layout.addWidget(self.create_run_temp_whatif, 0, 3)
		layout.addWidget(self.edit_headers, 0, 4)
		layout.addWidget(self.import_csv, 0, 5)
		layout.addWidget(self.clr_all_fld, 0, 6)
		layout.addWidget(self.hlp, 0, 7)
		self.bottomGroupBox.setLayout(layout)

	def onToggled(self, on):
		for box in self.sender().findChildren(QtGui.QCheckBox):
			box.setChecked(on)
			box.setEnabled(True)

	def checkboxChanged(self, lists):
		try:
			temp_list = []
			for i, v in enumerate(lists):
				if (v.isChecked() and v.isEnabled()):
					temp_list.append(lists[i].text())
			return temp_list
		except Exception as e:
			return False

	def setLocationFile(self, textBoxName):
		fileName = QFileDialog.getOpenFileName(self, "Select File", "", "Powershell Scripts (*.ps1)")
		if fileName != "":
			textBoxName.setText(str(os.path.normpath(fileName)))

	def setLocationFolder(self, textBoxName):
		fileName = QFileDialog.getExistingDirectory(self, "Select Folder")
		if fileName != "":
			textBoxName.setText(str(fileName))

	def iconFromBase64(self, base64):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64))
		icon = QtGui.QIcon(pixmap)
		return icon

	def putTextinList(self, text):
		try:
			if ((text.text() != "") and text.isEnabled()):
				temp_list = text.text().replace(" ", "").split(",")
			return temp_list
		except Exception as e:
			return False

	def putCommentinList(self, comment):
		try:
			if ((comment != "")):
				temp_list = comment.split("\n")
			return temp_list
		except Exception as e:
			return False

	########################MAIN FUNCTIONS#########################

	def ct(self):
		try:
			chosen_option = "CT"

			instance_id = self.putTextinList(self.instance_id_txt)
			machine_label = self.putTextinList(self.mach_label_txt)
			customer_prefix = self.putTextinList(self.cust_prefix_txt)
			cost_center_list = self.checkboxChanged(var_cost_centers)
			production_list = self.checkboxChanged(var_production)
			deploytype_list = self.checkboxChanged(var_deploy_type)
			service_list = self.checkboxChanged(var_service)

			acc1_region_list = self.checkboxChanged(var_account_acc1_region)
			acc2_region_list = self.checkboxChanged(var_account_acc2_region)
			acc3_region_list = self.checkboxChanged(var_account_acc3_region)

			final_comment = self.putCommentinList(script_comment)

			if ( (self.script_path_txt.text() != "") and (self.ssm_wrapperloc_txt.text() != "") and ((acc1_region_list) or (acc2_region_list) or (acc3_region_list)) ):

				if(self.wrapper_timeout_txt.text() == ""):
					self.wrapper_timeout_txt.setText("240")
				
				yaml_dict = {}
				self.addElementToDict(yaml_dict, "Prefix", self.fn_prefix_txt.text())
				self.addElementToDict(yaml_dict, "CreatedScript", self.script_path_txt.text())
				self.addElementToDict(yaml_dict, "SSMWrapperLocation", self.ssm_wrapperloc_txt.text())
				self.addElementToDict(yaml_dict, "OutputLocation", self.output_loc_txt.text())
				self.addElementToDict(yaml_dict, "InstanceID", instance_id)
				self.addElementToDict(yaml_dict, "MachineLabel", machine_label)
				self.addElementToDict(yaml_dict, "CustomerPrefix", customer_prefix)
				self.addElementToDict(yaml_dict, "WrapperTimeout", self.wrapper_timeout_txt.text())
				self.addElementToDict(yaml_dict, "CostCenter", cost_center_list)
				self.addElementToDict(yaml_dict, "Production", production_list)
				self.addElementToDict(yaml_dict, "DeploymentType", deploytype_list)
				self.addElementToDict(yaml_dict, "Service", service_list)
				self.addElementToDict(yaml_dict, "acc1_region", acc1_region_list)
				self.addElementToDict(yaml_dict, "acc2_region", acc2_region_list)
				self.addElementToDict(yaml_dict, "acc3_region", acc3_region_list)
				self.addElementToDict(yaml_dict, "ScriptComment", final_comment)

				with open("config.yaml", "w") as x:
					yaml.dump(yaml_dict, x)

				#Production List Radio Button Pre-processed data
				if ((bool(production_list) == False)):
					production_list = False
				elif ((bool(production_list)) and (production_list[0] != 'Both')):
					for x in production_list[0].split():
						production_list[0] = x[0]
				else:
					production_list = False

				#Deployment Type List Radio Button Pre-processed data
				if ((bool(deploytype_list) == False)):
					deploytype_list = False
				elif (deploytype_list[0] == 'Both'):
					deploytype_list = False

				self.ProcessWindow = ProcessWidget(chosen_option, self.filename_log, prefix=self.fn_prefix_txt.text(), cs=self.script_path_txt.text(), ssml=self.ssm_wrapperloc_txt.text(), ol=self.output_loc_txt.text(), et=self.wrapper_timeout_txt.text(), sc=script_comment, iid=instance_id, ml=machine_label, cp=customer_prefix, wt=self.wrapper_timeout_txt.text(), cc=cost_center_list, pl=production_list, dl=deploytype_list, sl=service_list, acc1l=acc1_region_list, acc2l=acc2_region_list, acc3l=acc3_region_list)
				self.ProcessWindow.displayWindow()
			else:
				popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
					"Warning",
					"All fields and options that are required must have input!",
					QtGui.QMessageBox.Ok,
					self)
				popup.show()
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)

	def crt(self):
		try:
			chosen_option = "CRT"

			instance_id = self.putTextinList(self.instance_id_txt)
			machine_label = self.putTextinList(self.mach_label_txt)
			customer_prefix = self.putTextinList(self.cust_prefix_txt)
			cost_center_list = self.checkboxChanged(var_cost_centers)
			production_list = self.checkboxChanged(var_production)
			deploytype_list = self.checkboxChanged(var_deploy_type)
			service_list = self.checkboxChanged(var_service)

			acc1_region_list = self.checkboxChanged(var_account_acc1_region)
			acc2_region_list = self.checkboxChanged(var_account_acc2_region)
			acc3_region_list = self.checkboxChanged(var_account_acc3_region)

			final_comment = self.putCommentinList(script_comment)

			if ( (self.script_path_txt.text() != "") and (self.ssm_wrapperloc_txt.text() != "") and ((acc1_region_list) or (acc2_region_list) or (acc3_region_list)) ):
				
				message_box = QtGui.QMessageBox
				popup = message_box.question(self, '', "Are you sure you want to create and run the template?\n(WhatIf: Disabled)", message_box.Yes | message_box.No)
				if popup == message_box.Yes:

					if(self.wrapper_timeout_txt.text() == ""):
						self.wrapper_timeout_txt.setText("240")

					yaml_dict = {}
					self.addElementToDict(yaml_dict, "Prefix", self.fn_prefix_txt.text())
					self.addElementToDict(yaml_dict, "CreatedScript", self.script_path_txt.text())
					self.addElementToDict(yaml_dict, "SSMWrapperLocation", self.ssm_wrapperloc_txt.text())
					self.addElementToDict(yaml_dict, "OutputLocation", self.output_loc_txt.text())
					self.addElementToDict(yaml_dict, "InstanceID", instance_id)
					self.addElementToDict(yaml_dict, "MachineLabel", machine_label)
					self.addElementToDict(yaml_dict, "CustomerPrefix", customer_prefix)
					self.addElementToDict(yaml_dict, "WrapperTimeout", self.wrapper_timeout_txt.text())
					self.addElementToDict(yaml_dict, "CostCenter", cost_center_list)
					self.addElementToDict(yaml_dict, "Production", production_list)
					self.addElementToDict(yaml_dict, "DeploymentType", deploytype_list)
					self.addElementToDict(yaml_dict, "Service", service_list)
					self.addElementToDict(yaml_dict, "acc1_region", acc1_region_list)
					self.addElementToDict(yaml_dict, "acc2_region", acc2_region_list)
					self.addElementToDict(yaml_dict, "acc3_region", acc3_region_list)
					self.addElementToDict(yaml_dict, "ScriptComment", final_comment)

					with open("config.yaml", "w") as x:
						yaml.dump(yaml_dict, x)

					#Production List Radio Button Pre-processed data
					if ((bool(production_list) == False)):
						production_list = False
					elif ((bool(production_list)) and (production_list[0] != 'Both')):
						for x in production_list[0].split():
							production_list[0] = x[0]
					else:
						production_list = False

					#Deployment Type List Radio Button Pre-processed data
					if ((bool(deploytype_list) == False)):
						deploytype_list = False
					elif (deploytype_list[0] == 'Both'):
						deploytype_list = False

					self.ProcessWindow = ProcessWidget(chosen_option, self.filename_log, prefix=self.fn_prefix_txt.text(), cs=self.script_path_txt.text(), ssml=self.ssm_wrapperloc_txt.text(), ol=self.output_loc_txt.text(), et=self.wrapper_timeout_txt.text(), sc=script_comment, iid=instance_id, ml=machine_label, cp=customer_prefix, wt=self.wrapper_timeout_txt.text(), cc=cost_center_list, pl=production_list, dl=deploytype_list, sl=service_list, acc1l=acc1_region_list, acc2l=acc2_region_list, acc3l=acc3_region_list)
					self.ProcessWindow.displayWindow()
			else:
				popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
					"Warning",
					"All fields and options that are required must have input!",
					QtGui.QMessageBox.Ok,
					self)
				popup.show()
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)

	def crt_whatif(self):
		try:
			chosen_option = "CRT_WhatIf"

			instance_id = self.putTextinList(self.instance_id_txt)
			machine_label = self.putTextinList(self.mach_label_txt)
			customer_prefix = self.putTextinList(self.cust_prefix_txt)
			cost_center_list = self.checkboxChanged(var_cost_centers)
			production_list = self.checkboxChanged(var_production)
			deploytype_list = self.checkboxChanged(var_deploy_type)
			service_list = self.checkboxChanged(var_service)

			acc1_region_list = self.checkboxChanged(var_account_acc1_region)
			acc2_region_list = self.checkboxChanged(var_account_acc2_region)
			acc3_region_list = self.checkboxChanged(var_account_acc3_region)

			final_comment = self.putCommentinList(script_comment)

			if ( (self.script_path_txt.text() != "") and (self.ssm_wrapperloc_txt.text() != "") and ((acc1_region_list) or (acc2_region_list) or (acc3_region_list)) ):
				
				message_box = QtGui.QMessageBox
				popup = message_box.question(self, '', "Are you sure you want to create and run the template?\n(WhatIf: Enabled)", message_box.Yes | message_box.No)
				if popup == message_box.Yes:

					if(self.wrapper_timeout_txt.text() == ""):
						self.wrapper_timeout_txt.setText("240")

					yaml_dict = {}
					self.addElementToDict(yaml_dict, "Prefix", self.fn_prefix_txt.text())
					self.addElementToDict(yaml_dict, "CreatedScript", self.script_path_txt.text())
					self.addElementToDict(yaml_dict, "SSMWrapperLocation", self.ssm_wrapperloc_txt.text())
					self.addElementToDict(yaml_dict, "OutputLocation", self.output_loc_txt.text())
					self.addElementToDict(yaml_dict, "InstanceID", instance_id)
					self.addElementToDict(yaml_dict, "MachineLabel", machine_label)
					self.addElementToDict(yaml_dict, "CustomerPrefix", customer_prefix)
					self.addElementToDict(yaml_dict, "WrapperTimeout", self.wrapper_timeout_txt.text())
					self.addElementToDict(yaml_dict, "CostCenter", cost_center_list)
					self.addElementToDict(yaml_dict, "Production", production_list)
					self.addElementToDict(yaml_dict, "DeploymentType", deploytype_list)
					self.addElementToDict(yaml_dict, "Service", service_list)
					self.addElementToDict(yaml_dict, "acc1_region", acc1_region_list)
					self.addElementToDict(yaml_dict, "acc2_region", acc2_region_list)
					self.addElementToDict(yaml_dict, "acc3_region", acc3_region_list)
					self.addElementToDict(yaml_dict, "ScriptComment", final_comment)

					with open("config.yaml", "w") as x:
						yaml.dump(yaml_dict, x)

						#Production List Radio Button Pre-processed data
					if ((bool(production_list) == False)):
						production_list = False
					elif ((bool(production_list)) and (production_list[0] != 'Both')):
						for x in production_list[0].split():
							production_list[0] = x[0]
					else:
						production_list = False

					#Deployment Type List Radio Button Pre-processed data
					if ((bool(deploytype_list) == False)):
						deploytype_list = False
					elif (deploytype_list[0] == 'Both'):
						deploytype_list = False

					self.ProcessWindow = ProcessWidget(chosen_option, self.filename_log, prefix=self.fn_prefix_txt.text(), cs=self.script_path_txt.text(), ssml=self.ssm_wrapperloc_txt.text(), ol=self.output_loc_txt.text(), et=self.wrapper_timeout_txt.text(), sc=script_comment, iid=instance_id, ml=machine_label, cp=customer_prefix, wt=self.wrapper_timeout_txt.text(), cc=cost_center_list, pl=production_list, dl=deploytype_list, sl=service_list, acc1l=acc1_region_list, acc2l=acc2_region_list, acc3l=acc3_region_list)
					self.ProcessWindow.displayWindow()
			else:
				popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
					"Warning",
					"All fields and options that are required must have input!",
					QtGui.QMessageBox.Ok,
					self)
				popup.show()
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)

	def clear_all_fields(self):
		try:
			self.fn_prefix_txt.setText("")
			self.script_path_txt.setText("")
			self.ssm_wrapperloc_txt.setText("")
			self.output_loc_txt.setText("")
			self.instance_id_txt.setText("")
			self.mach_label_txt.setText("")
			self.cust_prefix_txt.setText("")
			self.wrapper_timeout_txt.setText("")

			#Production
			for i, v in enumerate(var_production):
				var_production[i].setAutoExclusive(False)
				var_production[i].setChecked(False)
				var_production[i].setAutoExclusive(True)
			#Deployment Type
			for i, v in enumerate(var_deploy_type):
				var_deploy_type[i].setAutoExclusive(False)
				var_deploy_type[i].setChecked(False)
				var_deploy_type[i].setAutoExclusive(True)
			
			#Cost Center
			for i, v in enumerate(var_cost_centers):
				var_cost_centers[i].setChecked(False)

			#Service
			for i, v in enumerate(var_service):
				var_service[i].setChecked(False)

			#acc1
			for i, v in enumerate(var_account_acc1_region):
				var_account_acc1_region[i].setChecked(False)
			#acc2
			for i, v in enumerate(var_account_acc2_region):
				var_account_acc2_region[i].setChecked(False)
			#acc3
			for i, v in enumerate(var_account_acc3_region):
				var_account_acc3_region[i].setChecked(False)
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)

	#####################ADDITIONAL FUNCTIONS#######################

	def helpWindow(self):
		self.helpWindow = HelpWidget()
		self.helpWindow.displayWindow()

	def commentWindow(self):
		self.commentWindow = CommentWidget()
		self.commentWindow.displayWindow()

	def importCSV(self, filename_log):
		self.importCSVwindow = ImportCSVWidget()
		self.importCSVwindow.displayWindow(filename_log)

	def closeEvent(self, event):
		app = QtGui.QApplication.instance()
		app.closeAllWindows()
		sys.stdout.close()

	def loadConfigFile(self, element):
		try:
			if(os.path.isfile("config.yaml")):
				config_file = open("config.yaml")
				data = yaml.safe_load(config_file)
			return data[element]
		except Exception as e:
			return False

	def addElementToDict(self, temp_dict, new_key, new_value):
		if(bool(new_value)):
			temp_dict[new_key] = new_value

	def disableTextBox2(self):
		if (self.instance_id_txt.text() != ""):
			self.mach_label_txt.setEnabled(False)
			self.cust_prefix_txt.setEnabled(False)
			self.ServiceGroupBox.setEnabled(False)
			self.CostCenterGroupBox.setEnabled(False)
		else:
			self.mach_label_txt.setEnabled(True)
			self.cust_prefix_txt.setEnabled(True)
			self.ServiceGroupBox.setEnabled(True)
			self.CostCenterGroupBox.setEnabled(True)

	def disableTextBox(self):
		if ( (self.mach_label_txt.text() != "") or (self.cust_prefix_txt.text() != "") ):
			self.instance_id_txt.setEnabled(False)
		else:
			self.instance_id_txt.setEnabled(True)

		if (self.mach_label_txt.text() != ""):
			self.ServiceGroupBox.setEnabled(False)
		else:
			self.ServiceGroupBox.setEnabled(True)

class ImportCSVWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setGeometry(300, 200, 600, 400)
		image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAABcElEQVR42mM4I61EU8QwMiw4K68BRppA9mkJuas2HldtPM/IqVPPAgXNs7Jqp0UlT4tJ347P+nbt5oPK5jPSitSzQE79tLjMOVX9J12T/37+8v////tFtWck5almwWkpxSu2Hu/3Hf4PBv+AFhTUnJFUoF4kS8o/KG34jwTuF9edkVKkqgXlTSgWlDZQ0wdnZVWuugc/65/5tHfas/7pz/pnXHMPOSujTM1UBPTECQHuEwK8EATkggSpmA/Oq+hd1Le6qGd1Sc8ayDinqntWToOKOVnxTmL21yvXP52//PnC5S+Xr91OzKZqUYERyUAuVZOplML9wlpIDvgHSUWgjEbVfHC/sAbFgsKaIWaBAhYLpGhrQS2ViwoaB5EUhg+GQSqibhxIDUgkUzWZKt4vqEa1oJrKqQi9sKugbmEnrXAntfDb7btfrt38ev3Wtxu3b6flU7XZIq9xTs3wsrkTEF0BIjOn82pGZ6nY8BrZjV8AtoThH2QTo+cAAAAASUVORK5CYII=
		"""
		self.icon = self.iconFromBase64(image_icon)
		self.setWindowIcon(self.icon)
		self.setWindowTitle("Create Template from CSV results")
		self.setFixedSize(400, 280)

		layout = QVBoxLayout()

		self.fn_prefix_lbl = QLabel("Filename Prefix")
		self.fn_prefix_lbl.adjustSize()
		self.fn_prefix_txt = QLineEdit()
		self.fn_prefix_txt.setPlaceholderText("sample1")

		self.script_path_lbl = QtGui.QLabel("Specify path of created script (Required)")
		self.script_path_lbl.adjustSize()
		self.script_path_txt = QtGui.QLineEdit()
		self.script_path_txt.setPlaceholderText("C:\\Users\\MyName\\MyScripts\\NewScript.ps1")
		self.browse_script = QtGui.QPushButton("Browse...", self)
		self.browse_script.clicked.connect(lambda: self.setLocationFile(self.script_path_txt))
		self.browse_script.resize(self.browse_script.minimumSizeHint())

		self.ssm_wrapperloc_lbl = QtGui.QLabel("SSM wrapper location (Required)")
		self.ssm_wrapperloc_lbl.adjustSize()
		self.ssm_wrapperloc_txt = QtGui.QLineEdit()
		self.ssm_wrapperloc_txt.setPlaceholderText("C:\\ssm\\ExecuteSSMWrapper.ps1")
		self.browse_ssm = QtGui.QPushButton("Browse...", self)
		self.browse_ssm.clicked.connect(lambda: self.setLocationFile(self.ssm_wrapperloc_txt))
		self.browse_ssm.resize(self.browse_ssm.minimumSizeHint())

		if (self.loadConfigFile("SSMWrapperLocation")):
			value = self.loadConfigFile("SSMWrapperLocation")
			self.ssm_wrapperloc_txt.setText(value)

		self.output_loc_lbl = QtGui.QLabel("Output location folder")
		self.output_loc_lbl.adjustSize()
		self.output_loc_txt = QtGui.QLineEdit()
		self.output_loc_txt.setPlaceholderText("C:\\Users\\MyName\\Templates")
		self.browse_loc = QtGui.QPushButton("Browse...", self)
		self.browse_loc.clicked.connect(lambda: self.setLocationFolder(self.output_loc_txt))
		self.browse_loc.resize(self.browse_loc.minimumSizeHint())

		if (self.loadConfigFile("OutputLocation")):
			value = self.loadConfigFile("OutputLocation")
			self.output_loc_txt.setText(value)

		self.csv_path_lbl = QtGui.QLabel("Specify CSV File")
		self.csv_path_lbl.adjustSize()
		self.csv_path_txt = QtGui.QLineEdit()
		self.csv_path_txt.setPlaceholderText("C:\\Users\\MyName\\MyFolder\\output.csv")
		self.browse_csv = QtGui.QPushButton("Browse...", self)
		self.browse_csv.clicked.connect(lambda: self.setCSVFile(self.csv_path_txt))
		self.browse_csv.resize(self.browse_csv.minimumSizeHint())

		button_layout = QHBoxLayout()

		self.create_temp = QtGui.QPushButton("Create Template", self)
		self.create_temp.clicked.connect(self.ct)
		self.create_temp.resize(self.create_temp.minimumSizeHint())

		self.create_run_temp = QtGui.QPushButton("Create and Run Template", self)
		self.create_run_temp.clicked.connect(self.crt)
		self.create_run_temp.resize(self.create_run_temp.minimumSizeHint())

		button_layout.addWidget(self.create_temp)
		button_layout.addWidget(self.create_run_temp)

		script_loc_layout = QHBoxLayout()
		script_loc_layout.addWidget(self.script_path_txt)
		script_loc_layout.addWidget(self.browse_script)
		ssm_wrapper_layout = QHBoxLayout()
		ssm_wrapper_layout.addWidget(self.ssm_wrapperloc_txt)
		ssm_wrapper_layout.addWidget(self.browse_ssm)
		output_loc_layout = QHBoxLayout()
		output_loc_layout.addWidget(self.output_loc_txt)
		output_loc_layout.addWidget(self.browse_loc)
		csv_loc_layout = QHBoxLayout()
		csv_loc_layout.addWidget(self.csv_path_txt)
		csv_loc_layout.addWidget(self.browse_csv)

		layout.addWidget(self.fn_prefix_lbl)
		layout.addWidget(self.fn_prefix_txt)
		layout.addWidget(self.script_path_lbl)
		layout.addLayout(script_loc_layout)
		layout.addWidget(self.ssm_wrapperloc_lbl)
		layout.addLayout(ssm_wrapper_layout)
		layout.addWidget(self.output_loc_lbl)
		layout.addLayout(output_loc_layout)
		layout.addWidget(self.csv_path_lbl)
		layout.addLayout(csv_loc_layout)
		layout.addLayout(button_layout)
		layout.addStretch(1)

		self.setLayout(layout)

	def displayWindow(self, filename_log):
		self.show()
		self.filename_log = filename_log

	def iconFromBase64(self, base64):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64))
		icon = QtGui.QIcon(pixmap)
		return icon

	def setCSVFile(self, textBoxName):
		fileName = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.prn;*.txt;*.csv)")
		if fileName != "":
			textBoxName.setText(str(os.path.normpath(fileName)))

	def setLocationFile(self, textBoxName):
		fileName = QFileDialog.getOpenFileName(self, "Select File", "", "Powershell Scripts (*.ps1)")
		if fileName != "":
			textBoxName.setText(str(os.path.normpath(fileName)))

	def setLocationFolder(self, textBoxName):
		fileName = QFileDialog.getExistingDirectory(self, "Select Folder")
		if fileName != "":
			textBoxName.setText(str(fileName))

	def loadConfigFile(self, element):
		try:
			if(os.path.isfile("config.yaml")):
				config_file = open("config.yaml")
				data = yaml.safe_load(config_file)
			return data[element]
		except Exception as e:
			return False

	def putCommentinList(self, comment):
		try:
			if ((comment != "")):
				temp_list = comment.split("\n")
			return temp_list
		except Exception as e:
			return False

	def ct(self):
		try:
			chosen_option = "CT"

			final_comment = self.putCommentinList(script_comment)

			if ( (self.script_path_txt.text() != "") and (self.ssm_wrapperloc_txt.text() != "") and (self.csv_path_txt.text() != "") ):

				csv_acc1_region_list = {}
				csv_acc2_region_list = {}
				csv_acc3_region_list = {}
				hostnames = [] #placeholder only for kwargs["ml"] to fill the requirement in ProcessWidget()

				df = read_csv(self.csv_path_txt.text())
				for data in df.to_records(index=False):
					if data["Account"] == "acc1":
						if data["Region"] not in csv_acc1_region_list.keys():
							csv_acc1_region_list[data["Region"]] = []
						csv_acc1_region_list[data["Region"]].append(data["InstanceID"])
					elif data["Account"] == "acc2":
						if data["Region"] not in csv_acc2_region_list.keys():
							csv_acc2_region_list[data["Region"]] = []
						csv_acc2_region_list[data["Region"]].append(data["InstanceID"])
					elif data["Account"] == "acc3":
						if data["Region"] not in csv_acc3_region_list.keys():
							csv_acc3_region_list[data["Region"]] = []
						csv_acc3_region_list[data["Region"]].append(data["InstanceID"])

				self.ProcessWindow = ProcessWidget(chosen_option, self.filename_log, prefix=self.fn_prefix_txt.text(), cs=self.script_path_txt.text(), ssml=self.ssm_wrapperloc_txt.text(), ol=self.output_loc_txt.text(), sc=script_comment, ml=hostnames, acc1lcsv=csv_acc1_region_list, acc2lcsv=csv_acc2_region_list, acc3lcsv=csv_acc3_region_list)
				self.ProcessWindow.displayWindow()
			else:
				popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
					"Warning",
					"All fields and options that are required must have input!",
					QtGui.QMessageBox.Ok,
					self)
				popup.show()
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)

	def crt(self):
		try:
			chosen_option = "CRT"

			final_comment = self.putCommentinList(script_comment)

			if ( (self.script_path_txt.text() != "") and (self.ssm_wrapperloc_txt.text() != "") and (self.csv_path_txt.text() != "") ):
				
				message_box = QtGui.QMessageBox
				popup = message_box.question(self, '', "Are you sure you want to create and run the template?\n(WhatIf: Disabled)", message_box.Yes | message_box.No)
				if popup == message_box.Yes:

					csv_acc1_region_list = {}
					csv_acc2_region_list = {}
					csv_acc3_region_list = {}
					hostnames = [] #placeholder only for kwargs["ml"] to fill the requirement in ProcessWidget()

					df = read_csv(self.csv_path_txt.text())
					for data in df.to_records(index=False):
						if data["Account"] == "acc1":
							if data["Region"] not in csv_acc1_region_list.keys():
								csv_acc1_region_list[data["Region"]] = []
							csv_acc1_region_list[data["Region"]].append(data["InstanceID"])
						elif data["Account"] == "acc2":
							if data["Region"] not in csv_acc2_region_list.keys():
								csv_acc2_region_list[data["Region"]] = []
							csv_acc2_region_list[data["Region"]].append(data["InstanceID"])
						elif data["Account"] == "acc3":
							if data["Region"] not in csv_acc3_region_list.keys():
								csv_acc3_region_list[data["Region"]] = []
							csv_acc3_region_list[data["Region"]].append(data["InstanceID"])

					self.ProcessWindow = ProcessWidget(chosen_option, self.filename_log, prefix=self.fn_prefix_txt.text(), cs=self.script_path_txt.text(), ssml=self.ssm_wrapperloc_txt.text(), ol=self.output_loc_txt.text(), sc=script_comment, ml=hostnames, acc1lcsv=csv_acc1_region_list, acc2lcsv=csv_acc2_region_list, acc3lcsv=csv_acc3_region_list)
					self.ProcessWindow.displayWindow()
			else:
				popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
					"Warning",
					"All fields and options that are required must have input!",
					QtGui.QMessageBox.Ok,
					self)
				popup.show()
		except Exception as e:
			var = traceback.format_exc()
			print(var, flush=True)
			print(e, flush=True)


class CommentWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setGeometry(300, 200, 600, 150)
		image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAABcElEQVR42mM4I61EU8QwMiw4K68BRppA9mkJuas2HldtPM/IqVPPAgXNs7Jqp0UlT4tJ347P+nbt5oPK5jPSitSzQE79tLjMOVX9J12T/37+8v////tFtWck5almwWkpxSu2Hu/3Hf4PBv+AFhTUnJFUoF4kS8o/KG34jwTuF9edkVKkqgXlTSgWlDZQ0wdnZVWuugc/65/5tHfas/7pz/pnXHMPOSujTM1UBPTECQHuEwK8EATkggSpmA/Oq+hd1Le6qGd1Sc8ayDinqntWToOKOVnxTmL21yvXP52//PnC5S+Xr91OzKZqUYERyUAuVZOplML9wlpIDvgHSUWgjEbVfHC/sAbFgsKaIWaBAhYLpGhrQS2ViwoaB5EUhg+GQSqibhxIDUgkUzWZKt4vqEa1oJrKqQi9sKugbmEnrXAntfDb7btfrt38ev3Wtxu3b6flU7XZIq9xTs3wsrkTEF0BIjOn82pGZ6nY8BrZjV8AtoThH2QTo+cAAAAASUVORK5CYII=
		"""
		self.icon = self.iconFromBase64(image_icon)
		self.setWindowIcon(self.icon)
		self.setWindowTitle("Edit Headers")
		self.setFixedSize(400, 150)

		global script_comment

		layout = QVBoxLayout()

		self.blockText = QTextEdit(self)
		self.blockText.resize(400,80)
		
		if (self.loadConfigFile("ScriptComment")):
			value = self.loadConfigFile("ScriptComment")
			self.blockText.setText('\n'.join(str(x) for x in value))
			script_comment = ""
		
		self.blockText.insertPlainText(script_comment)

		button_layout = QHBoxLayout()

		self.btn_comment = QtGui.QPushButton("Save", self)
		self.btn_comment.clicked.connect(lambda: self.setComment(self.blockText.toPlainText()))
		self.btn_comment.resize(self.btn_comment.minimumSizeHint())

		self.btn_comment_cancel = QtGui.QPushButton("Cancel", self)
		self.btn_comment_cancel.clicked.connect(self.close)
		self.btn_comment_cancel.resize(self.btn_comment_cancel.minimumSizeHint())

		button_layout.addWidget(self.btn_comment)
		button_layout.addWidget(self.btn_comment_cancel)

		layout.addWidget(self.blockText)
		layout.addLayout(button_layout)

		self.setLayout(layout)

	def displayWindow(self):
		self.show()

	def putCommentinList(self, comment):
		try:
			if ((comment != "")):
				temp_list = comment.split("\n")
			return temp_list
		except Exception as e:
			return False

	def setComment(self, new_comment):
		global script_comment
		script_comment = new_comment
		try:
			with open("config.yaml") as x:
				temp_list = yaml.safe_load(x)

			for line in temp_list:
				if (temp_list["ScriptComment"]):
					temp_list["ScriptComment"] = self.putCommentinList(script_comment)

			with open("config.yaml", "w") as x:
				yaml.dump(temp_list, x)

			self.close()
		except Exception as e:
			self.close()

	def loadConfigFile(self, element):
		try:
			if(os.path.isfile("config.yaml")):
				config_file = open("config.yaml")
				data = yaml.safe_load(config_file)
			return data[element]
		except Exception as e:
			return False

	def iconFromBase64(self, base64):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64))
		icon = QtGui.QIcon(pixmap)
		return icon


class HelpWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setGeometry(300, 200, 600, 280)
		image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAABcElEQVR42mM4I61EU8QwMiw4K68BRppA9mkJuas2HldtPM/IqVPPAgXNs7Jqp0UlT4tJ347P+nbt5oPK5jPSitSzQE79tLjMOVX9J12T/37+8v////tFtWck5almwWkpxSu2Hu/3Hf4PBv+AFhTUnJFUoF4kS8o/KG34jwTuF9edkVKkqgXlTSgWlDZQ0wdnZVWuugc/65/5tHfas/7pz/pnXHMPOSujTM1UBPTECQHuEwK8EATkggSpmA/Oq+hd1Le6qGd1Sc8ayDinqntWToOKOVnxTmL21yvXP52//PnC5S+Xr91OzKZqUYERyUAuVZOplML9wlpIDvgHSUWgjEbVfHC/sAbFgsKaIWaBAhYLpGhrQS2ViwoaB5EUhg+GQSqibhxIDUgkUzWZKt4vqEa1oJrKqQi9sKugbmEnrXAntfDb7btfrt38ev3Wtxu3b6flU7XZIq9xTs3wsrkTEF0BIjOn82pGZ6nY8BrZjV8AtoThH2QTo+cAAAAASUVORK5CYII=
		"""
		self.icon = self.iconFromBase64(image_icon)
		self.setWindowIcon(self.icon)
		self.setWindowTitle("Help")
		self.setFixedSize(600, 280)

		fontTitle = QtGui.QFont()
		fontTitle.setBold(True)
		fontTitle.setPointSize(14)

		self.blockText = QPlainTextEdit(self)
		self.blockText.resize(600,280)
		self.blockText.setReadOnly(True)

		whole_text = """Welcome to LE SSM Wrapper Template Creator!

How to Use?

1. Fill up the required options (Path of Created Script, SSM Wrapper Location, Accounts).

2. For the other entities, you may or may not fill up them as they are optional.

3. Customize the headers of your script to be created by clicking "Edit Headers" before choosing what action you want to do.

4. Choose an action.
 -> Create Template - creates the ps1 template based on the values set that is ready to be executed. After execution, you will have the option to view the powershell file.
 -> Create and Run Template - creates the ps1 template based on the values set and will be executed. After execution. you will have the option to view the report or the powershell file.
 -> Create and Run Template (WhatIf) - creates the ps1 template based on the values set and will be executed with -WhatIf enabled. After execution. you will have the option to view the report or the powershell file.

Note:
-> The created file will be stored in the same directory of the application if Output location does not have a value.
-> This tool only allows one process at a time.

© 2021 Clark Pañares."""
		
		self.blockText.insertPlainText(whole_text)

	def displayWindow(self):
		self.show()

	def iconFromBase64(self, base64):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64))
		icon = QtGui.QIcon(pixmap)
		return icon

class ProcessWidget(QtGui.QWidget):

	def __init__(self, option, filename_log, **kwargs):
		super().__init__()
		self.setGeometry(400, 300, 400, 120)
		image_icon = """
		iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAABcElEQVR42mM4I61EU8QwMiw4K68BRppA9mkJuas2HldtPM/IqVPPAgXNs7Jqp0UlT4tJ347P+nbt5oPK5jPSitSzQE79tLjMOVX9J12T/37+8v////tFtWck5almwWkpxSu2Hu/3Hf4PBv+AFhTUnJFUoF4kS8o/KG34jwTuF9edkVKkqgXlTSgWlDZQ0wdnZVWuugc/65/5tHfas/7pz/pnXHMPOSujTM1UBPTECQHuEwK8EATkggSpmA/Oq+hd1Le6qGd1Sc8ayDinqntWToOKOVnxTmL21yvXP52//PnC5S+Xr91OzKZqUYERyUAuVZOplML9wlpIDvgHSUWgjEbVfHC/sAbFgsKaIWaBAhYLpGhrQS2ViwoaB5EUhg+GQSqibhxIDUgkUzWZKt4vqEa1oJrKqQi9sKugbmEnrXAntfDb7btfrt38ev3Wtxu3b6flU7XZIq9xTs3wsrkTEF0BIjOn82pGZ6nY8BrZjV8AtoThH2QTo+cAAAAASUVORK5CYII=
		"""
		self.icon = self.iconFromBase64(image_icon)
		self.setWindowIcon(self.icon)
		self.setWindowTitle("Processing...")
		self.setFixedSize(400, 120)

		self.filename_log = filename_log
		self.cred_to_check = str()

		temp_list_statement = []
		list_of_accounts = {"acc1": 0, "acc2": 0, "acc3": 0}

		for k, v in list_of_accounts.items():
			accl = k + "l"
			acclcsv = k + "lcsv"

			if accl in kwargs:
				if (bool(kwargs[accl]) == True):
					list_of_accounts[k] = 1
					for region in kwargs[accl]:
						statement = 'Start-Job -Name "' + k + '_' + region + '" -ArgumentList $a,$outfile,$hostname -ScriptBlock {param($a, $outfile, $hostname) ' +  kwargs["ssml"] + ' -DocumentName AWS-RunPowerShellScript -Parameters @{"commands" = $a; "executionTimeout" = "' + kwargs["et"] + '"} -CSVOutPath $outfile -Account ' + k + ' -Region ' + region + ' -Timeout ' + kwargs["et"] + ((' ' + '-CostCenter ' + ','.join("'" + str(x) + "'" for x in kwargs["cc"])) if bool(kwargs["cc"]) else "") + ((' ' + '-Service ' + ','.join("'" + str(x) + "'" for x in kwargs["sl"])) if bool(kwargs["sl"]) else "") + ((' ' + '-InstanceIDs ' + ','.join("'" + str(x) + "'" for x in kwargs["iid"])) if bool(kwargs["iid"]) else "") + ((' ' + '-MachineLabel $hostname') if bool(kwargs["ml"]) else "") + ((' ' + '-DeploymentType ' + ','.join(str(x) for x in kwargs["dl"])) if bool(kwargs["dl"]) else "") + ((' ' + '-CustomerPrefix ' + ','.join("'" + str(x) + "'" for x in kwargs["cp"])) if bool(kwargs["cp"]) else "") + ((' ' + '-IsProduction ' + ','.join(str(x) for x in kwargs["pl"])) if bool(kwargs["pl"]) else "")
						temp_list_statement.append(statement)
				else:	
					pass
			elif acclcsv in kwargs:
				if (bool(kwargs[acclcsv]) == True):
					list_of_accounts[k] = 1
					for i,j in kwargs[acclcsv].items():
						statement = 'Start-Job -Name "' + k + '_' + i + '" -ArgumentList $a,$outfile,$hostname -ScriptBlock {param($a, $outfile, $hostname) ' +  kwargs["ssml"] + ' -DocumentName AWS-RunPowerShellScript -Parameters @{"commands" = $a; "executionTimeout" = "240"} -CSVOutPath $outfile -Account ' + k + ' -Region ' + i + ' -Timeout 240' + ((' ' + '-InstanceIDs ' + ','.join("'" + str(x) + "'" for x in j)) if bool(j) else "")
						temp_list_statement.append(statement)
				else:	
					pass

		fontTitle = QtGui.QFont()
		fontTitle.setBold(True)
		fontTitle.setPointSize(8)

		self.title = QtGui.QLabel("",self)
		self.title.setFont(fontTitle)
		self.title.setAlignment(QtCore.Qt.AlignCenter)
		self.title.resize(600,70)

		self.indicator = QtGui.QLabel("",self)
		self.indicator.setFont(fontTitle)
		self.indicator.hide()

		self.btn_report = QtGui.QPushButton("View Report", self)
		self.btn_report.resize(self.btn_report.minimumSizeHint())
		self.btn_report.hide()

		self.btn_log = QtGui.QPushButton("View Powershell Script", self)
		self.btn_log.resize(self.btn_log.minimumSizeHint())
		#self.btn_log.clicked.connect(lambda: self.openPSFile(os.getcwd() + "\\logs\\" + self.filename_log + ".log"))
		self.btn_log.hide()

		self.btn = QtGui.QPushButton("Close", self)
		self.btn.clicked.connect(self.closeWindow)
		self.btn.resize(self.btn.minimumSizeHint())
		self.btn.hide()


		########Widget for running the powershell script##########

		self.w = QWidget()
		self.w.setWindowIcon(self.icon)
		self.w.setWindowTitle("Powershell")
		self.w.setFixedSize(600, 280)
		self.w.setWindowFlags(self.w.windowFlags() | QtCore.Qt.CustomizeWindowHint)
		self.w.setWindowFlags(self.w.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

		self.text = QPlainTextEdit()
		self.text.setReadOnly(True)

		self.btn_close = QtGui.QPushButton("Close Window", self)
		self.btn_close.resize(self.btn_close.minimumSizeHint())
		self.btn_close.hide()

		l = QVBoxLayout()
		l.addWidget(self.text)
		l.addWidget(self.btn_close)
		self.w.setLayout(l)

		########END##########

		mainLayout = QVBoxLayout()
		mainLayout.addWidget(self.title)
		mainLayout.addWidget(self.btn_report)
		mainLayout.addWidget(self.btn_log)
		mainLayout.addWidget(self.btn)
		self.setLayout(mainLayout)

		if option == "CT":
			self.ThreadingClass = ThreadingClass(option, filename_log, temp_list_statement, kwargs["cs"], kwargs["prefix"], kwargs["ol"], kwargs["ml"], list_of_accounts, kwargs["sc"])
			self.ThreadingClass.start()
			self.connect(self.ThreadingClass, QtCore.SIGNAL('TEXT'), self.updateTextProgress)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('REPORT'), self.updateTextProgress3)
		elif option == "CRT":
			self.ThreadingClass = ThreadingClass(option, filename_log, temp_list_statement, kwargs["cs"], kwargs["prefix"], kwargs["ol"], kwargs["ml"], list_of_accounts, kwargs["sc"])
			self.ThreadingClass.start()
			self.connect(self.ThreadingClass, QtCore.SIGNAL('TEXT'), self.updateTextProgress)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('OPTION'), self.updateTextProgress2)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('REPORT'), self.updateTextProgress3)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('RUN'), self.processScript)
		elif option == "CRT_WhatIf":
			self.ThreadingClass = ThreadingClass(option, filename_log, temp_list_statement, kwargs["cs"], kwargs["prefix"], kwargs["ol"], kwargs["ml"], list_of_accounts, kwargs["sc"])
			self.ThreadingClass.start()
			self.connect(self.ThreadingClass, QtCore.SIGNAL('TEXT'), self.updateTextProgress)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('OPTION'), self.updateTextProgress2)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('REPORT'), self.updateTextProgress3)
			self.connect(self.ThreadingClass, QtCore.SIGNAL('RUN'), self.processScript)

	def processScript(self, val):
		if "CLOSE" in val:
			self.btn_close.show()
			self.btn_close.clicked.connect(self.endProcess)
		else:
			self.message(self.text, val)

	def endProcess(self):
		global lock
		lock = True
		self.w.close()


	def message(self, var, s):
		var.appendPlainText(s)

	def displayWindow(self):
		self.show()

	def closeWindow(self):
		self.close()

	def closeEvent(self, event):
		self.endProcess()
		self.closeWindow()
		self.ThreadingClass.terminate()
		print("Stopping all threads...", flush=True)
		print("Process terminated! You may choose an action again.", flush=True)

	def openFile(self, file):
		os.startfile(file)
		self.closeWindow()

	def openPSFile(self, file):
		subprocess.Popen(["powershell_ise.exe", "-File", file])

	def openLogFileError(self, file):
		os.startfile(os.getcwd() + "\\logs\\" + file)
		QtCore.QCoreApplication.instance().quit()

	def updateTextProgress(self, val):
		print(val, flush=True)
		self.title.setText(val)
		if "An error has occurred." in val:
			time.sleep(2)
			self.hide()
			popup = QtGui.QMessageBox(QtGui.QMessageBox.Critical,
				"Error",
				val,
				QtGui.QMessageBox.Close,
				self)
			popup.show()
			popup.buttonClicked.connect(lambda: self.openLogFileError(self.filename_log + "_failed.log"))
			sys.stdout.close()
			os.rename("logs/" + self.filename_log + ".log", "logs/" + self.filename_log + "_failed.log")
		elif "Running Template..." in val:
			self.w.show()
		elif "successfully created" in val:
			self.btn.show()
			self.btn_log.show()

	def updateTextProgress2(self, val):
		self.indicator.setText(val)
		if ("CRT" in val) or ("CRT_WhatIf" in val):
			self.btn_report.show()

	def updateTextProgress3(self, val ,val2):
		if val != "":
			self.btn_report.clicked.connect(lambda: self.openFile(val))
		if val2 != "":
			self.btn_log.clicked.connect(lambda: self.openPSFile(val2))

	def iconFromBase64(self, base64):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64))
		icon = QtGui.QIcon(pixmap)
		return icon

class ThreadingClass(QtCore.QThread):
	def __init__(self, option, filename_log, temp_list_statement, created_script, prefix, outputloc, hostname, cred_to_check, ssm_comment):
		super(ThreadingClass, self).__init__()

		global lock
		lock = False
		self.option = option
		self.filename_log = filename_log
		self.temp_list_statement = temp_list_statement
		self.created_script = created_script
		self.prefix = prefix
		self.outputloc = outputloc
		self.hostname = hostname
		self.cred_to_check = cred_to_check
		self.ssm_comment = ssm_comment

	def run(self):
		if self.option == "CT":
			try:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "\nCreating Template...")
				sys.stdout.flush()
				time.sleep(5)
				output_script = createTemplate(self.temp_list_statement, self.created_script, self.prefix, self.outputloc, self.hostname, self.ssm_comment)
				self.emit(QtCore.SIGNAL('TEXT'), "Template successfully created!")
				self.emit(QtCore.SIGNAL('REPORT'), "", output_script)
				sys.stdout.flush()
			except Exception as e:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "An error has occurred. See " + self.filename_log + "_failed.log for details.")
				var = traceback.format_exc()
				print(var, flush=True)
				print(e, flush=True)
		
		elif self.option == "CRT":
			try:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "\nCreating Template...")
				sys.stdout.flush()
				time.sleep(5)
				output_script, final_name_script = create_Run_Template(self.temp_list_statement, self.created_script, self.prefix, self.outputloc, self.hostname, self.ssm_comment)
				sys.stdout.flush()
				self.emit(QtCore.SIGNAL('TEXT'), "Template creation successful!")
				time.sleep(2)
				sys.stdout.flush()
				
				self.emit(QtCore.SIGNAL('TEXT'), "Validating STS credentials...")
				checkCredentials(self.cred_to_check)
				time.sleep(3)
				sys.stdout.flush()

				print("", flush=True)
				self.emit(QtCore.SIGNAL('TEXT'), "Running Template...")

				with subprocess.Popen(["start", "/B", "/wait", "powershell", "-File", output_script], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) as p:
					for line in p.stdout:
							self.emit(QtCore.SIGNAL('RUN'), line.rstrip().decode("utf-8"))
					temp_err = p.stderr.read().rstrip().decode("utf-8")
					if (temp_err != ""):
							self.emit(QtCore.SIGNAL('RUN'), temp_err)
							self.emit(QtCore.SIGNAL('RUN'), "CLOSE")
							p.kill()
							raise Exception(temp_err)
					else:
						self.emit(QtCore.SIGNAL('RUN'), "CLOSE")
						p.kill()
						while(lock == False):
							time.sleep(1)

				csv_file = findTemplateReport(final_name_script)
				sys.stdout.flush()
				self.emit(QtCore.SIGNAL('TEXT'), "Template successfully created and executed!")
				self.emit(QtCore.SIGNAL('OPTION'), self.option)
				self.emit(QtCore.SIGNAL('REPORT'), csv_file, output_script)
				sys.stdout.flush()

			except Exception as e:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "An error has occurred. See " + self.filename_log + "_failed.log for details.")
				var = traceback.format_exc()
				print(var, flush=True)
				print(e, flush=True)
		else:
			try:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "\nCreating Template...")
				sys.stdout.flush()
				time.sleep(5)
				output_script, final_name_script = create_Run_Template_WhatIf(self.temp_list_statement, self.created_script, self.prefix, self.outputloc, self.hostname, self.ssm_comment)
				sys.stdout.flush()
				self.emit(QtCore.SIGNAL('TEXT'), "Template creation successful!")
				time.sleep(2)
				sys.stdout.flush()
				
				self.emit(QtCore.SIGNAL('TEXT'), "Validating STS credentials...")
				checkCredentials_WI(self.cred_to_check)
				time.sleep(3)
				sys.stdout.flush()

				print("", flush=True)
				self.emit(QtCore.SIGNAL('TEXT'), "Running Template...")

				with subprocess.Popen(["start", "/B", "/wait", "powershell", "-File", output_script], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) as p:
					for line in p.stdout:
							self.emit(QtCore.SIGNAL('RUN'), line.rstrip().decode("utf-8"))
					temp_err = p.stderr.read().rstrip().decode("utf-8")
					if (temp_err != ""):
							self.emit(QtCore.SIGNAL('RUN'), temp_err)
							self.emit(QtCore.SIGNAL('RUN'), "CLOSE")
							p.kill()
							raise Exception(temp_err)
					else:
						self.emit(QtCore.SIGNAL('RUN'), "CLOSE")
						p.kill()
						while(lock == False):
							time.sleep(1)

				csv_file = findTemplateReport_WhatIf(final_name_script)
				sys.stdout.flush()
				self.emit(QtCore.SIGNAL('TEXT'), "Template successfully created and executed with -WhatIf option!")
				self.emit(QtCore.SIGNAL('OPTION'), self.option)
				self.emit(QtCore.SIGNAL('REPORT'), csv_file, output_script)
				sys.stdout.flush()

			except Exception as e:
				#self.emit(QtCore.SIGNAL('PERCENTAGE'), completed)
				self.emit(QtCore.SIGNAL('TEXT'), "An error has occurred. See " + self.filename_log + "_failed.log for details.")
				var = traceback.format_exc()
				print(var, flush=True)
				print(e, flush=True)

def remove_qt_temporary_files():
    if os.path.exists('qt.conf'):
        os.remove('qt.conf')

if __name__ == '__main__':
	app = QApplication(sys.argv)
	main = MainWidget()
	main.show()
	remove_qt_temporary_files()
	sys.exit(app.exec_())