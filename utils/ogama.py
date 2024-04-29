import os
import pandas as pd
import sqlite3
import numpy as np
from peitek_opt import opt
# Need to register numpy types to be able to save them in the database, as SQL only supports int8
sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))

# Path to database (Change this to your database path of the Ogama experiment)
base_database_path = 'G:\\Dokumente\\OgamaExperiments\\Experiment4_1\\Database\\Experiment4_1.db'

######################################Sharafi Ogama########################################

def import_data_into_ogama_sharafi(path, subject, database_path=base_database_path):

	# We load the original data from the file data/4/formatted-raw-data/151/ogama.txt
	data = pd.read_csv(path, sep=',', skiprows=0, encoding='utf-16')

	# Change the values of the ImageName column to remove the last 4 characters (".PNG")
	data[' ImageName'] = data[' ImageName'].str[:-4]

	# We remove all rows where Included? is "N"
	data = data[data[' Included?'] == "Y"]

	# Normalize time
	data[' StartTime'] = data[' StartTime'] - data[' StartTime'].min()
	# Time as integer
	data[' StartTime'] = data[' StartTime'].astype('int32')

	# Format X and Y to screen of size 1920x1080 instead of 1024x768
	data[' X'] = data[' X'] * 1920 / 1024
	data[' Y'] = data[' Y'] * 1080 / 768

	# Check if database exists
	if not os.path.exists(database_path):
		raise Exception("Database does not exist")
	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	# Add a table for the subject called Subject + 'RawData'
	c.execute("CREATE TABLE IF NOT EXISTS ["+ subject +"Rawdata] ([ID] integer PRIMARY KEY AUTOINCREMENT NOT NULL,[SubjectName] varchar(50) NOT NULL COLLATE NOCASE, [TrialSequence] integer NOT NULL, [Time] integer NOT NULL, [PupilDiaX] float, [PupilDiaY] float, [GazePosX] float, [GazePosY] float, [MousePosX] float, [MousePosY] float, [EventID] integer)")

	# Add data in the following scheme:
		# SubjectName = subject
		# TrialSequence = ' ImageName'
		# Time = ' StartTime'
		# GazePosX = ' X'
		# GazePosY = ' Y'
	
	# For each row in the dataframe
	for index, row in data.iterrows():
		# Insert the data into the table
		c.execute("INSERT INTO ["+ subject +"Rawdata] (SubjectName, TrialSequence, Time, GazePosX, GazePosY) VALUES (?, ?, ?, ?, ?)", (subject, row[' ImageName'], row[' StartTime'], row[' X'], row[' Y']))

	# Add subject to the Subjects table
	c.execute("INSERT INTO Subjects (SubjectName) VALUES (?)", (subject,))

	# Add each grouped trial to the Trials table
	for trial in data.groupby(' ImageName'):
		trialstarttime = trial[1][' StartTime'].min()
		# Max Starttime + last duration
		trialduration = trial[1][' StartTime'].max() - trial[1][' StartTime'].min() + trial[1][' Duration'].iloc[-1]
		trialduration = int(trialduration)
		c.execute("INSERT INTO Trials (SubjectName, TrialID, TrialName, TrialSequence, Category,  TrialStartTime, Duration) VALUES (?, ?, ?, ?, ?, ?, ?)", (subject, trial[0], trial[0], trial[0], "",trialstarttime, trialduration))

	# Save the database
	conn.commit()

def drop_all_subject_tables_sharafi(database_path=base_database_path):
	# Check if database exists
	if not os.path.exists(database_path):
		raise Exception("Database does not exist")
	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	for i in range(151, 205):
		# Drop the table named S + str(i) + "RawData"
		c.execute("DROP TABLE IF EXISTS S" + str(i) + "Rawdata")

	# Delete entries from Trials
	c.execute("DELETE FROM Trials")

	# Delete entries from Subjects
	c.execute("DELETE FROM Subjects")

	# Save the database
	conn.commit()


