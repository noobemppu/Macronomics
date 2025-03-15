from django.shortcuts import render
from .models import IMFData, IMFDataForm
import plotly.express as px


def main_page(request):
    return render(request, 'main_page.html')

def imf_data(request):
    error_message = None
    graph = None
    if request.method == 'POST':
        form = IMFDataForm(request.POST)
        if form.is_valid():
            country_code = form.cleaned_data['country_code']
            country_name = form.country_name  # Use the stored country name
            indicator_name = f"{form.indicator_name} - {country_name}"
            indicator_code = form.cleaned_data['indicator_code']
            frequency = form.cleaned_data['frequency']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            try:
                df = IMFData.get_observation(country_code, indicator_code, frequency, start_date, end_date)
                df['value'] = df['value'].astype(float).round(2)
                fig = px.line(df, x='date', y='value', title=indicator_name)
                fig.update_yaxes(tickformat='.2f', exponentformat='none')
                fig.update_traces(hovertemplate='%{y:.2f}')
                graph = fig.to_html(full_html=False, config={'displayModeBar': False})
                context = {
                    'form': form,
                    'graph': graph,
                }
                return render(request, 'imf_data.html', context)
            except ValueError as e:
                error_message = str(e)
    else:
        form = IMFDataForm()
    return render(request, 'imf_data.html', {'form': form, 'error_message': error_message, 'graph': graph})

def world_bank_data(request):
    # Add logic to query World Bank data using models
    context = {
        'data': 'World Bank Data Overview',
        # Add more context data as needed
    }
    return render(request, 'world_bank_data.html', context)
