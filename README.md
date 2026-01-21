# Smart Cashier: Weather-Aware Data

A lightweight, desktop-based cashier application built with **Python** and **PySide6**. This project goes beyond basic CRUD operations by integrating real-time weather data 
to provide contextual insights into sales patterns.

## Features
- **Menu Management**: Easily add and manage your shop's menu and pricing.
- **Shopping Cart System**: Add multiple items, calculate subtotal, and manage quantities before processing payments.
- **Weather Integration**: Automatically fetches and logs real-time weather conditions for every transaction using the OpenWeatherMap API.
- **Daily Omset Log**: Track income, operational expenses, and net profit with a calendar-based interface.
- **Data Persistence**: All records are stored locally in a JSON-based database for easy access.

## Tech Stack
- **Language**: Python
- **GUI Framework**: PySide6 (Qt for Python)
- **API**: OpenWeatherMap API
- **Storage**: JSON

## Prerequisites
Before running the application, ensure you have the following installed:
- Python 3.x
- PySide6
- `pip` (Python package manager)

## Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/kim-sana/Smart-Cashier-Weather-Aware-Data.git](https://github.com/kim-sana/Smart-Cashier-Weather-Aware-Data.git)
   cd Smart-Cashier-Weather-Aware-Data



2. **Install Dependencies**
Install the required Python libraries:
```bash
pip install PySide6 requests python-dotenv

```


3. **Configure API Key**
To enable weather tracking, you need an API key from OpenWeatherMap (https://openweathermap.org/api):
* Create a file named `.env` in the root directory.
* <img width="761" height="45" alt="image" src="https://github.com/user-attachments/assets/47239da9-e63f-4fe3-9705-100f05ef47e6" />

* Add your API key to the file in the following format:
```text
WEATHER_API_KEY=your_api_key_here

```





## How to Use

Run the application using the following command:

```bash
python kasir.py

```

* **Adding Menu**: Use the "+ Menu Baru" button to populate your catalog.
* **Transactions**: Select items from the dropdown, set the quantity, and click "PROSES & BAYAR" to save the transaction along with the current weather.
* **Viewing Logs**: Switch to the "LOG OMSET" tab and select a date on the calendar to see that day's financial summary.

## Project Structure

* `kasir.py`: The main application script.
* `kasir_data.json`: Local database file
* `.env`: Configuration file for API credentials

## Bonus
you can package the code into singular exe file if you have pyinstaller.



```bash
pip install pyinstaller

pyinstaller --noconsole --onefile --icon=icon.ico --name=Kasir-Warung-Kak-San kasir.py
```

*Developed as part of the Visual Programming coursework (Semester 3).*