def calculate_results_for_subject_sharafi(subject, database_path=base_database_path):
	# Check if database exists
	if not os.path.exists(database_path):
		raise Exception("Database does not exist")
	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	# Export all fixations for the subject
	c.execute("SELECT * FROM GazeFixations WHERE SubjectName = ?", (subject,))
	fixations = c.fetchall()

	# Save it into a dataframe
	fixations_df = pd.DataFrame(fixations)

	# Set the column names of the dataframe
	fixations_df.columns = ['ID', 'SubjectName', 'TrialID', 'TrialSequence', 'CountInTrial', 'StartTime', 'Length', 'PosX', 'PosY']

	# For each TrialID, we calculate the total fixation count, fixation duration and average fixation duration
	results = pd.DataFrame()
	results['Total Fixation Count'] = fixations_df.groupby('TrialID')['ID'].count()
	results['Total Fixation Duration'] = fixations_df.groupby('TrialID')['Length'].sum()
	results['Average Fixation Duration'] = fixations_df.groupby('TrialID')['Length'].mean()
	results['Subject'] = subject


	return results

######################################EMIP Ogama########################################

trial_to_num = {
		'mupliple_choice_rectangle.jpg': '1',
		'mupliple_choice_vehicle.jpg': '2',
		'rectangle_java.jpg': '3',
		'rectangle_java2.jpg': '4',
		'rectangle_python.jpg': '5',
		'rectangle_scala.jpg': '6',
		'vehicle_java.jpg': '7',
		'vehicle_java2.jpg': '8',
		'vehicle_python.jpg': '9',
		'vehicle_scala.jpg': '10',
	}

def add_to_sql_emip(c, df_msg, subject, last_task_name):

	df_msg = df_msg[(df_msg['R Validity'] == 1)].copy()

	if df_msg.size == 0:
		print("df_msg is empty", last_task_name)
		return

	# Define parameters for fixation detection
	x_right = df_msg.loc[:,('R POR X [px]')]
	df_msg.loc[:,('X')] = x_right

	y_right = df_msg.loc[:,('R POR Y [px]')]
	df_msg.loc[:,('Y')] = y_right
	

	# Add a table for the subject called Subject + 'RawData'
	c.execute("CREATE TABLE IF NOT EXISTS ["+ subject +"Rawdata] ([ID] integer PRIMARY KEY AUTOINCREMENT NOT NULL,[SubjectName] varchar(50) NOT NULL COLLATE NOCASE, [TrialSequence] integer NOT NULL, [Time] integer NOT NULL, [PupilDiaX] float, [PupilDiaY] float, [GazePosX] float, [GazePosY] float, [MousePosX] float, [MousePosY] float, [EventID] integer)")

	# Add data in the following scheme:
	# SubjectName = subject
	# TrialSequence = ' ImageName'
	# Time = ' StartTime'
	# GazePosX = ' X'
	# GazePosY = ' Y'

	# For each row in the dataframe
	for index, row in df_msg.iterrows():
		# Insert the data into the table
		c.execute("INSERT INTO ["+ subject +"Rawdata] (SubjectName, TrialSequence, Time, GazePosX, GazePosY) VALUES (?, ?, ?, ?, ?)", (subject, trial_to_num[last_task_name], row['Time'], row['X'], row['Y']))

	trialstarttime = df_msg['Time'].min()
	# Endtime - Starttime + 4 ms for the duration of the last measuremnt
	trialduration = df_msg['Time'].max() - df_msg['Time'].min() + 4
	if np.isnan(trialduration):
		print("trialduration is nan", trialstarttime, df_msg['Time'].max(), df_msg['Time'].min())
		print(df_msg)

	trialduration = int(trialduration)
	c.execute("INSERT INTO Trials (SubjectName, TrialID, TrialName, TrialSequence, Category,  TrialStartTime, Duration) VALUES (?, ?, ?, ?, ?, ?, ?)", (subject, trial_to_num[last_task_name], last_task_name, trial_to_num[last_task_name], "",trialstarttime, trialduration))

