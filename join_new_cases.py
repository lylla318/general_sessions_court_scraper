import os
import csv
import simplejson as json
import time
import urllib3
import requests
import collections


class Joiner:

	def __init__(self, directory, output_file):

		self.directory   = directory
		self.output_file = output_file

		self.joined_data = self.join_data()

	# Read case numbers from CSV.
	def join_data(self):

		joined_data = []

		for filename in os.listdir(self.directory):
			print("Processing... " + str(filename))
			if (filename.endswith(".csv")):
				file = self.directory + "/" + filename
				with open(file) as csvfile:
					reader = csv.reader(csvfile)
					next(reader, None)
					next(reader, None)
					for row in reader:
						# print(row)
						joined_data.append(row)
				continue
			else:
				continue

		print(len(joined_data))
		with open(self.output_file, mode='a') as filename:
		    csvwriter = csv.writer(filename, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

		    for row in joined_data:
		    	if(len(row) > 2):
		   			csvwriter.writerow(row)

		return joined_data


if __name__ == '__main__':

	folder_name = "/Users/lyllayounes/Documents/LRN Docs/MLK50/court_scraping/input_data/new_cases" 
	output_file = "output_data/joined_2009_2011_new_cases.csv"
	joiner      = Joiner(folder_name, output_file)




# WHERE WE LEFT OFF: Collecting cases for 29-Nov-2017

