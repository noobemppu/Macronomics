from datetime import datetime, timedelta, date

# Third-party imports
import pandas as pd
import datacommons as dc
import plotly.express as px
import plotly.graph_objects as go

# Django imports
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

# Local application imports
from .models import DataCommonsData, DataCommonsDataForm, get_indicators  
from .models_finance import FinanceModel, FinanceDataForm  
from .models_gd import GDIMF

def main_page(request):

    return render(request, 'main_page.html')


def datacommons_data(request):
    
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
                error_message = str(e)
    else:
        form = DataCommonsDataForm()
    
    return render(request, 'datacommons_data.html', {'form': form, 'error_message': error_message, 'graph': graph})

def markets_data(request):

    if request.method == 'POST':
        form = FinanceDataForm(request.POST)

        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            start_date = form.cleaned_data['start_date'] or (datetime.now().date() - timedelta(days=365))
            end_date = form.cleaned_data['end_date'] or datetime.now().date()

            request.session['ticker'] = ticker
            request.session['start_date'] = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date
            request.session['end_date'] = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date

            return redirect('markets_results')
    else:
        form = FinanceDataForm()
        return render(request, 'markets_search.html', {'form': form})


def markets_results(request):

    graph = None
    error_message = None
    info_box = None

    ticker = request.session.get('ticker')
    start_date_str = request.session.get('start_date')
    end_date_str = request.session.get('end_date')

    if ticker and start_date_str and end_date_str:
        data = FinanceModel.get_market_data(ticker, start_date_str, end_date_str)
        if data is not None:
            
            print(f"Data shape: {data.shape}, Columns: {data.columns}")
            print(f"Is MultiIndex: {isinstance(data.columns, pd.MultiIndex)}")
            print("Data columns:", data.columns)
            
            if isinstance(data.columns, pd.MultiIndex):

                close_prices = data['Close'][ticker]
                title = ticker

                if close_prices is not None:
                    fig = px.line(
                        x=close_prices.index, 
                        y=close_prices.values,
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
        

    form = FinanceDataForm()

    return render(request, 'markets_search.html', {
        'form': form, 
        'error_message': error_message, 
        'graph': graph, 
        'info_box': info_box,
        'ticker': ticker,
        'active_period': 'custom'
    })

def markets_period(request, ticker, period):
    graph = None
    error_message = None
    info_box = None
    active_period = None

    try: 
        end_date = datetime.now().date()
        
        #if period == '1d':
        #    start_date = end_date - timedelta(days=1)
        if period == '1m':
            start_date = end_date - timedelta(days=30)
        elif period == 'ytd':
            start_date = date(end_date.year, 1, 1)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == 'all':
            start_date = date(1900, 1, 1)
        else:
            start_date = end_date - timedelta(days=30)
            active_period = '1m'

        request.session['ticker'] = ticker
        request.session['start_date'] = start_date.strftime('%Y-%m-%d')
        request.session['end_date'] = end_date.strftime('%Y-%m-%d')

        data = FinanceModel.get_market_data(ticker, start_date, end_date)                

        if data is not None:

            if isinstance(data.columns, pd.MultiIndex):
                close_prices = data['Close'][ticker]
                title = f"{ticker} - {period.upper()} Price History"

                fig = px.line(
                    x=close_prices.index,
                    y=close_prices.values,
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
                        'modeBarButtonsToAdd': ['downloadImage']
                    }
                )
        else:
            error_message = f"No data found for {ticker} in the specified date range."
        
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
        
    except Exception as e:
        error_message = f"Error processing data: {str(e)}"
        import traceback
        traceback.print_exc()
    
    # Create a form for searching again
    form = FinanceDataForm()
    if ticker:
        form.initial['ticker'] = ticker

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'graph': graph,
            'period': period,
            'info_box': info_box,
            'error': error_message
        })
    
    return render(request, 'markets_search.html', {
        'form': form,
        'graph': graph,
        'info_box': info_box,
        'ticker': ticker,
        'error_message': error_message,
        'active_period': active_period
    })


def gd_popular_countries_data(request):
    """
    View for displaying popular countries data from the IMF.
    """
    table = GDIMF.popular_countries_data()
    if table is not None:
        
        table = table.sort_values(by='GDP (Billions USD)', ascending=False)

        table_html = table.to_html(
            classes='table table-striped table-hover',
            index=False,
            border=0, 
            justify='center', 
            escape=False
        )

        return render(request, 'general_data.html', {'table_html': table_html})
    else:
        return render(request, 'general_data.html', {'error': 'No data available.'})