def import_data_into_ogama_emip(path, subject, database_path=base_database_path):

	# Load the Tobii eye tracker data into a Pandas DataFrame and skip lines that start with ## as they are comments

	df = None
	possible_skipped_rows = [37, 32, 41, 45]
	counter = 0
	while df is None:
		try:
			df = pd.read_csv(path, delimiter='\t', low_memory=False, on_bad_lines='skip', skiprows=possible_skipped_rows[counter])
			df = df[['Time', 'Type', 'L Raw X [px]', 'L Raw Y [px]', 'R Raw X [px]', 'R Raw Y [px]', 'L Validity', 'R Validity', 'R POR X [px]', 'R POR Y [px]']]
		except KeyError as e:
			counter = counter + 1
			df = None
			if counter >= len(possible_skipped_rows):
				print("no possible skipped rows worked", e)
				break
		else:
			break

	df['Type'] = df['Type'].astype(str)
	df = df.fillna(0.0)

	# Normalize time
	df['Time'] = df['Time'] - df['Time'].min()
	# Time conversion from microseconds to milliseconds
	df['Time'] = df['Time'] / 1000
	# Time as integer
	df['Time'] = df['Time'].astype('int32')

	# Get the row numbers where Type is 'MSG'
	msg_rows = df[df['Type'] == 'MSG'].index

	# For each msg_row, split the df into two dataframes, one before the msg_row and one after
	# Run the analysis for each of those split dataframes as they represent different tasks
	last_task_name = None
	last_task_row_number = 0
	removed_task_names = {
		'instruction_calibration.jpg': True,
		'instruction_comprehension.jpg': True,
	}

	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	for msg_row in msg_rows:
		current_task_name = df['L Raw X [px]'][msg_row].split('Message: ')[1]
		if '.jpg' in current_task_name:			
			if last_task_name is not None and last_task_name not in removed_task_names:
				
				df_msg = df[last_task_row_number:msg_row]
				if df_msg.size > 0:
					add_to_sql_emip(c, df_msg, subject, last_task_name)
				else:
					print("df_msg is empty", last_task_name, last_task_row_number, msg_row)
				

			last_task_name = current_task_name
			last_task_row_number = msg_row

	df_msg = df[last_task_row_number:]
	add_to_sql_emip(c, df_msg, subject, last_task_name)
	

	# Add subject to the Subjects table
	c.execute("INSERT INTO Subjects (SubjectName) VALUES (?)", (subject,))

	# Save the database
	conn.commit()

def drop_all_subject_tables_emip(database_path=base_database_path):
	# Connect to database
	import sqlite3
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	for i in range(1, 217):
		# Drop the table named S + str(i) + "RawData"
		c.execute("DROP TABLE IF EXISTS S" + str(i) + "Rawdata")

	# Delete entries from Trials
	c.execute("DELETE FROM Trials")

	# Delete entries from Subjects
	c.execute("DELETE FROM Subjects")

	# Save the database
	conn.commit()


def calculate_results_for_subject_emip(subject, database_path=base_database_path):
	# Connect to database
	import sqlite3
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	# Export all fixations for the subject
	c.execute("SELECT * FROM GazeFixations WHERE SubjectName = ?", (subject,))
	fixations = c.fetchall()


	if len(fixations) == 0:
		# Create an empty dataframe with the columns ID, SubjectName, TrialID, TrialSequence, CountInTrial, StartTime, Length, PosX, PosY
		fixations_df = pd.DataFrame(columns=['ID', 'SubjectName', 'TrialID', 'TrialSequence', 'CountInTrial', 'StartTime', 'Length', 'PosX', 'PosY'])
	else:
		# Save it into a dataframe
		fixations_df = pd.DataFrame(fixations)

		# Set the column names of the dataframe
		fixations_df.columns = ['ID', 'SubjectName', 'TrialID', 'TrialSequence', 'CountInTrial', 'StartTime', 'Length', 'PosX', 'PosY']

	# For each TrialID, we calculate the total fixation count, fixation duration and average fixation duration
	results = pd.DataFrame()
	results['Total Fixation Count'] = fixations_df.groupby('TrialID')['ID'].count()
	results['Total Fixation Duration'] = fixations_df.groupby('TrialID')['Length'].sum()
	results['Average Fixation Duration'] = fixations_df.groupby('TrialID')['Length'].mean()
	results['Subject'] = subject


	return results


####################################Peitek Ogama#############################################

