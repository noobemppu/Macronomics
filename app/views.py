# Standard library imports
import csv
import datetime
import io
import json
import os

# Third-party imports
import pandas as pd
import datacommons as dc
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# Django imports
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

# Local application imports
from .models import DataCommonsData, DataCommonsDataForm, get_indicators  
from .models_finance import FinanceModel, FinanceDataForm  

def main_page(request):
    """
    Render the main landing page of the application.
    """
    # Simply render the main page template
    return render(request, 'main_page.html')


def datacommons_data(request):
    """
    View for displaying IMF data query form and results.
    Handles both GET requests (show empty form) and POST requests (process form and show results).
    """
    print(f"Request method: {request.method}, is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print(f"POST data: {request.POST}")
    
    error_message = None  
    graph = None          

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST' and is_ajax:
        action = request.POST.get('action', '')
        country_code = request.POST.get('country_code', '')

        if action == 'get_indicators':
            category = request.POST.get('indicator_category', '') 

            try:
                indicators = get_indicators(country_code, category)
                return JsonResponse({
                    'success': True,
                    'indicators': indicators
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            

    if request.method == 'POST' and not is_ajax:
        # Create a form instance with the submitted data
        form = DataCommonsDataForm(request.POST)
        
        # Validate the form data
        if form.is_valid():
            # Extract all the form fields
            country_code = form.cleaned_data['country_code']         
            country_name = form.country_name                        
            indicator_name = f"{form.indicator_name} - {country_name}"
            indicator_category = form.cleaned_data['indicator_category']  
            indicator_code = form.cleaned_data['indicator_code']     
            frequency = form.cleaned_data['frequency']               
            #start_date = form.cleaned_data['start_date']             
            #end_date = form.cleaned_data['end_date']
            graph_type = form.cleaned_data['graph_type']             
            
            try:
                data = DataCommonsData.get_data_commons_data(country_code, indicator_code, frequency)
                
                if data is None:
                    raise ValueError("No data found for the specified parameters.")
                
                else:
                    
                    if not isinstance(data, pd.DataFrame):
                        df = pd.DataFrame(data)
                    else:
                        df = data
                    print(df.head()) 
                    print(df.columns.tolist())

                    title = indicator_name

                    if graph_type == 'line':
                        fig = px.line(
                            df, x='date', y='value',
                            title=title, 
                            labels={'date': 'Date', 'value': indicator_name}
                        )
                    elif graph_type == 'bar':
                        fig = px.bar(
                            df, x='date', y='value',
                            title=title,
                            labels={'value': indicator_name, 'date': 'Year'}
                        )
                    elif graph_type == 'pie':
                        fig = px.pie(
                            df, values='value', names='date',
                            title=title
                        )

                    fig.update_layout(
                        template = 'plotly_white',
                        xaxis_tickformat = '%Y',
                        yaxis_tickformat = '.2f',
                        hovermode = 'x unified'
                    )

                    graph = fig.to_html(
                        full_html=False,
                        include_plotlyjs='cdn', 
                        config={
                            'displaylogo': False,
                            'modeBarButtonsToAdd': [
                                'downloadImage'                       
                            ],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': f"{indicator_name}_{country_code}",
                                'scale': 2
                            }
                        })


            except ValueError as e:
                # If any error occurs during data retrieval or processing, capture the error message
                error_message = str(e)
    else:
        # For GET requests, create a new empty form
        form = DataCommonsDataForm()
    
    # Render the template with the form and any error message
    # For GET requests or failed POST requests
    return render(request, 'datacommons_data.html', {'form': form, 'error_message': error_message, 'graph': graph})

def markets_data(request):

    graph = None
    error_message = None
    info_box = None

    if request.method == 'POST':
        form = FinanceDataForm(request.POST)

        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            data = FinanceModel.get_market_data(ticker, start_date, end_date)
            if data is not None:
                df = pd.DataFrame(data)
            
            if isinstance(data.columns, pd.MultiIndex):

                close_prices = data['Close'][ticker]
                title = ticker

                fig = px.line(
                    df, x=close_prices.index, y=close_prices.values,
                    title=title,
                    labels={'x': 'Date', 'y': 'Close Price'}
                )
                fig.update_layout(
                    template='plotly_white',
                    xaxis_tickformat='%Y-%m-%d',
                    yaxis_tickformat='.2f',
                    hovermode='x unified'
                )
                graph = fig.to_html(
                    full_html=False,
                    include_plotlyjs='cdn', 
                    config={
                        'displaylogo': False,
                        'modeBarButtonsToAdd': [
                            'downloadImage'                       
                        ]
                    })
                
            basic_info = FinanceModel.get_basic_info(ticker)

            if basic_info is not None:
                info_box = {
                    'Name': basic_info.get('longName', 'N/A'),
                    'Sector': basic_info.get('sector', 'N/A'),
                    'Industry': basic_info.get('industry', 'N/A'),
                    'Market_Cap': basic_info.get('marketCap', 'N/A'),
                    'Beta': basic_info.get('beta', 'N/A'),
                    '52_Week_High': basic_info.get('fiftyTwoWeekHigh', 'N/A'),
                    '52_Week_Low': basic_info.get('fiftyTwoWeekLow', 'N/A'),
                    'Current_Price': basic_info.get('currentPrice', 'N/A'),
                    'PE_Ratio': basic_info.get('forwardPE', 'N/A'),
                    'Dividend_Yield': basic_info.get('dividendYield', 'N/A')
                }
                print(info_box)

    else:
        form = FinanceDataForm()

    return render(request, 'markets_search.html', {
        'form': form, 
        'error_message': error_message, 
        'graph': graph, 
        'info_box': info_box
    })
                
