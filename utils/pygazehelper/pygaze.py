import os
import xml.etree.ElementTree as ET
import pandas as pd
from utils.pygazehelper.corrected_pygaze_functions import fixation_detection_fixed, saccade_detection_fixed


def call_fixation_detection_on_data(fixation_info, participant, time, x, y, task = 0, parameters = {'missing': 0.0, 'maxdist': 25, 'mindur': 50}):
	missing = parameters['missing']  # Missing value threshold 
	maxdist = parameters['maxdist']  # Maximum distance for a fixation 
	mindur = parameters['mindur']  # Minimum duration for a fixation

	# Perform fixation detection using the fixed fixation_detection function
	Sfix, Efix = fixation_detection_fixed(x, y, time, missing=missing, maxdist=maxdist, mindur=mindur)

	# Calculate total fixation duration and average fixation duration
	total_duration = sum(sublist[2] for sublist in Efix)
	average_duration = total_duration / len(Efix) if len(Efix) > 0 else 0

	# Update the fixation_info dictionary
	fixation_info['Participant'].append(participant)
	fixation_info['Task'].append(task)
	fixation_info['Fixation Count'].append(len(Efix))
	fixation_info['Total Fixation Duration [ms]'].append(total_duration)
	fixation_info['Average Fixation Duration [ms]'].append(average_duration)

def call_saccade_detection_on_data(saccade_info, participant, time, x, y, task = 0, parameters={'missing': 0.0, 'minlen': 5, 'maxvel': 40, 'maxacc': 340}):
    missing = parameters['missing']  # Missing value threshold 
    minlen = parameters['minlen']  # Maximum distance for a saccade 
    maxvel = parameters['maxvel']  # Minimum duration for a saccade 
    maxacc = parameters['maxacc']

    # Perform saccade detection using the saccade_detection function
    Ssac, Esac = saccade_detection_fixed(x, y, time, missing=missing, minlen=minlen, maxvel=maxvel, maxacc=maxacc)

    # Calculate total saccade duration and average saccade duration
    total_duration = sum(sublist[2] for sublist in Esac)
    average_duration = total_duration / len(Esac) if len(Esac) > 0 else 0

	# Calculate average saccade distance
    average_distance = sum(((sublist[3] - sublist[5])**2 + (sublist[4] - sublist[6])**2)**0.5 for sublist in Esac) / len(Esac) if len(Esac) > 0 else 0

    # Update the saccade_info dictionary
    saccade_info['Participant'].append(participant)
    saccade_info['Task'].append(task)
    saccade_info['Saccade Count'].append(len(Esac))
    saccade_info['Total Saccade Duration [ms]'].append(total_duration)
    saccade_info['Average Saccade Duration [ms]'].append(average_duration)
    saccade_info['Average Saccade Distance [px]'].append(average_distance)


def prepare_tobii_data(directory_path, file_name, fixation_info, fn, parameters = {'missing': 0.0, 'maxdist': 25, 'mindur': 50}):
	tsv_file = os.path.join(directory_path, file_name)

	# Load the Tobii eye tracker data into a Pandas DataFrame and skip lines that start with ## as they are comments

	df = None
	# Tobii data files have different number of rows to skip at the beginning of the file
	# Try different row numbers to skip until the data is loaded successfully
	possible_skipped_rows = [37, 32, 41, 45]
	counter = 0
	while df is None:
		try:
			df = pd.read_csv(tsv_file, delimiter='\t', low_memory=False, on_bad_lines='skip', skiprows=possible_skipped_rows[counter])
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

	# Get the row numbers where Type is 'MSG'
	msg_rows = df[df['Type'] == 'MSG'].index

	# For each msg_row, split the df into two dataframes, one before the msg_row and one after
	# Run the analysis for each of those split dataframes as they represent different tasks
	last_task_name = None
	last_task_row_number = 0
	# Ignore the instruction tasks
	removed_task_names = {
		'instruction_calibration.jpg': True,
		'instruction_comprehension.jpg': True,
	}

	for msg_row in msg_rows:
		current_task_name = df['L Raw X [px]'][msg_row].split('Message: ')[1]
		# If the current task is an image name, it means that the current task has ended
		if '.jpg' in current_task_name:			
			if last_task_name is not None and last_task_name not in removed_task_names:
				
				df_msg = df[last_task_row_number:msg_row]
				# Remove all rows where the eye is invalid
				df_msg = df_msg[(df_msg['R Validity'] == 1)]

				# Define parameters for fixation detection
				x_right = df_msg.loc[:,('R POR X [px]')]
				df_msg.loc[:,('X')] = x_right

				y_left = df_msg['L Raw Y [px]']
				y_right = df_msg.loc[:,('R POR Y [px]')]
				df_msg.loc[:,('Y')] = y_right

				# Normalize time
				time = df_msg['Time'] - df_msg['Time'].min()
				# Time conversion from microseconds to milliseconds
				time = time / 1000

				participant_id = file_name.split('_')[0]
				fn(fixation_info, participant_id, time, x_right, y_right, last_task_name, parameters)

			last_task_name = current_task_name
			last_task_row_number = msg_row

		
	df_msg = df[last_task_row_number:]
	# Remove all rows at least one eye is invalid
	df_msg = df_msg[(df_msg['R Validity'] == 1)]

	# Define parameters for fixation detection
	x_left = df_msg['L Raw X [px]'].astype(float)
	x_right = df_msg['R POR X [px]'] 
	x = (x_left + x_right) / 2

	y_left = df_msg['L Raw Y [px]']
	y_right = df_msg['R POR Y [px]']
	y = (y_left + y_right) / 2
	# Normalize time
	time = df_msg['Time'] - df_msg['Time'].min()
	# Time conversion from microseconds to milliseconds
	time = time / 1000

	participant_id = file_name.split('_')[0]
	fn(fixation_info, participant_id, time, x_right, y_right, last_task_name)



