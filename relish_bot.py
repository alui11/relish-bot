#!/Library/Developer/CommandLineTools/usr/bin/python3

#TODO: prices

import datetime
from getpass import getpass
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import sys
import time

emailll = input("Email: ")
passwordd = getpass()

def element_exists(parent, xpath):
  try:
      parent.find_element(By.XPATH, "." + xpath)
  except NoSuchElementException:
      return False
  return True

def click_when_available(driver, xpath):
  wait_start = time.perf_counter()
  while not element_exists(driver, xpath):
    if time.perf_counter() - wait_start > 10:
      print("Error: Timed out while waiting for page to load. How's your internet connection?")
      sys.exit()
  driver.find_element(By.XPATH, xpath).click()

def get_headless_options():
  options = Options()
  options.add_argument("--headless")
  options.add_argument("--disable-gpu")
  options.add_argument("--window-size=1920,1200")
  options.add_argument("--ignore-certificate-errors")
  options.add_argument("--disable-extensions")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  return options

def log_in(driver):
  driver.get("https://www.getrelish.com/schedule")
  email = driver.find_element(By.ID, "identity_email")
  password = driver.find_element(By.ID, "identity_password")
  email.send_keys(emailll)
  password.send_keys(passwordd)
  sign_in_button = driver.find_element(By.XPATH, "//input[@name='commit' and @value='Sign in']")
  sign_in_button.click()

  try:
    pop_up_button = driver.find_element(By.XPATH, "//button[@aria-label='Close modal' and @class='button' and @data-close]")
    pop_up_button.click()
  except NoSuchElementException:
    pass

def order(driver, date, meal):
  driver.get("https://www.getrelish.com/schedule/"+ date)
  restaurants = driver.find_elements(By.XPATH, f"//div[@data-role='meal-type-{meal}']/div[contains(@id, 'se-')]")
  if element_exists(restaurants[0], "//div[contains(@class, 'card-order-placed')]"):
    print(meal.capitalize() + " for " + date + " already ordered. Aborting.")
    return
  if element_exists(driver, f"//div[@data-role='meal-type-{meal}']//div[contains(text(), 'Time')]"):
    print("Too slow. You snooze you lose.")
    return
  restaurant_links = []
  for restaurant in restaurants:
    if element_exists(restaurant, "//a"):
      restaurant_links.append(restaurant.find_element(By.TAG_NAME, "a").get_attribute("href"))
  meal_options = []
  for link in restaurant_links:
    driver.get(link)
    first_menu_cell = driver.find_element(By.XPATH, "//div[@class='menu-items']/div[@class='grid-x menu-category-container']")
    if element_exists(first_menu_cell, "//div[@id='previously-ordered']"):
      prev_ordered_items = first_menu_cell.find_elements(By.XPATH, "./div[contains(@class, 'menu-item-items')]/div[@class='cell']")
      for item in prev_ordered_items:
        item_name = item.find_element(By.XPATH, ".//div[@class='cell-header']").get_attribute("textContent")
        item_link = link #item.find_element(By.XPATH, ".//a").get_attribute("href")
        meal_options.append((item_name, item_link))
  for i, item in enumerate(meal_options):
    print(str(i+1) + ". " + item[0].strip().rstrip())
  choice = input("Choice [0 for nothing, anything for random]: ")
  try:
    choice = int(choice)
    if choice == 0:
      print("Skipping this meal.")
      return
    if choice in range(1,len(meal_options)+1):
      chosen_meal = meal_options[choice-1]
    else:
      chosen_meal = random.choice(meal_options)
  except ValueError:
    chosen_meal = random.choice(meal_options)
  print("Chose " + chosen_meal[0].strip().rstrip())
  driver.get(chosen_meal[1])
  first_menu_cell = driver.find_element(By.XPATH, "//div[@class='menu-items']/div[@class='grid-x menu-category-container']")
  chosen_meal_cell = first_menu_cell.find_element(By.XPATH, f"./div[contains(@class, 'menu-item-items')]/div[.//div[contains(text(), '{chosen_meal[0]}')]]")
  chosen_meal_cell.find_element(By.XPATH, ".//a").click()
  #click_when_available(driver, f"//div[@class='menu-items']/div[@class='grid-x menu-category-container']/div[contains(@class, 'menu-item-items')]/div[.//div[contains(text(), '{chosen_meal[0]}')]]//a")
  click_when_available(driver, "//form[@id='new_order_item']//input[@name='commit' and @value='Add to cart']")
  click_when_available(driver, "//a[text()='Proceed to Checkout']")
  click_when_available(driver, "//input[@name='commit' and contains(@value, 'Place Order')]")
  print("Success")

def main():
  print("Launching Chrome...")
  try:
    driver = webdriver.Chrome(options=get_headless_options())
  except:
    # TODO: instructions for installing chromedriver.
    print("Error: Could not connect to Chrome. You probably need to install chromedriver.")
    sys.exit()
  print("Logging in " + emailll + " to getrelish.com...")
  log_in(driver)
  print("Login successful.")
  today = datetime.datetime.today()
  date_list = [today + datetime.timedelta(days=x) for x in range(7)]
  for date in date_list:
    if date.weekday() in [5, 6]:
      continue
    datestr = date.strftime("%Y-%m-%d")
    for meal in ["lunch", "dinner"]:
      print("Ordering " + meal + " for " + datestr + "...")
      order(driver, datestr, meal)

if __name__ == "__main__":
  main()
