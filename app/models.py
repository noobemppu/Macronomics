from django.db import models
from django import forms
import pandas as pd
from datetime import datetime
import requests
import datacommons as dc
import datacommons_pandas as dc_pd

class DataCommonsData(models.Model):
    """
    Gets data from the Data Commons API.
    """

    @staticmethod
    def get_data_commons_data(country_code, indicator_code, frequency):
        """
        Retrieve observations from Data Commons which includes World Bank and IMF data.
        
        Parameters:
        - country_code: The country code (e.g., 'USA' for United States)
        - indicator_code: The indicator code (Data Commons Statistical Variable)
        - start_date: Optional start date filter (int year or datetime)
        - end_date: Optional end date filter (int year or datetime)
        
        Returns:
        - DataFrame with date and value columns
        """

        try:
            dcid = f"country/{country_code}"

            observation_period = None
            if frequency == 'A':
                observation_period = 'P1Y' 
            elif frequency == 'Q':
                observation_period = 'P3M'
            elif frequency == 'M':
                observation_period = 'P1M' 
            elif frequency == 'D':
                observation_period = 'P1D' 

            series_data = dc.get_stat_series(dcid, stat_var=indicator_code, observation_period=observation_period)

            if not series_data:
                place_id_alt = country_code
                series_data = dc.get_stat_series(place_id_alt, indicator_code, observation_period=observation_period)

                if series_data is None:
                    raise ValueError(f"Failed to find indicator {indicator_code} for country {country_code}")

            if isinstance(series_data, list):
                print("Creating df from a list")
                df = pd.DataFrame(series_data)
                df = df.sort_values('date')
                return df

            elif isinstance(series_data, dict):
                print("Creating df from a dict")
                records = []

                for key, value in series_data.items():
                    try:
                        pd.to_datetime(key)
                        records.append({'date': key, 'value': value})

                    except:
                        if isinstance(value, dict) and 'date' in value and 'value' in value:
                            records.append({'date': value['date'], 'value': value['value']})
                        elif isinstance(value, (int, float)) and key.isdigit():
                            records.append({'date': key, 'value': value})

                        else:
                            print('random format from response')

                df = pd.DataFrame(records)
                df = df.sort_values('date')
                return df


        except Exception as e:
            print(f"Failed to fetch data from Data Commons: {e}")
            return pd.DataFrame()

def get_indicators(country_code, category=''):
    """
    Get a list of indicators for user to choose from.
    """
    try:
        dcid = f"country/{country_code}"
        common_indicators = {
            'EconomicActivity': [
                ('Amount_EconomicActivity_GrossDomesticProduction_Nominal', 'GDP (Nominal)'),
                ('GrowthRate_Amount_EconomicActivity_GrossDomesticProduction', 'GDP Growth Rate'),
                ('Amount_EconomicActivity_GrossDomesticProduction_Nominal_PerCapita', 'Nominal GDP Per Capita'),
                #('sdg/FP_CPI_TOTL_ZG', 'Annual Inflation Rate (CPI)'),
                #('InflationAdjustedGDP', 'Inflation Adjusted Gross Domestic Production'),
                #('sdg/NE_EXP_GNFS_KD_ZG', 'Annual growth of exports of goods and services'),
                #('sdg/NE_IMP_GNFS_KD_ZG', 'Annual growth of imports of goods and services'),
                ('Amount_EconomicActivity_GrossNationalIncome_PurchasingPowerParity', 'Gross National Income Based on Purchasing Power Parity'),
                #('sdg/GC_BAL_CASH_GD_ZS', 'Cash surplus/deficit as a proportion of GDP')
            ], 
            'Population': [
                ('Count_Person', 'Total Population'),
                ('Count_Person_Rural', 'Rural Population'),
                ('Count_Person_Urban', 'Urban Population'),
                ('GrowthRate_Count_Person', 'Population Growth Rate'),
                ('LifeExpectancy_Person', 'Life Expectancy'),
                ('worldBank/SL_UEM_TOTL_NE_ZS', 'Unemployment, total (% of total labor force) (national estimate)')
            ],
            'Demographics': [
                ('Count_Person_Female', 'Female Population'),
                ('Count_Person_Male', 'Male Population')
            ]
        }
        
        """
        IN TEST
            'Debt': [
                ('Amount_Debt_Government', 'Government Debt'),
                ('Amount_Debt_Government_PerCapita', 'Government Debt Per Capita'),
                ('Percent_Debt_Government_GDP', 'Government Debt to GDP'),
                ('Amount_Debt_Household', 'Household Debt'),
                ('Amount_Debt_External', 'External Debt')
            ],
            'Employment': [
                ('UnemploymentRate_Person', 'Unemployment Rate'),
                ('Count_UnemploymentInsuranceClaim_PercentOfCoveredEmployment', 'Unemployment Insurance Claims'),
                ('Count_Person_Employed', 'Employed Persons'),
                ('Count_Person_InLaborForce', 'Labor Force'),
                ('Count_Job', 'Jobs'),
                ('GrowthRate_Count_Job', 'Job Growth Rate')
            ],
            'Income': [
                ('Median_Income_Person', 'Median Income'),
                ('Median_Income_Household', 'Median Household Income'),
                ('Percent_Person_BelowPovertyLevel', 'Poverty Rate'),
                ('GiniIndex_EconomicActivity', 'Gini Index'),
                ('Median_Earnings_Person_WithEarnings', 'Median Earnings')
            ],
            'Government': [
                ('Amount_Government_Revenue', 'Government Revenue'),
                ('Amount_Government_Expenditure', 'Government Expenditure'),
                ('Amount_Government_Deficit', 'Government Deficit')
            ],
            'Finance': [
                ('InterestRate_Discount', 'Discount Rate'),
                ('InterestRate_Market', 'Market Interest Rate'),
                ('Amount_Currency_Volume', 'Currency Volume'),
                ('Amount_Stock_Traded', 'Stock Traded Value'),
                ('MarketCapitalization_Stock', 'Stock Market Capitalization')
            ],
            'Trade': [
                ('Amount_EconomicActivity_ExportValue', 'Exports'),
                ('Amount_EconomicActivity_ImportValue', 'Imports'),
                ('Amount_EconomicActivity_GrossExternalDebt', 'Gross External Debt'),
                ('Amount_EconomicActivity_TradeBalance', 'Trade Balance'),
                ('Percent_ExportValue_GDP', 'Exports to GDP'),
                ('Percent_ImportValue_GDP', 'Imports to GDP')
            ]
        """
        indicators = []

        if category in common_indicators:
            indicators = common_indicators[category]
        
        return indicators


    except Exception as e:
        print(f"Failed to fetch indicators: {e}")
        indicators = []
        return indicators



