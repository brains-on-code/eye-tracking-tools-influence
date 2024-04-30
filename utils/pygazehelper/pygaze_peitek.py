import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from utils.pygazehelper.corrected_pygaze_functions import fixation_detection_fixed
from utils.peitek_opt import opt
import os


def analyze_csv_data_pygaze(res_path="results/pygaze_fixations_peitek.csv"):
	base_path = os.path.join(os.getcwd(), '../data/StudyPeitek/dataEvaluation/')
	path = os.path.join(base_path,'data/filteredData/filtered_data.csv')
	csv_file = os.path.join(os.getcwd(), path)
	df_behavioral = pd.read_csv(csv_file)
	df_fixation = pd.DataFrame([], columns=["Participant", "Algorithm", "Behavioral", "StartTime", "EndTime", "Duration", "IsOutlier", "SkillScore",
										"Fixation_startT", "Fixation_endT",  "Fixation_x", "Fixation_y", "Fixation_x_range", "Fixation_y_range"])
	#iterate through each row to generate fixation data
	for index, row in df_behavioral.iterrows():

		# print("Analyzing row", index, "of participants", row["Participant"])
		# read in eyetracking file
		eyetracking_file = row["Eyetracking"]
		# Exchange './' with the current working directory
		eyetracking_file = os.path.join(base_path, eyetracking_file[2:])
		df_eyetracking = pd.read_csv(eyetracking_file)
		# normalize the time regarding eyetracking to 0
		df_eyetracking["time"] = df_eyetracking["time"].astype(float)
		df_eyetracking["time"] = df_eyetracking["time"] - df_eyetracking["time"].iloc[0]

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

		missing = 0.0  # Specify the missing value threshold (if any)
		maxdist = 25  # Maximum distance for a fixation (adjust as needed)
		mindur = 50  # Minimum duration for a fixation (adjust as needed)

		# Perform fixation detection using the fixed fixation_detection function
		Sfix, Efix = fixation_detection_fixed(df_eyetracking["X"], df_eyetracking["Y"], df_eyetracking["time"], missing=missing, maxdist=maxdist, mindur=mindur)

		# save the fixation
		# extract meta data
		participant = row["Participant"]
		algorithm = row["Algorithm"]
		behavioral = row["Behavioral"]
		start_time = row["StartTime"]
		end_time = row["EndTime"]
		duration = row["Duration"]
		is_outlier = row["IsOutlier"]
		skill_score = row["SkillScore"]

		# extract fixation data
		fixations_start_time = np.array([entry[0] for entry in Efix])
		fixations_end_time = np.array([entry[1] for entry in Efix])
		fixations_x_pos = np.array([entry[3] for entry in Efix])
		fixations_y_pos = np.array([entry[4] for entry in Efix])
		fixations_x_range = np.array([0 for _ in Efix])
		fixations_y_range = np.array([0 for _ in Efix])

		# append data to dataframe
		df_fixation.loc[len(df_fixation)] = [participant, algorithm, behavioral, start_time, end_time, duration, is_outlier, skill_score,
											fixations_start_time, fixations_end_time, fixations_x_pos, fixations_y_pos, fixations_x_range, fixations_y_range]
		

	# Transform the lists to strings
	df_fixation["Fixation_startT"] = df_fixation["Fixation_startT"].astype(str)
	df_fixation["Fixation_endT"] = df_fixation["Fixation_endT"].astype(str)
	df_fixation["Fixation_x"] = df_fixation["Fixation_x"].astype(str)
	df_fixation["Fixation_y"] = df_fixation["Fixation_y"].astype(str)
	df_fixation["Fixation_x_range"] = df_fixation["Fixation_x_range"].astype(str)
	df_fixation["Fixation_y_range"] = df_fixation["Fixation_y_range"].astype(str)

	# Save the data
	df_fixation.to_csv(res_path, index=False, sep=";", float_format='{:f}'.format)