trial_to_num = {
    1: "IsPrime",
    2: "SiebDesEratosthenes",
    3: "IsAnagram",
    4: "RemoveDoubleChar",
    5: "BinToDecimal",
    6: "PermuteString",
    7: "Power",
    8: "BinarySearch",
    9: "ContainsSubstring",
    10: "ReverseArray",
    11: "SumArray",
    12: "RectanglePower",
    13: "Vehicle",
    14: "GreatestCommonDivisor",
    15: "HIndex",
    16: "LengthOfLast",
    17: "MedianOnSorted",
    18: "SignChecker",
    19: "ArrayAverage",
    20: "DropNumber",
    21: "BinomialCoefficient",
    22: "Palindrome",
    23: "DumpSorting",
    24: "InsertSort",
    25: "HeightOfTree",
    26: "CheckIfLettersOnly",
    27: "SmallGauss",
    28: "BogoSort",
    29: "ReverseQueue",
    30: "Ackerman",
    31: "RabbitTortoise",
    32: "Rectangle",
}

num_to_trial = {v: k for k, v in trial_to_num.items()}

added_subjects = []

def add_to_sql_peitek(c, df_eyetracking, subject_name, task_name, starttime, endtime):
	
	print("Adding data for subject " + subject_name + " to the database...", task_name, starttime, endtime)
	# Add a table for the subject called Subject + 'RawData'
	c.execute("CREATE TABLE IF NOT EXISTS ["+ subject_name +"Rawdata] ([ID] integer PRIMARY KEY AUTOINCREMENT NOT NULL,[SubjectName] varchar(50) NOT NULL COLLATE NOCASE, [TrialSequence] integer NOT NULL, [Time] integer NOT NULL, [PupilDiaX] float, [PupilDiaY] float, [GazePosX] float, [GazePosY] float, [MousePosX] float, [MousePosY] float, [EventID] integer)")

	# Add data in the following scheme:
	# SubjectName = subject
	# TrialSequence = ' ImageName'
	# Time = ' StartTime'
	# GazePosX = ' X'
	# GazePosY = ' Y'

	if task_name not in trial_to_num:
		trial_to_num[task_name] = trial_to_num["current_count"]
		trial_to_num["current_count"] += 1
	trial_id = trial_to_num[task_name]
	
	# For each row in the dataframe
	for index, row in df_eyetracking.iterrows():
		# Insert the data into the table
		c.execute("INSERT INTO ["+ subject_name +"Rawdata] (SubjectName, TrialSequence, Time, GazePosX, GazePosY) VALUES (?, ?, ?, ?, ?)", (subject_name, trial_id, row['time'], row['X'], row['Y']))

	starttime = int(starttime * 1000)
	endtime = int(endtime * 1000)
	duration = endtime - starttime
	c.execute("INSERT INTO Trials (SubjectName, TrialID, TrialName, TrialSequence, Category,  TrialStartTime, Duration) VALUES (?, ?, ?, ?, ?, ?, ?)", (subject_name, trial_id, task_name, trial_id, "",starttime, duration))