class DataCommonsDataForm(forms.Form):
    """
    Django form for World Bank data retrieval interface.
    Provides fields for country, indicator, frequency and date range selection.
    """
    
    country_choices = [
        ('AFG', 'Afghanistan'),
        ('ALB', 'Albania'),
        ('DZA', 'Algeria'),
        ('AGO', 'Angola'),
        ('ARG', 'Argentina'),
        ('AUS', 'Australia'),
        ('AUT', 'Austria'),
        ('DEU', 'Germany'),
        ('USA', 'United States'),
        ('GBR', 'United Kingdom'),
    ]

    indicator_categories = [
        'EconomicActivity', 'Population', 'Demographics'
    ]

    # Country selection dropdown
    country_code = forms.ChoiceField(    
        label='Country',           
        label_suffix='',                
        choices=country_choices,                      
        widget=forms.Select(attrs={     
            'id': 'country_code',       
            'class': 'form-control'    
        })
    )

    indicator_category = forms.ChoiceField(
        label='Indicator Category',
        label_suffix='',
        choices=indicator_categories,
        widget=forms.Select(attrs={
            'id': 'indicator_category',
            'class': 'form-control'
        })
    )
    
    # Economic indicator selection dropdown
    indicator_code = forms.ChoiceField(
        label='Indicator',   
        label_suffix='',                         
        choices=[],                     
        widget=forms.Select(attrs={     
            'id': 'indicator_code',     
            'class': 'form-control'    
        })
    )
    
    # Data frequency selection dropdown
    frequency = forms.ChoiceField(
        label='Frequency',
        label_suffix='',              
        choices=[   
            ('A', 'annual'),
            ('Q', 'quarterly')
        ],    
        widget=forms.Select(attrs={     
            'class': 'form-control'     
        })
    )
    """
    # Start date selector
    start_date = forms.DateField(
        label='Start Date',             # Display label for the field
        required=False,                 # Not required (can be left blank)
        widget=forms.TextInput(attrs={  # Use a date input field
            'type': 'date',             # HTML5 date input type
            'class': 'form-control'     # Bootstrap styling class
        })
    )
    
    # End date selector
    end_date = forms.DateField(
        label='End Date',               # Display label for the field
        required=False,                 # Not required (can be left blank)
        widget=forms.TextInput(attrs={  # Use a date input field
            'type': 'date',             # HTML5 date input type
            'class': 'form-control'     # Bootstrap styling class
        })
    )
    """
    # Select graph type
    graph_type = forms.ChoiceField(
        label='Graph Type',
        label_suffix='',
        choices=[
            ('line', 'Line Graph'),
            ('bar', 'Bar Graph'),
            ('pie', 'Pie Chart')
        ],
        widget=forms.Select(attrs={     
            'class': 'form-control'     
        })
    )
    

    def __init__(self, *args, **kwargs):

        # Call the parent class __init__ method
        super(DataCommonsDataForm, self).__init__(*args, **kwargs)
        
        self.country_names = dict(self.country_choices)

        self.indicator_choices = {}
            
        self.fields['indicator_category'].choices = [(c, c) for c in self.indicator_categories]
        
        if 'country_code' in self.data:
            country_code = self.data.get('country_code')
            self.country_name = self.country_names.get(country_code, country_code)
            category = None
            if 'indicator_category' in self.data:
                category = self.data.get('indicator_category')

            try:
                indicator_list =  get_indicators(country_code, category or '')
                self.fields['indicator_code'].choices = indicator_list

                self.indicator_choices = dict(indicator_list)

            except Exception as e:
                print(f"Error fetching indicators: {e}")
                
        
        # Set indicator name attribute based on selected indicator code
        if 'indicator_code' in self.data:
            indicator_code = self.data.get('indicator_code')
            self.indicator_name = self.indicator_choices.get(indicator_code, indicator_code)