def prepare_txt_data(directory_path, file_name, fixation_info, fn, parameters = {'missing': 0.0, 'maxdist': 25, 'mindur': 50}):
	# We only want the ogama txt files as those have the x and y coordinates
	if not 'ogama' in file_name:
		return
	txt_file = os.path.join(directory_path, file_name)

	path_elements = directory_path.split('/')
	participant_id = path_elements[-1]

	# Load the eye tracker data into a Pandas DataFrame
	df = pd.read_csv(txt_file, delimiter=',', low_memory=False, on_bad_lines='skip', encoding = "utf-16")
	df = df[[' ImageName', ' X', ' Y', ' StartTime', ' Included?', ' StimulusType']]

	df[' X'] = df[' X'] * 1920 / 1024
	df[' Y'] = df[' Y'] * 1080 / 768

	# Remove all rows where Included? == N
	df = df[df[' Included?'] == 'Y']

	df = df.fillna(0.0)

	
	# Iterate over all unique images
	for image_name in df[' ImageName'].unique():
		# Get the data for the current image
		image_df = df[df[' ImageName'] == image_name]

		# Call the defined fn
		fn(fixation_info, participant_id, image_df[' StartTime'], image_df[' X'], image_df[' Y'], image_name, parameters)
	

# Define the function to prepare the eyetracking data
ending_to_function = {
    '.tsv': prepare_tobii_data,
	'.txt': prepare_txt_data
}


def fixation_data_analysis(directory_path, output_csv = "pygaze_fixations.csv", parameters = {'missing': 0.0, 'maxdist': 25, 'mindur': 50}):

    # Initialize a dictionary to store the fixation counts, total fixation duration, and average fixation duration for each file
    fixation_info = {
        'Participant': [],
        'Task': [],
        'Fixation Count': [],
        'Total Fixation Duration [ms]': [],
        'Average Fixation Duration [ms]': []
    }


    # List all files in the directory and subfolders
    file_names = {}
    for root, dirs, files in os.walk(directory_path):
        dir_filenames = [file_name for file_name in files]
        file_names[root] = dir_filenames

    # Iterate over the files in the directory
    for directory, file_names in file_names.items():
        for file_name in file_names:
            ending = os.path.splitext(file_name)[1]
            if ending in ending_to_function:
                ending_to_function[ending](directory, file_name, fixation_info, call_fixation_detection_on_data, parameters)

    # Create a DataFrame to store the fixation information
    count_df = pd.DataFrame(fixation_info)

    # Write the DataFrame to a CSV file
    count_df.to_csv(output_csv, index=False)

    print(f"Fixation information saved to {output_csv}")
  

def saccade_data_analysis(directory_path, output_csv="pygaze_saccades.csv", parameters={'missing': 0.0, 'minlen': 5, 'maxvel': 40, 'maxacc': 340}):
    """
    Parameters:
        directory_path (str): The path to the directory containing the Tobii eye tracker data TSV files.

    Returns:
        pd.DataFrame: A DataFrame containing the saccade information for each file.
    """
    # Initialize a dictionary to store the saccade counts, total saccade duration, and average saccade duration for each file
    saccade_info = {
        'Participant': [],
        'Task': [],
        'Saccade Count': [],
        'Total Saccade Duration [ms]': [],
        'Average Saccade Duration [ms]': [],
        'Average Saccade Distance [px]': []
    }

    # List all files in the directory and subfolders
    file_names = {}
    for root, dirs, files in os.walk(directory_path):
        dir_filenames = [file_name for file_name in files]
        file_names[root] = dir_filenames

    # Iterate over the files in the directory
    for directory, file_names in file_names.items():
        for file_name in file_names:
            ending = os.path.splitext(file_name)[1]
            if ending in ending_to_function:
                ending_to_function[ending](directory, file_name, saccade_info, call_saccade_detection_on_data, parameters)
        
            

    # Create a DataFrame to store the saccade information
    count_df = pd.DataFrame(saccade_info)

    # Write the DataFrame to a CSV file
    count_df.to_csv(output_csv, index=False)

    # Print the saccade information
    print(f"Saccade information saved to {output_csv}")


