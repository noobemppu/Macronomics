from django.db import models
from django import forms
import pandas as pd
import pandasdmx as sdmx
from datetime import datetime

# Import our cache manager from the cache_config module
from .cache_config import cache_manager

class IMFData(models.Model):
    """
    Django model for handling IMF data retrieval.
    This doesn't actually create a database table - it's just a container for methods.
    """
    
    def __str__(self):
        """Return a string representation of this model"""
        return "IMF Data Model"

@staticmethod
def get_observation(country_code, indicator_code, frequency, start_date=None, end_date=None, series='IFS', bypass_cache=False):
    """
    Retrieve observations from IMF using pandaSDMX with configurable caching.
    """
    try:
        # Choose the appropriate request object
        if bypass_cache:
            imf = cache_manager.get_fresh_request()
        else:
            imf = cache_manager.get_data_request()
        
        # Check which API version we're using
        if hasattr(cache_manager, 'api_version') and cache_manager.api_version == 'v2':
            # For v2 API, we might need a different key format
            # Try format 1 (newer):
            try:
                # Format might be different for v2
                key = f"{country_code}.{indicator_code}.{frequency}"
                
                params = {}
                if start_date:
                    params['startPeriod'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else str(start_date)
                if end_date:
                    params['endPeriod'] = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else str(end_date)
                
                data_response = imf.data(resource_id=series, key=key, params=params)
                df = data_response.to_pandas()
            except Exception as e:
                print(f"First format attempt failed: {e}, trying traditional format...")
                # Fall back to traditional format
                key = {
                    'FREQ': frequency,
                    'REF_AREA': country_code,
                    'INDICATOR': indicator_code
                }
                
                params = {}
                if start_date:
                    params['startPeriod'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else str(start_date)
                if end_date:
                    params['endPeriod'] = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else str(end_date)
                
                data_response = imf.data(resource_id=series, key=key, params=params)
                df = data_response.to_pandas()
        else:
            # Use the original approach for legacy API
            key = {
                'FREQ': frequency,
                'REF_AREA': country_code,
                'INDICATOR': indicator_code
            }
            
            params = {}
            if start_date:
                params['startPeriod'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else str(start_date)
            if end_date:
                params['endPeriod'] = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else str(end_date)
            
            data_response = imf.data(resource_id=series, key=key, params=params)
            df = data_response.to_pandas()
            
            # Check if the dataframe is empty (no data found)
            if df.empty:
                raise ValueError("No observations found for the given parameters")
            
            # Process the dataframe to match the expected format
            # SDMX returns a multi-index dataframe, so we need to reset and rename
            df = df.reset_index()
            
            # Initialize variables to store detected column names
            time_col = None
            value_col = None
            
            # Find the time and value columns in the returned dataframe
            # Column names in SDMX responses can vary, so we need to detect them
            for col in df.columns:
                # Look for column names containing 'TIME_PERIOD' for date
                if 'TIME_PERIOD' in col:
                    time_col = col
                # For value column, find one that's not a dimension column
                elif not any(dim in col for dim in ['REF_AREA', 'INDICATOR', 'FREQ']):
                    value_col = col
            
            # If we couldn't find columns with the expected naming convention, try alternatives
            if not time_col or not value_col:
                # Try to find date columns based on common naming patterns
                time_candidates = [col for col in df.columns if 'TIME' in col or 'DATE' in col or 'PERIOD' in col]
                if time_candidates:
                    time_col = time_candidates[0]
                
                # For value column, look for any numeric column that isn't the time column
                for col in df.columns:
                    if col != time_col and pd.api.types.is_numeric_dtype(df[col]):
                        value_col = col
                        break
            
            # If we still don't have the needed columns, we can't process the data
            if not time_col or not value_col:
                raise ValueError("Could not identify time or value columns in response")
            
            # Create a new dataframe with standardized column names
            # This ensures consistent column names regardless of the API response format
            result_df = pd.DataFrame({
                'date': df[time_col],   # Standardize the date column name
                'value': df[value_col]  # Standardize the value column name
            })
            
            # Return the processed dataframe
            return result_df
            
    except Exception as e:
        # Log the error for debugging purposes
        print(f"SDMX Error: {e}")
        # Raise a ValueError with a more user-friendly message
        raise ValueError(f"Error fetching data: {e}")


def get_country_choices(search_term=''):
    """
    Get list of country codes and names from IMF using pandaSDMX.
    Uses the metadata cache (7-day expiration).
    
    Parameters:
    - search_term: Optional text to filter countries by name
    
    Returns:
    - A list of tuples (country_code, country_name) suitable for Django form choices
    """
    try:
        # Get the metadata request object with longer cache duration
        imf = cache_manager.get_metadata_request()
        
        # Check which API version we're using to adjust our approach
        if hasattr(cache_manager, 'api_version') and cache_manager.api_version == 'v2':
            # For v2 API
            response = imf.dataflow('IFS')
            structure = response.structure[0]  # Get the first structure
            
            # Look for the country codelist in the structure
            area_codelist = None
            for cl in structure.codelists:
                if cl.id == 'CL_AREA_IFS':
                    area_codelist = cl
                    break
            
            # If we couldn't find the codelist, try a direct approach
            if not area_codelist:
                # Try to get the codelist directly
                codelist_response = imf.codelist('CL_AREA_IFS')
                area_codelist = codelist_response.codelist[0]
        else:
            # For legacy API, use the original approach
            response = imf.dataflow('IFS')
            structure = response.structure[0]  # Get the first structure
            
            # Look for the country codelist in the structure
            area_codelist = None
            for cl in structure.codelists:
                if cl.id == 'CL_AREA_IFS':
                    area_codelist = cl
                    break
        
        # If we still couldn't find the codelist, raise an error
        if not area_codelist:
            raise ValueError("Country codelist not found")
        
        # Convert codelist items to Django form choices format
        choices = []
        for code in area_codelist.items.values():
            # If a search term is provided, filter by it
            if search_term.lower() in code.name.lower():
                # Add tuple of (code_id, code_name) to choices
                choices.append((code.id, code.name))
        
        # Return choices sorted alphabetically by country name
        return sorted(choices, key=lambda x: x[1])
    except Exception as e:
        # Log the error and return a fallback value
        print(f"SDMX Error fetching country choices: {e}")
        # Return a single option indicating the API is unreachable
        return [('', 'API Unreachable')]


def get_indicator_choices(search_term=''):
    """
    Get list of indicator codes and names from IMF using pandaSDMX.
    Uses the metadata cache (7-day expiration).
    
    Parameters:
    - search_term: Optional text to filter indicators by name
    
    Returns:
    - A list of tuples (indicator_code, indicator_name) suitable for Django form choices
    """
    try:
        # Get the metadata request object with longer cache duration
        imf = cache_manager.get_metadata_request()
        
        if hasattr(cache_manager, 'api_version') and cache_manager.api_version == 'v2':
            # Get the dataflow structure which contains code lists
            response = imf.dataflow('IFS')
            # Get the first structure from the response
            structure = response.structure[0]
            
            # Look for the indicator codelist in the structure
            indicator_codelist = None
            for cl in structure.codelists:
                # Find the codelist with the specific ID for indicators
                if cl.id == 'CL_INDICATOR_IFS':
                    indicator_codelist = cl
                    break
        
        else:
            # For legacy API, use the original approach
            response = imf.dataflow('IFS')
            structure = response.structure[0]  # Get the first structure
            
            # Look for the country codelist in the structure
            area_codelist = None
            for cl in structure.codelists:
                if cl.id == 'CL_AREA_IFS':
                    area_codelist = cl
                    break

        # If we couldn't find the codelist, raise an error
        if not indicator_codelist:
            raise ValueError("Indicator codelist not found")
            
        # Convert codelist items to Django form choices format
        choices = []
        for code in indicator_codelist.items.values():
            # If a search term is provided, filter by it
            if search_term.lower() in code.name.lower():
                # Add tuple of (code_id, code_name) to choices
                choices.append((code.id, code.name))
            
        # Return choices sorted alphabetically by indicator name
        return sorted(choices, key=lambda x: x[1])
    except Exception as e:
        # Log the error and return a fallback value
        print(f"SDMX Error fetching indicator choices: {e}")
        # Return a single option indicating the API is unreachable
        return [('', 'API Unreachable')]


class IMFDataForm(forms.Form):
    """
    Django form for IMF data retrieval interface.
    Provides fields for country, indicator, frequency and date range selection.
    """
    
    # Country selection dropdown
    country_code = forms.ChoiceField(
        label='Country',                # Display label for the field
        choices=[],                     # Empty initially, populated in __init__
        widget=forms.Select(attrs={     # Use a select dropdown with custom attributes
            'id': 'country_code',       # HTML id for the field
            'class': 'form-control'     # Bootstrap styling class
        })
    )
    
    # Economic indicator selection dropdown
    indicator_code = forms.ChoiceField(
        label='Indicator',              # Display label for the field
        choices=[],                     # Empty initially, populated in __init__
        widget=forms.Select(attrs={     # Use a select dropdown with custom attributes
            'id': 'indicator_code',     # HTML id for the field
            'class': 'form-control'     # Bootstrap styling class
        })
    )
    
    # Data frequency selection dropdown
    frequency = forms.ChoiceField(
        label='Frequency',              # Display label for the field
        choices=[                       # Fixed choices for frequency
            ('M', 'Monthly'),           # Monthly data
            ('A', 'Annual')             # Annual data
        ],
        widget=forms.Select(attrs={     # Use a select dropdown with custom attributes
            'class': 'form-control'     # Bootstrap styling class
        })
    )
    
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
    
    # Cache bypass option
    refresh_data = forms.BooleanField(
        label='Refresh data (bypass cache)',  # Display label for the checkbox
        required=False,                       # Not required (can be unchecked)
        initial=False,                        # Unchecked by default
        widget=forms.CheckboxInput(attrs={    # Use a checkbox input
            'class': 'form-check-input'       # Bootstrap styling class
        })
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and populate dynamic choice fields.
        This method runs when creating a new form instance.
        """
        # Call the parent class __init__ method
        super(IMFDataForm, self).__init__(*args, **kwargs)
        
        # Populate the country and indicator dropdowns with choices from the API
        try:
            # Get country choices from the API and set them in the form field
            self.fields['country_code'].choices = get_country_choices('')
            # Get indicator choices from the API and set them in the form field
            self.fields['indicator_code'].choices = get_indicator_choices('')
            
            # Create dictionaries for easier lookup of names by code
            # These will be used later to display full names instead of codes
            self.indicator_choices = dict(get_indicator_choices(''))
            self.country_choices = dict(get_country_choices(''))
        except Exception as e:
            # If API fails, set empty/fallback choices
            self.fields['country_code'].choices = [('', 'API Unreachable')]
            self.fields['indicator_code'].choices = [('', 'API Unreachable')]
            self.indicator_choices = {}
            self.country_choices = {}
            # Log the error
            print(f"Failed to fetch choices from IMF API: {e}")
        
        # Handle country search if present in the request
        if 'country_search' in self.data:
            search_term = self.data.get('country_search', '')
            try:
                # Update the country choices based on search term
                self.fields['country_code'].choices = get_country_choices(search_term)
            except Exception as e:
                # Log any errors during search
                print(f"Error during country search: {e}")
        
        # Handle indicator search if present in the request
        if 'indicator_search' in self.data:
            search_term = self.data.get('indicator_search', '')
            try:
                # Update the indicator choices based on search term
                self.fields['indicator_code'].choices = get_indicator_choices(search_term)
            except Exception as e:
                # Log any errors during search
                print(f"Error during indicator search: {e}")
        
        # Set indicator name attribute based on selected indicator code
        if 'indicator_code' in self.data:
            indicator_code = self.data.get('indicator_code')
            # Look up the full name for the selected code or use 'Indicator' as fallback
            self.indicator_name = self.indicator_choices.get(indicator_code, 'Indicator')
        
        # Set country name attribute based on selected country code
        if 'country_code' in self.data:
            country_code = self.data.get('country_code')
            # Look up the full name for the selected code or use the code itself as fallback
            self.country_name = self.country_choices.get(country_code, country_code)