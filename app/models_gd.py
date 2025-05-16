import requests
import pandas as pd



class GDIMF():

    def __init__():
        pass

    @staticmethod
    def popular_countries_data():

        countries = [
            ('USA', 'United States'),
            ('CAN', 'Canada'),
            ('GBR', 'United Kingdom'),
            ('DEU', 'Germany'),
            ('FRA', 'France'),
            ('ITA', 'Italy'),
            ('ESP', 'Spain'),
            ('NLD', 'Netherlands'),
            ('CHE', 'Switzerland'),
            ('BEL', 'Belgium'),
            ('AUT', 'Austria'),
            ('DNK', 'Denmark'),
            ('NOR', 'Norway'),
            ('SWE', 'Sweden'),
            ('FIN', 'Finland'),
            ('IRL', 'Ireland'),
            ('AUS', 'Australia'),
            ('NZL', 'New Zealand'),
            ('JPN', 'Japan'),
            ('KOR', 'South Korea'),
            ('SGP', 'Singapore')
        ]
        countries_str = ','.join([country[0] for country in countries])
        data = {}
        
        url = f"https://www.imf.org/external/datamapper/api/v1/NGDPD/{countries_str}?periods=2024"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            gdp_data = json_data['values']['NGDPD']
            for code, country in countries:
                result = gdp_data[code]['2024']
                data[country] = round(result, 2)
        else:
            print(f"Failed to fetch data: {response.status_code}")
            
        df = pd.DataFrame(list(data.items()), columns=['Country', 'GDP (Billions USD)'])
        return df