def import_data_into_ogama_peitek(df_eyetracking, metadata, database_path=base_database_path, opt=None):

	# normalize the time regarding eyetracking to 0
	#df_eyetracking["time"] = df_eyetracking["time"].astype(float)
	#df_eyetracking["time"] = df_eyetracking["time"] - df_eyetracking["time"].iloc[0]

	# drop unused columns
	df_eyetracking = df_eyetracking.drop(columns=["l_gaze_point_in_user_coordinate_system_x",
												"l_gaze_point_in_user_coordinate_system_y",
												"l_gaze_point_in_user_coordinate_system_z",
												"r_gaze_point_in_user_coordinate_system_x",
												"r_gaze_point_in_user_coordinate_system_y",
												"r_gaze_point_in_user_coordinate_system_z",
												"l_gaze_origin_in_user_coordinate_system_x",
												"l_gaze_origin_in_user_coordinate_system_y",
												"l_gaze_origin_in_user_coordinate_system_z",
												"r_gaze_origin_in_user_coordinate_system_x",
												"r_gaze_origin_in_user_coordinate_system_y",
												"r_gaze_origin_in_user_coordinate_system_z"])

	# convert eyetracking data to display coordinates
	df_eyetracking["l_display_x"] = df_eyetracking["l_display_x"].astype(float) * opt["xres"]
	df_eyetracking["l_display_y"] = df_eyetracking["l_display_y"].astype(float) * opt["yres"]
	df_eyetracking["r_display_x"] = df_eyetracking["r_display_x"].astype(float) * opt["xres"]
	df_eyetracking["r_display_y"] = df_eyetracking["r_display_y"].astype(float) * opt["yres"]

	# convert miss column to right integer used by I2MC
	df_eyetracking["l_miss_x"] = df_eyetracking.apply(lambda row: row["l_display_x"] < -opt["xres"] or row["l_display_x"] > 2 * opt["xres"], axis=1)
	df_eyetracking["l_miss_y"] = df_eyetracking.apply(lambda row: row["l_display_y"] < -opt["yres"] or row["l_display_y"] > 2 * opt["yres"], axis=1)
	df_eyetracking["r_miss_x"] = df_eyetracking.apply(lambda row: row["r_display_x"] < -opt["xres"] or row["r_display_x"] > 2 * opt["xres"], axis=1)
	df_eyetracking["r_miss_y"] = df_eyetracking.apply(lambda row: row["r_display_y"] < -opt["yres"] or row["r_display_y"] > 2 * opt["yres"], axis=1)

	df_eyetracking["l_miss"] = df_eyetracking.apply(lambda row: row["l_miss_x"] or row["l_miss_y"] or not row["l_valid"] >= 1, axis=1)
	df_eyetracking["r_miss"] = df_eyetracking.apply(lambda row: row["r_miss_x"] or row["r_miss_y"] or not row["r_valid"] >= 1, axis=1)

	# Set a default value for missing data
	df_eyetracking.loc[df_eyetracking["l_miss"], "l_display_x"] = opt["missingx"]
	df_eyetracking.loc[df_eyetracking["l_miss"], "l_display_y"] = opt["missingy"]
	df_eyetracking.loc[df_eyetracking["r_miss"], "r_display_x"] = opt["missingx"]
	df_eyetracking.loc[df_eyetracking["r_miss"], "r_display_y"] = opt["missingy"]

	# drop unused columns
	df_eyetracking = df_eyetracking.drop(columns=["l_miss_x", "l_miss_y", "r_miss_x", "r_miss_y", "l_miss", "r_miss"])

	# rename columns to match I2MC format
	df_eyetracking.rename(columns={"l_display_x": "L_X",
								"l_display_y": "L_Y",
								"r_display_x": "R_X",
								"r_display_y": "R_Y",
								"l_valid" : "LValidity",
								"r_valid" : "RValidity"}, inplace=True)
	
	# Add new columns X and Y which are the average of L_X and R_X and L_Y and R_Y
	df_eyetracking["X"] = (df_eyetracking["L_X"] + df_eyetracking["R_X"]) / 2
	df_eyetracking["Y"] = (df_eyetracking["L_Y"] + df_eyetracking["R_Y"]) / 2
	
	# Transform time to ms
	df_eyetracking["time"] = df_eyetracking["time"].astype(float) * 1000.0
	# Save the time as integer, as the database does not support float
	df_eyetracking["time"] = df_eyetracking["time"].astype(int)

	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	subject_name = "S" + str(metadata["Participant"])
	add_to_sql_peitek(c, df_eyetracking, subject_name, metadata["Algorithm"], metadata["StartTime"], metadata["EndTime"])
	

	# Add subject to the Subjects table if it does not exist
	if not subject_name in added_subjects:
		added_subjects.append(subject_name)
		# Add the subject to the Subjects table
		c.execute("INSERT OR IGNORE INTO Subjects (SubjectName) VALUES (?)", (subject_name,))

	# Save the database
	conn.commit()

def drop_all_subject_tables_peitek(database_path=base_database_path):
	added_subjects = []
	# Connect to database
	conn = sqlite3.connect(database_path)
	c = conn.cursor()

	for i in range(1, 72):
		# Drop the table named S + str(i) + "RawData"
		c.execute("DROP TABLE IF EXISTS S" + str(i) + "Rawdata")
		#c.execute(f"DROP TABLE IF EXISTS {str(i)}Rawdata")

	# Delete entries from Trials
	c.execute("DELETE FROM Trials")

	# Delete entries from Subjects
	c.execute("DELETE FROM Subjects")

	# Save the database
	conn.commit()