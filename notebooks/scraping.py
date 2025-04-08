# Scraping libraries
import requests
from bs4 import BeautifulSoup
import urllib

url = "https://casas.trovit.com.co/arriendo-valle-aburra"
response = requests.get(url)

print(response.status_code) # Conexion exitosa

# Se guarda la response en una variable para luego verla 
html_content = response.text
with open("page_1.txt", "w", encoding='utf-8') as file:
    file.write(html_content)
    print('HTML Content has been saved succcesfully')

html_content[:100]
soup = BeautifulSoup(response.text, features='html.parser')

soup('a')

