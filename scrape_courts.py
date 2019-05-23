import os
import csv
import simplejson as json
import time
import urllib3
import requests
import collections
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options 
from selenium.common.exceptions import TimeoutException


class Scraper:

	def __init__(self, input_file, output_file):

		self.input_file  = input_file
		self.output_file = output_file
		self.case_nums = self.read_case_numbers()
		self.case_data = collections.defaultdict(dict)
		self.cases_not_found = 0

		# self.case_nums = ["1HA-14-00014CR"] # TESTING

		for i in range(len(self.case_nums)):
			case = self.case_nums[i]
			print("Scraping case " + str(i) + " of " + str(len(self.case_nums)) + " cases, number " + case)
			try:
				self.case_data[case] = self.search(case)
			except:
				print("Error retrieving info.")
				self.case_data[case] = {}

			if(len((self.case_data[case]).keys()) == 0):
				self.cases_not_found += 1
		
		print("Cases not found: " + str(self.cases_not_found))
		self.write_data()



	# Search for the page corresponding to a given case number.
	def search(self, case_no):

		# Set up the driver.
		chrome_path = os.path.realpath('chromedriver')
		chrome_options = Options()
		chrome_options.add_experimental_option("detach", True)
		driver = webdriver.Chrome(executable_path='/Users/lyllayounes/Documents/alaska_scraping/chromedriver', chrome_options=chrome_options)
		page = driver.get( 'https://records.courts.alaska.gov/eaccess/home.page.2' )
		
		# Go to case lookup.
		button = driver.find_element_by_id('idb')
		button.click()

		# Wait for page load.
		try:
			driver.find_element_by_id('caseDscr')
		except:
			time.sleep(1)
				
		# Search for case.
		searchbox = driver.find_element_by_id('caseDscr')
		searchbox.send_keys(case_no)
		button = driver.find_element_by_name('submitLink')
		button.click()

		# Set up the new scraper.
		html = driver.page_source
		soup = BeautifulSoup(html, features="html.parser")
		base_url = "https://records.courts.alaska.gov/eaccess/search.page.3"
		fields = collections.defaultdict(dict)

		# Get the urls that match the case number and scrape the info.
		for link in soup.findAll("a"):

			if(link.text == case_no):

				try:
					button = driver.find_element_by_id('grid$row:1$cell:3$link')
					button.click()
				except:
					print("Waiting for page load...")

				# Wait for page load.
				try:
					driver.find_element_by_id('caseHeader')
				except:
					time.sleep(2)

				# Set up the new scraper.
				html = driver.page_source
				soup = BeautifulSoup(html, features="html.parser")

				# Scrape top panel.
				case_header = soup.find('div', {'id':'caseHeader'})
				for div in case_header.findAll('div', {'class': 'caseInfo-col3'}):
					for ul in div.findAll("ul"):
						lis =  ul.findAll("li")
						fields[lis[0].text] = lis[1].text

				# Scrape party information.
				party_info        = soup.find('div', {'id':'ptyContainer'})
				party_name        = party_info.findAll('div', {'class': 'ptyInfoLabel'})
				party_type        = party_info.findAll('div', {'class': 'ptyType'})
				party_dob_label   = party_info.findAll('div', {'class': 'ptyPersLabel'})
				party_dob         = party_info.findAll('div', {'class': 'ptyPersInfo'})
				party_atty_label  = party_info.select('li.ptyAttyLabel')
				party_atty_info   = party_info.select('li.ptyAttyInfo')

				fields["caseNum"] = case_no
				fields["party0"]["ptyType"] = (self.form_str(party_type[0].text)).replace("- ","")
				fields["party1"]["ptyType"] = (self.form_str(party_type[1].text)).replace("- ","")
				fields["party0"]["ptyName"] = self.form_str(party_name[0].text)
				fields["party1"]["ptyName"] = self.form_str(party_name[1].text)
				fields["party0"]["ptyDob"]  = self.form_str(party_dob[0].text)
				fields["party0"][self.form_str(party_atty_label[0].text)] = self.form_str(party_atty_info[0].text)
				fields["charges"] = []

				# Scrape charge information.
				charge_container = soup.find('div', {'id': 'chgContainer'})
				charges = charge_container.findAll('div', {'class': 'rowodd'}) + charge_container.findAll('div', {'class': 'roweven'})

				for charge in charges:	

					tmp = collections.defaultdict()

					# Grab charge header information.
					chrg_header = charge.find('div', {'class': 'subSectionHeader2'})

					if(chrg_header):

						tmp["defendantName"] = self.form_str(chrg_header.find('li', {'class':'ptyNameInfo'}).text)
						chrg_label = chrg_header.find('div', {"class":"chgLbl"})
						chrg_number = chrg_label.find("span", {"class", "chgHeadNum"})						
						tmp["chrgNumber"] = self.form_str(chrg_number.text)

						chrg_header_info  = chrg_header.find('div', {"class":"chrg"})
						tmp["chgAction"]  = self.form_str(chrg_header_info.find("span", {"class", "chgHeadActn"}).text)	
						tmp["chgDegree"]  = self.form_str(chrg_header_info.find("span", {"class", "chgHeadDeg"}).text)	
						tmp["chgDescription"] = self.form_str(chrg_header_info.find("span", {"class", "chgHeadDscr"}).text)	
						
					
						# Grab additoinal charge information.
						chrg_phase = charge.find('div', {'class': 'chgPhase'})
						chrg_offense = charge.find('div', {'class': 'chgOffense'})
						chrg_boxes = [chrg_phase, chrg_offense]

						for box in chrg_boxes:
							if(box):
								data_pane = box.find("li", {"class": "displayData"})
								if(data_pane):
									for ul in data_pane.findAll("ul"):
										label = self.form_str(ul.find("li", {"class":"ptyChgLabel"}).text)
										info  = self.form_str(ul.find("li", {"class":"ptyChgInfo"}).text)
										tmp[label] = info

						try:
							chrg_disposition = charge.find('div', {'class': 'chgDisp'})
							if(chrg_disposition):
								chrg_disposition = chrg_disposition.find({'div', 'chrDispContainer'})
								chrg_disposition = chrg_disposition.find('div', 'rowodd')
								disp_date = self.form_str((chrg_disposition.find('div', 'dspDtField')).text)
								disp_text = self.form_str((chrg_disposition.find('div', 'dspCdField')).text)
								tmp["dispDate"] = disp_date
								tmp["dispText"] = disp_text
							else:
								tmp["dispDate"] = "-"
								tmp["dispText"] = "missing"
						except:
							tmp["dispDate"] = "-"
							tmp["dispText"] = "missing"

						# Add charge to charge list.
						if(len(tmp.keys()) > 0):
							fields["charges"].append(tmp)

				# Get last event info
				events = soup.find("div", {"id": "eventInfo"})
				table_rows  = ((events.find("table")).find("tbody")).findAll("tr")
				last_event_data = (table_rows[-1]).findAll("td")
				event_fields = ["datetime", "location", "type", "result", "event_judge"]
				tmp = collections.defaultdict()
				for i in range(len(last_event_data)):
					tmp[event_fields[i]] = self.form_str(last_event_data[i].text)

				fields["lastEvent"] = tmp

		driver.close()

		return fields


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

	input_file  = "original_data/alaska_sex_crime_charges.csv"
	output_file = "output_data/output.json"
	instance = Scraper(input_file, output_file)

