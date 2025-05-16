from django.db import models
from django import forms
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
import pandas as pd
from django.core.cache import cache
from django.conf import settings

class FinanceModel(models.Model):

    @staticmethod  
    def get_market_data(ticker, start_date, end_date):
        """
        Fetches market data for a given ticker symbol between specified start and end dates.
        """
        
        API_KEY = settings.ALPHA_VANTAGE_API_KEY

        full_cache_key = f"av_market_data_{ticker}"
        full_data = cache.get(full_cache_key)

        if full_data is not None:
            print(f"Using cached data for {ticker}")
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            filtered_data = full_data.loc[start_date:end_date]
            return filtered_data
        
        cache_key = f"av_market_data_{ticker}_{start_date}_{end_date}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            print(f"Using cached data for {ticker} from {start_date} to {end_date}")
            return cached_data
                
        try:
            print(ticker, start_date, end_date)
            if hasattr(start_date, 'strftime'):
                start_date = start_date.strftime('%Y-%m-%d')
            if hasattr(end_date, 'strftime'):
                end_date = end_date.strftime('%Y-%m-%d')

            series = TimeSeries(key=API_KEY, output_format='pandas') 

            data, meta_data = series.get_daily(symbol=ticker, outputsize='full')
            print(data)


            data_start = data.index.min()
            data_end = data.index.max()

            data_columns = data.columns.tolist()
            print(data_columns)
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

            if not isinstance(data.index, pd.DatetimeIndex):
                data.index = pd.to_datetime(data.index)

            data.index = pd.to_datetime(data.index)
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            data = data.sort_index()

            if start_date < data_start:
                print(f"Warning: Requested start date {start_date} is earlier than available data ({data_start})")
                start_date = data_start
                
            if end_date > data_end:
                print(f"Warning: Requested end date {end_date} is later than available data ({data_end})")
                end_date = data_end 
            filtered_data = data.loc[start_date:end_date]

            filtered_data.columns = pd.MultiIndex.from_product(
                [filtered_data.columns, [ticker]],
                names=['Price', 'Ticker']
            )

            cache.set(cache_key, filtered_data, timeout=86400)

            print(filtered_data)
            return filtered_data
          
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

    @staticmethod
    def get_basic_info(ticker):
        
        cache_key = f"av_basic_info_{ticker}"
        cached_info = cache.get(cache_key)
        if cached_info is not None:
            print(f"Using cached company info for {ticker}")
            return cached_info

        try:
            basic_info = FundamentalData(key=settings.ALPHA_VANTAGE_API_KEY, output_format='json')
            response = basic_info.get_company_overview(ticker)
            print(response)
            print(type(response))

            if isinstance(response, tuple) and len(response) > 0:
                data = response[0]
            else:
                data = response

            def convert_to_float(key, default="N/A"):
                try:
                    value = data.get(key)
                    if value is None or value == '':
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default

            def convert_to_int(key, default="N/A"):
                try:
                    value = data.get(key)
                    if value is None or value == '':
                        return default
                    return int(value)
                except (ValueError, TypeError):
                    return default
                
            info = {
                'symbol': ticker,
                'longName': data.get('Name', 'N/A'),
                'sector': data.get('Sector', 'N/A'),
                'industry': data.get('Industry', 'N/A'),
                'marketCap': convert_to_int('MarketCapitalization', 0),
                'beta': convert_to_float('Beta', 'N/A'),
                'fiftyTwoWeekHigh': convert_to_float('52WeekHigh', 'N/A'),
                'fiftyTwoWeekLow': convert_to_float('52WeekLow', 'N/A'),
                'currentPrice': convert_to_float('Price', 'N/A'),
                'forwardPE': convert_to_float('ForwardPE', 'N/A'),
                'dividendYield': convert_to_float('DividendYield', 0) * 100
                                if data.get('DividendYield') and data.get('DividendYield') != ''
                                else 'N/A'
            }
            print(info['marketCap'])
            print(type(info['marketCap']))

            if info['marketCap'] != 'N/A':
                if info['marketCap'] >= 10**9:
                    info['marketCap'] = f"{info['marketCap'] / 10**9:.2f}B"
                elif info['marketCap'] >= 10**6:
                    info['marketCap'] = f"{info['marketCap'] / 10**6:.2f}M"
                elif info['marketCap'] >= 10**3:
                    info['marketCap'] = f"{info['marketCap'] / 10**3:.2f}K"
            
            print(info['marketCap'])
            print(info)
            # Cache info for 1 day
            cache.set(cache_key, info, 86400)
            
            return info
        
        except Exception as e:
            print(f"Error fetching basic info for {ticker}: {e}")
            return None
        
        
class FinanceDataForm(forms.Form):
    """
    Form for fetching financial data from Yahoo Finance.
    """
    ticker = forms.CharField(
        label='Ticker Symbol',
        max_length=10
    )
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
        
    def __init__(self, *args, **kwargs):

        super(FinanceDataForm, self).__init__(*args, **kwargs)

        self.fields['ticker'].widget.attrs.update({'placeholder': 'e.g., AAPL'})
        self.fields['start_date'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        self.fields['end_date'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        