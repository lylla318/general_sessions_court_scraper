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

	def __init__(self, input_file, output_file):

		self.input_file   = input_file
		self.output_file  = output_file
		self.case_numbers = self.read_case_numbers()
		self.scrape_garnishment_answers()


	# Search for the page corresponding to a given case number.
	def scrape_garnishment_reports(self):

		# Set up the driver.
		chrome_path = os.path.realpath('chromedriver')
		chrome_options = Options()
		chrome_options.add_experimental_option("detach", True)
		driver = webdriver.Chrome(executable_path='/Users/lyllayounes/Documents/alaska_scraping/chromedriver', chrome_options=chrome_options)
		page = driver.get( 'https://apps.shelbycountytn.gov/GeneralSessions/garnishments.xhtml' )

		with open(self.output_file, mode='a') as csvfile:

		   	writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

		   	i = 0
			for case_no in self.case_numbers.keys():

				if(i % 20 == 0): 
					print "Completed %s cases..." % i

				data_row = self.case_numbers[case_no]
		
				time.sleep(3)
				toggler = driver.find_element_by_xpath('//*[@id="j_idt44"]/legend/span') # //*[@id="j_idt44"]/legend/span
				toggler.click()
				time.sleep(3)

				searchbox = driver.find_element_by_xpath('//*[@id="form4:attIdTxtCG"]') # //*[@id="form4:attIdTxtCG"]
				searchbox.clear()
				time.sleep(1)
				searchbox.send_keys(unicode(case_no[-7:], errors='replace'))
				time.sleep(1)

				submit = driver.find_element_by_xpath('//*[@id="form4:gar4"]') # //*[@id="form4:gar3"] //*[@id="form4:gar4"]
				submit.click()
				time.sleep(1)

				html = driver.page_source
				soup = BeautifulSoup(html, features="html.parser")
				no_data = False

				try:
					form = ((soup.find("form")).find("div", {"id":"form:checkBoxGR"})).find("div", {"class":"ui-datatable-tablewrapper"})
					row  = form.find("table").find("tbody").find("tr")

					tmp  = data_row
					for td in row.findAll("td"):
						tmp.append(str(td.text))

					time.sleep(1)
					driver.back()
					print(tmp)
					writer.writerow(tmp)
				except:
					print("NO DATA")

				i += 1
		

		driver.close()



	# Search for the page corresponding to a given case number.
	def scrape_garnishment_answers(self):

		# Set up the driver.
		chrome_path = os.path.realpath('chromedriver')
		chrome_options = Options()
		chrome_options.add_experimental_option("detach", True)
		driver = webdriver.Chrome(executable_path='/Users/lyllayounes/Documents/alaska_scraping/chromedriver', chrome_options=chrome_options)
		page = driver.get( 'https://apps.shelbycountytn.gov/GeneralSessions/garnishments.xhtml' )

	   	i = 0
		for case_no in self.case_numbers.keys():

			if(i % 20 == 0): 
				print "Completed %s cases..." % i

			data_row = self.case_numbers[case_no]
	
			time.sleep(3)
			toggler = driver.find_element_by_xpath('//*[@id="j_idt44"]/legend/span') # //*[@id="j_idt44"]/legend/span
			toggler.click()
			time.sleep(3)

			searchbox = driver.find_element_by_xpath('//*[@id="form4:attIdTxtCG"]') # //*[@id="form4:attIdTxtCG"]
			searchbox.clear()
			time.sleep(1)
			searchbox.send_keys(unicode(case_no[-7:], errors='replace'))
			time.sleep(1)

			submit = driver.find_element_by_xpath('//*[@id="form4:gar4"]') # //*[@id="form4:gar3"] //*[@id="form4:gar4"]
			submit.click()
			time.sleep(1)

			html = driver.page_source
			soup = BeautifulSoup(html, features="html.parser")
			no_data = False

			try:
				form = ((soup.find("form")).find("div", {"id":"form:checkBoxGRA"})).find("div", {"class":"ui-datatable-tablewrapper"})
				row  = form.find("table").find("tbody").find("tr")

				tmp  = data_row
				for td in row.findAll("td"):
					tmp.append(str(td.text))

				time.sleep(1)

				with open(self.output_file, mode='a') as csvfile:
	   				writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
					writer.writerow(tmp)

				print("****")
				print(tmp)
				driver.back()
			except:
				print("NO DATA")

			i += 1
		

		driver.close()


	# Read case numbers from CSV.
	def read_case_numbers(self):

		case_nums = []
		case_dict = collections.defaultdict(list)
		with open(self.input_file) as csvfile:
			reader = csv.reader(csvfile)
			next(reader, None)
			for row in reader:
				case_nums.append(row[0])
				case_dict[row[0]] = row

		return case_dict

	# # Write output.
	# def write_data(self):
	# 	with open(self.output_file, "w") as outfile:
	# 		json.dump(self.case_data, outfile)
		


if __name__ == '__main__':

	input_file  = "input_data/garnishments_qa.csv"
	output_file = "output_data/garnishment_answers_qa_output.csv"
	instance    = Scraper(input_file, output_file)




# WHERE WE LEFT OFF: Collecting cases for 29-Nov-2017

