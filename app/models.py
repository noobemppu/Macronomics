from django.db import models
from django import forms
import requests
import pandas as pd

# Create your models here.


class IMFData(models.Model):

    def __str__(self):
        return "IMF Data Model"

    @staticmethod
    def get_observation(country_code, indicator_code, frequency, start_date=None, end_date=None, series='IFS'):
        url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
        key = f'CompactData/{series}/{frequency}.{country_code}.{indicator_code}'
        if start_date and end_date:
            key += f'?startPeriod={start_date}&endPeriod={end_date}'
        print(key)
        
        response = requests.get(f'{url}{key}').json()
        print(response)  # Print the entire JSON response for debugging
        
        # Check for errors in the response
        if 'CompactData' not in response:
            raise ValueError("Invalid response structure: 'CompactData' key not found")
        
        compact_data = response['CompactData']
        dataset = compact_data.get('DataSet', None)
        if dataset is None:
            raise ValueError("Invalid response structure: 'DataSet' key not found")
        
        # Print the DataSet structure for debugging
        print("DataSet structure:", dataset)
        
        # Handle different structures of the DataSet
        series = dataset.get('Series', None)
        if series is None:
            # Check if Series is a list
            if isinstance(dataset, list):
                for item in dataset:
                    if 'Series' in item:
                        series = item['Series']
                        break
            if series is None:
                raise ValueError("No data found for the given country, indicator, and series codes")
        
        # Handle case where Series is a list of series
        if isinstance(series, list):
            series = series[0]
        
        # Extract observations
        observations = series.get('Obs', [])
        if not observations:
            raise ValueError("No observations found for the given country, indicator, and series codes")
        
        # Convert observations to a pandas DataFrame
        data = {
            'date': [obs['@TIME_PERIOD'] for obs in observations],
            'value': [obs['@OBS_VALUE'] for obs in observations]
        }
        df = pd.DataFrame(data)
        
        return df


def get_country_choices(search_term=''):
    try:
        url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CodeList/CL_AREA_IFS'
        response = requests.get(url, timeout=10).json()
        countries = response['Structure']['CodeLists']['CodeList']['Code']
        choices = [(country['@value'], country['Description']['#text']) for country in countries if search_term.lower() in country['Description']['#text'].lower()]
        return choices
    except Exception as e:
        print(f"Error fetching country choices: {e}")
        return [('', 'API Unreachable')]

def get_indicator_choices(search_term=''):
    try:
        url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CodeList/CL_INDICATOR_IFS'
        response = requests.get(url, timeout=10).json()
        indicators = response['Structure']['CodeLists']['CodeList']['Code']
        choices = [(indicator['@value'], indicator['Description']['#text']) for indicator in indicators if search_term.lower() in indicator['Description']['#text'].lower()]
        return choices
    except Exception as e:
        print(f"Error fetching indicator choices: {e}")
        return [('', 'API Unreachable')]


class IMFDataForm(forms.Form):
    country_code = forms.ChoiceField(label='Country', choices=[], widget=forms.Select(attrs={'id': 'country_code', 'class': 'form-control'}))
    indicator_code = forms.ChoiceField(label='Indicator', choices=[], widget=forms.Select(attrs={'id': 'indicator_code', 'class': 'form-control'}))
    frequency = forms.ChoiceField(label='Frequency', choices=[('M', 'Monthly'), ('A', 'Annual')], widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateField(label='Start Date', required=False, widget=forms.TextInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date = forms.DateField(label='End Date', required=False, widget=forms.TextInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(IMFDataForm, self).__init__(*args, **kwargs)
        # Only fetch choices when actually instantiating the form
        try:
            self.fields['country_code'].choices = get_country_choices()
            self.fields['indicator_code'].choices = get_indicator_choices()
            self.indicator_choices = dict(get_indicator_choices())
            self.country_choices = dict(get_country_choices())
        except Exception as e:
            # Fallback if API is unavailable
            self.fields['country_code'].choices = [('', 'API Unreachable')]
            self.fields['indicator_code'].choices = [('', 'API Unreachable')]
            self.indicator_choices = {}
            self.country_choices = {}
            print(f"Failed to fetch choices from IMF API: {e}")
        
        if 'country_search' in self.data:
            search_term = self.data.get('country_search', '')
            try:
                self.fields['country_code'].choices = get_country_choices(search_term)
            except Exception:
                pass
        
        if 'indicator_search' in self.data:
            search_term = self.data.get('indicator_search', '')
            try:
                self.fields['indicator_code'].choices = get_indicator_choices(search_term)
            except Exception:
                pass
        
        if 'indicator_code' in self.data:
            indicator_code = self.data.get('indicator_code')
            self.indicator_name = self.indicator_choices.get(indicator_code, 'Indicator')
        
        if 'country_code' in self.data:
            country_code = self.data.get('country_code')
            self.country_name = self.country_choices.get(country_code, country_code)