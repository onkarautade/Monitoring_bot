import requests
token = "7895806169:AAEpdSo_onClB0eY4jW3zlEc4FlQ4dSf3jM"
response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print(response.json())
