from django.db import models
from django import forms
import yfinance as yf

class FinanceModel(models.Model):

    def get_market_data(ticker, start_date, end_date):
        """
        Fetches market data for a given ticker symbol between specified start and end dates.
        """
        try:
            print(ticker, start_date, end_date)
            if hasattr(start_date, 'strftime'):
                start_date = start_date.strftime('%Y-%m-%d')
            if hasattr(end_date, 'strftime'):
                end_date = end_date.strftime('%Y-%m-%d')

            # Fetch the data using yfinance
            data = yf.download(ticker, start=start_date, end=end_date)
            return data
        
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
        
    def get_basic_info(ticker):
        """
        Fetches basic information for a given ticker symbol.
        """
        try:
            basic_info = yf.Ticker(ticker).info
            print(basic_info)
            return basic_info
        
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
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
        
    def __init__(self, *args, **kwargs):

        super(FinanceDataForm, self).__init__(*args, **kwargs)

        self.fields['ticker'].widget.attrs.update({'placeholder': 'e.g., AAPL'})
        self.fields['start_date'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        self.fields['end_date'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        