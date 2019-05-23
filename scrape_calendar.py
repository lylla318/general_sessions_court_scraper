import os
import csv
import simplejson as json
import time
import urllib3
import requests
import collections
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select




class Scraper:

	def __init__(self, year, no_data_file, case_list_csv):

		self.year            = year
		self.no_data_file    = no_data_file
		self.case_list_csv   = case_list_csv
		self.date_range      = self.generate_date_range()
		
		for i in range(0,6):
			print("Scraping division " + str(i+1) + "...")
			self.scrape_calendar(i)


	# Search for the page corresponding to a given case number.
	def scrape_calendar(self, option_no):

		# Set up the driver.
		chrome_path = os.path.realpath('chromedriver')
		chrome_options = Options()
		chrome_options.add_experimental_option("detach", True)
		driver = webdriver.Chrome(executable_path='/Users/lyllayounes/Documents/alaska_scraping/chromedriver', chrome_options=chrome_options)
		page = driver.get( 'https://apps.shelbycountytn.gov/GeneralSessions/calendars.xhtml' )
		
		# Go to case lookup.		
		radioBtn = driver.find_element_by_xpath('//*[@id="form:opt4"]')
		radioBtn.click()
		time.sleep(3)
		dropDownBtn = driver.find_element_by_xpath('//*[@id="form:dvc"]/div[3]')
		time.sleep(3)
		dropDownBtn.click()

		# Store data rows in dictionary
		cases_dict = collections.defaultdict(list)
		cases_list = []
		no_data = []

		# Select the dropdown button once it is availble
		dropdown = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'form:dvc_label')))
		options = dropdown.parent.find_elements_by_tag_name('li')

		with open(self.case_list_csv, mode='a') as csvfile, open(self.no_data_file, mode='a') as no_datafile:
		   	case_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		   	no_data_writer = csv.writer(no_datafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			time.sleep(3)

			dropdown = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'form:dvc_label')))
			options = dropdown.parent.find_elements_by_tag_name('li')
			time.sleep(3)
			options[option_no].click()

			# FOR TESTING ONLY #
			# self.date_range = ["01-Feb-2017"]
			for date in self.date_range:
				date_object = datetime.strptime(date, '%d-%b-%Y') #'2012-02-10'
				weekno = date_object.weekday()
				# Check for weekends
				if(weekno < 5):
					try:
						print("Collecting cases for " + date)
						# Enter date.
						searchbox = driver.find_element_by_id('form:date_input')
						searchbox.clear()
						searchbox.send_keys(date)
						button = driver.find_element_by_name('form:cal1')
						button.click()
						time.sleep(3)

						try:
							# Select largest row view per page.
							dropdown = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'form:test_rppDD')))
							options = dropdown.parent.find_elements_by_tag_name('option')
							options[2].click()
							time.sleep(3)

							# Grab number of pages.
							page_count = driver.find_element_by_id("form:test_paginator_top")
							idx = (page_count.text).index(")")
							num_pages = int(((((page_count.text)[0:idx+1]).split(" "))[-1]).replace(")","")) + 1

							#Iterate through the pages, scraping case information.
							for k in range(1,num_pages):
								# Click to the next page.
								if(k != 1):
									next_btn = page_count.find_element_by_class_name("ui-paginator-next")
									next_btn.click()
									time.sleep(1)
								html = driver.page_source
								soup = BeautifulSoup(html, features="html.parser")
								table = (soup.find("div", {"class":"ui-datatable-tablewrapper"})).find("table")
								for tr in table.findAll("tr"):
									tmp = [date]
									for td in tr.findAll("td"):
										tmp.append(str((td.text).strip()))
									cases_dict[date].append(tmp)
									cases_list.append(tmp)
									if(len(tmp) > 1):
										case_writer.writerow(tmp)

							driver.back()
						except:
							no_data_writer.writerow([date])
					except:
						print("IN EXCEPT")
						driver.close()
						driver = webdriver.Chrome(executable_path='/Users/lyllayounes/Documents/alaska_scraping/chromedriver', chrome_options=chrome_options)
						page = driver.get( 'https://apps.shelbycountytn.gov/GeneralSessions/calendars.xhtml' )
						# Go to case lookup.		
						radioBtn = driver.find_element_by_xpath('//*[@id="form:opt4"]')
						radioBtn.click()
						time.sleep(3)
						dropDownBtn = driver.find_element_by_xpath('//*[@id="form:dvc"]/div[3]')
						time.sleep(3)
						dropDownBtn.click()
						# Select the dropdown button once it is availble
						dropdown = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'form:dvc_label')))
						options = dropdown.parent.find_elements_by_tag_name('li')
				else:
					print(date)

		driver.close()


	# Generate list of all possible dates in calendar, from 01-Jan-2018 - present
	def generate_date_range(self):
		dates = []
		months = {"Jan":31, "Feb":28, "Mar":31, "Apr":30, "May":31, "Jun":30, "Jul":31, "Aug":31, "Sep":30, "Oct":31, "Nov":30, "Dec":31}

		for month in months.keys():
			for i in range(1,months[month]):
				day = "%02d" % (i,)
				dates.append(day + "-" + month + "-" + str(self.year))

		return dates




	# Convert data to string and clean whitespace
	def form_str(self, data):
		return str(data).strip()


	# Read case numbers from CSV.
	def read_case_numbers(self):

		case_nums = []
		with open(self.input_file) as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				x = row[0].replace("\xef\xbb\xbf","")
				case_nums.append(x.replace("\xc2\xa0",""))

		return case_nums

	# Write output.
	def write_data(self):
		with open(self.output_file, "w") as outfile:
			json.dump(self.case_data, outfile)
		


if __name__ == '__main__':

	no_data_file   = "output_data/no_data_list_v2.csv"
	case_list_csv  = "output_data/case_list_csv_1_v2.csv"
	year           = "2014"
	instance       = Scraper(year, no_data_file, case_list_csv)




# WHERE WE LEFT OFF: Collecting cases for 29-Nov-2017

