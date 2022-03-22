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


def replace_last(input_str, old, new):
  return new.join(input_str.rsplit(old, 1))

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


def log_in(driver, email, password):
  driver.get("https://www.getrelish.com/schedule")
  email_box = driver.find_element(By.ID, "identity_email")
  password_box = driver.find_element(By.ID, "identity_password")
  email_box.send_keys(email)
  password_box.send_keys(password)
  sign_in_button = driver.find_element(By.XPATH, "//input[@name='commit' and @value='Sign in']")
  sign_in_button.click()
  
  login_successful = False
  try:
    driver.find_element(By.XPATH, "//input[@name='commit' and @value='Sign in']")
    print("Login failed. Wrong email or password. If this has happened >5 times your account might be locked.")
  except:
    login_successful = True
  if not login_successful:
    sys.exit()

  try:
    pop_up_button = driver.find_element(By.XPATH, "//button[@aria-label='Close modal' and @class='button' and @data-close]")
    pop_up_button.click()
  except NoSuchElementException:
    pass

  print("Login successful.")

class Restaurant():
  def __init__(self, name, link):
    self.name = name
    self.link = link

class Meal():
  def __init__(self, name, restaurant, price):
    self.true_name = name
    self.display_name = name.strip().rstrip()
    self.restaurant = restaurant
    self.price = price

def order(driver, date, meal):
  datestr = date.strftime("%Y-%m-%d")
  driver.get("https://www.getrelish.com/schedule/"+ datestr)
  restaurant_cards = driver.find_elements(By.XPATH, f"//div[@data-role='meal-type-{meal}']/div[contains(@id, 'se-')]")
  if not len(restaurant_cards):
    print("Found no restaurants on " + datestr + " for " + meal + ". This is unexpected.")
    return
  if element_exists(restaurant_cards[0], "//div[contains(@class, 'card-order-placed')]"):
    print(meal.capitalize() + " for " + datestr + " already ordered. Skipping.")
    return
  if element_exists(driver, f"//div[@data-role='meal-type-{meal}']//div[contains(text(), 'Time')]"):
    print("Too late to order " + meal + " for " + datestr + ". Skipping.")
    return

  restaurants = []
  for restaurant_card in restaurant_cards:
    name_and_tag = restaurant_card.find_element(By.XPATH, ".//h2").text
    tag_text = restaurant_card.find_element(By.XPATH, ".//h2/div").text
    name = replace_last(name_and_tag, tag_text, "").strip()
    if element_exists(restaurant_card, "//a"):
      link = restaurant_card.find_element(By.TAG_NAME, "a").get_attribute("href")
      restaurants.append(Restaurant(name, link))
  if not len(restaurants):
    print("No available restaurants for " + meal + " on " + datestr + ". It may be too late to order or they may be sold out.")
    return

  meal_options = []
  for restaurant in restaurants:
    driver.get(restaurant.link)
    first_menu_cell = driver.find_element(By.XPATH, "//div[@class='menu-items']/div[@class='grid-x menu-category-container']")
    if element_exists(first_menu_cell, "//div[@id='previously-ordered']"):
      prev_ordered_items = first_menu_cell.find_elements(By.XPATH, "./div[contains(@class, 'menu-item-items')]/div[@class='cell']")
      for item in prev_ordered_items:
        item_name = item.find_element(By.XPATH, ".//div[@class='cell-header']").get_attribute("textContent")
        item_price = float(item.find_element(By.XPATH, ".//span[@class='menu-item-price']").get_attribute("innerText")[1:])
        meal_options.append(Meal(item_name, restaurant, item_price))
  if not len(meal_options):
    print("You have never ordered from any of the available restaurants. Skipping this meal.")
    return

  for i, meal in enumerate(meal_options):
    print(f"{i+1}. {meal.display_name} ({meal.restaurant.name}) ${meal.price:.2f}")
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
  print("Chose " + chosen_meal.display_name)
  driver.get(chosen_meal.restaurant.link)
  first_menu_cell = driver.find_element(By.XPATH, "//div[@class='menu-items']/div[@class='grid-x menu-category-container']")
  chosen_meal_cell = first_menu_cell.find_element(By.XPATH, f"./div[contains(@class, 'menu-item-items')]/div[.//div[contains(text(), '{chosen_meal.true_name}')]]")
  chosen_meal_cell.find_element(By.XPATH, ".//a").click()
  click_when_available(driver, "//form[@id='new_order_item']//input[@name='commit' and @value='Add to cart']")
  click_when_available(driver, "//a[text()='Proceed to Checkout']")
  click_when_available(driver, "//input[@name='commit' and contains(@value, 'Place Order')]")
  print("Success")


def main():
  email = input("Email: ")
  password = getpass()

  print("Launching Chrome...")
  try:
    driver = webdriver.Chrome(options=get_headless_options())
  except:
    # TODO: instructions for installing chromedriver.
    print("Error: Could not connect to Chrome. You probably need to install chromedriver.")
    sys.exit()
  print("Logging in " + email + " to getrelish.com...")
  log_in(driver, email, password)
  today = datetime.datetime.today()
  date_list = [today + datetime.timedelta(days=x) for x in range(2)]
  for date in date_list:
    if date.weekday() in [5, 6]:
      continue
    for meal in ["lunch", "dinner"]:
      print()
      print(f"Ordering {meal} for {date.strftime('%A')} ({date.strftime('%m/%d')})...")
      order(driver, date, meal)

if __name__ == "__main__":
  main()
