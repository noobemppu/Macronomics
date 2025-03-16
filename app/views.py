# Standard library imports
import csv
import datetime
import io
import json
import os

# Third-party imports
import pandas as pd
import pandasdmx as sdmx
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# Django imports
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

# Local application imports
from .models import IMFData, IMFDataForm
from .cache_config import cache_manager  # This might be needed for your debug_imf_api view

def main_page(request):
    """
    Render the main landing page of the application.
    """
    # Simply render the main page template
    return render(request, 'main_page.html')


def imf_data(request):
    """
    View for displaying IMF data query form and results.
    Handles both GET requests (show empty form) and POST requests (process form and show results).
    """
    # Initialize variables that will be passed to the template
    error_message = None  # Stores error messages if any
    graph = None          # Stores the generated graph HTML if successful
    
    # Handle form submission (POST request)
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = IMFDataForm(request.POST)
        
        # Validate the form data
        if form.is_valid():
            # Extract all the form fields
            country_code = form.cleaned_data['country_code']         # Country code (e.g., 'US')
            country_name = form.country_name                         # Country name (e.g., 'United States')
            indicator_name = f"{form.indicator_name} - {country_name}"  # Full indicator name with country
            indicator_code = form.cleaned_data['indicator_code']     # Indicator code (e.g., 'NGDP_R_NSA')
            frequency = form.cleaned_data['frequency']               # Data frequency ('A' or 'M')
            start_date = form.cleaned_data['start_date']             # Start date for data range
            end_date = form.cleaned_data['end_date']                 # End date for data range
            refresh_data = form.cleaned_data.get('refresh_data', False)  # Whether to bypass cache
            
            try:
                # Get data from IMF API with cache settings applied
                df = IMFData.get_observation(
                    country_code,             # Country to query 
                    indicator_code,           # Indicator to query
                    frequency,                # Frequency of data
                    start_date,               # Start date filter
                    end_date,                 # End date filter
                    bypass_cache=refresh_data # Whether to bypass cache
                )
                
                # Convert values to float and round to 2 decimal places for display
                df['value'] = df['value'].astype(float).round(2)
                
                # Create a line chart using Plotly Express
                fig = px.line(
                    df,                           # DataFrame containing the data
                    x='date',                     # Column to use for x-axis
                    y='value',                    # Column to use for y-axis
                    title=indicator_name          # Chart title
                )
                
                # Configure y-axis format (use .2f format and don't use scientific notation)
                fig.update_yaxes(tickformat='.2f', exponentformat='none')
                
                # Configure the hover template for data points
                fig.update_traces(hovertemplate='%{y:.2f}')
                
                # Convert the Plotly figure to HTML for embedding in the template
                # full_html=False makes it embed-ready, displayModeBar=False hides the Plotly toolbar
                graph = fig.to_html(full_html=False, config={'displayModeBar': False})
                
                # Prepare context data for the template
                context = {
                    'form': form,    # Include the form (will show selected values)
                    'graph': graph,  # Include the generated graph
                }
                
                # Render the template with the form and graph
                return render(request, 'imf_data.html', context)
                
            except ValueError as e:
                # If any error occurs during data retrieval or processing, capture the error message
                error_message = str(e)
    else:
        # For GET requests, create a new empty form
        form = IMFDataForm()
    
    # Render the template with the form and any error message
    # For GET requests or failed POST requests
    return render(request, 'imf_data.html', {'form': form, 'error_message': error_message, 'graph': graph})


def export_imf_data_csv(request):
    """ 
    Export IMF data to CSV format.
    Processes form data and returns a CSV file for download.
    """
    # Only process POST requests
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = IMFDataForm(request.POST)
        
        # Validate the form data
        if form.is_valid():
            # Extract all the form fields
            country_code = form.cleaned_data['country_code']         # Country code
            country_name = form.country_name                         # Country name
            indicator_name = form.indicator_name                     # Indicator name
            indicator_code = form.cleaned_data['indicator_code']     # Indicator code
            frequency = form.cleaned_data['frequency']               # Data frequency
            start_date = form.cleaned_data['start_date']             # Start date
            end_date = form.cleaned_data['end_date']                 # End date
            refresh_data = form.cleaned_data.get('refresh_data', False)  # Whether to bypass cache
            
            try:
                # Get data from IMF API with cache settings applied
                df = IMFData.get_observation(
                    country_code, 
                    indicator_code, 
                    frequency, 
                    start_date, 
                    end_date,
                    bypass_cache=refresh_data
                )
                
                # Create a HTTP response with CSV content type
                response = HttpResponse(content_type='text/csv')
                
                # Generate a filename for the download that includes metadata
                filename = f"IMF_{indicator_code}_{country_code}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                
                # Set the Content-Disposition header to make the browser download the file
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                # Create a CSV writer that will write to the response
                writer = csv.writer(response)
                
                # Write metadata rows at the top of the CSV
                writer.writerow(['# IMF Data Export'])  # Title row
                writer.writerow(['# Indicator:', indicator_name])  # Indicator info
                writer.writerow(['# Country:', country_name])  # Country info
                writer.writerow(['# Frequency:', 'Monthly' if frequency == 'M' else 'Annual'])  # Frequency info
                writer.writerow(['# Date Range:', f"{start_date} to {end_date}"])  # Date range
                writer.writerow(['# Export Date:', datetime.datetime.now().strftime('%Y-%m-%d')])  # Export date
                writer.writerow([])  # Empty row as separator
                
                # Write column headers for the data
                writer.writerow(['Date', 'Value'])
                
                # Write each data point as a row
                for _, row in df.iterrows():
                    writer.writerow([row['date'], row['value']])
                
                # Return the response with the CSV data
                return response
                
            except ValueError as e:
                # If any error occurs, return an error message
                error_message = str(e)
                return HttpResponse(f"Error: {error_message}", status=400)
    
    # If not a POST request, return an error
    return HttpResponse("Invalid request method", status=400)


def export_imf_data_excel(request):
    """
    Export IMF data to Excel format with formatting and charts.
    Processes form data and returns an XLSX file for download.
    """
    # Only process POST requests
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = IMFDataForm(request.POST)
        
        # Validate the form data
        if form.is_valid():
            # Extract all the form fields
            country_code = form.cleaned_data['country_code']
            country_name = form.country_name
            indicator_name = form.indicator_name
            indicator_code = form.cleaned_data['indicator_code']
            frequency = form.cleaned_data['frequency']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            refresh_data = form.cleaned_data.get('refresh_data', False)
            
            try:
                # Get data from IMF API with cache settings applied
                df = IMFData.get_observation(
                    country_code, 
                    indicator_code, 
                    frequency, 
                    start_date, 
                    end_date,
                    bypass_cache=refresh_data
                )
                
                # Create an in-memory buffer to store the Excel file
                output = io.BytesIO()
                
                # Use pandas ExcelWriter with xlsxwriter engine to create Excel file
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Write the data to a sheet named 'Data'
                    df.to_excel(writer, sheet_name='Data', index=False)
                    
                    # Get references to the xlsxwriter workbook and worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Data']
                    
                    # Add a title format for better appearance
                    title_format = workbook.add_format({
                        'bold': True,           # Bold text
                        'font_size': 14         # Font size 14
                    })
                    
                    # Create a metadata sheet with information about the data
                    metadata_df = pd.DataFrame({
                        'Property': ['Indicator', 'Country', 'Frequency', 'Start Date', 'End Date', 'Export Date'],
                        'Value': [
                            indicator_name, 
                            country_name, 
                            'Monthly' if frequency == 'M' else 'Annual',
                            start_date,
                            end_date,
                            datetime.datetime.now().strftime('%Y-%m-%d')
                        ]
                    })
                    
                    # Write metadata to a separate sheet
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    # Create a line chart object
                    chart = workbook.add_chart({'type': 'line'})
                    
                    # Configure the chart series
                    chart.add_series({
                        'name': indicator_name,  # Legend label
                        'categories': ['Data', 1, 0, len(df), 0],  # x-axis data range (dates)
                        'values': ['Data', 1, 1, len(df), 1],      # y-axis data range (values)
                    })
                    
                    # Add chart title and axis labels
                    chart.set_title({'name': f"{indicator_name} - {country_name}"})
                    chart.set_x_axis({'name': 'Date'})  # X-axis label
                    chart.set_y_axis({'name': 'Value'})  # Y-axis label
                    
                    # Insert the chart into the worksheet
                    # Position at cell D2 with scaling factors
                    worksheet.insert_chart('D2', chart, {'x_scale': 1.5, 'y_scale': 1})
                
                # Set up the HTTP response for Excel download
                response = HttpResponse(
                    output.getvalue(),  # Get the content of the BytesIO buffer
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
                # Generate a filename for the download
                filename = f"IMF_{indicator_code}_{country_code}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
                
            except ValueError as e:
                # If any error occurs, return an error message
                error_message = str(e)
                return HttpResponse(f"Error: {error_message}", status=400)
    
    # If not a POST request, return an error
    return HttpResponse("Invalid request method", status=400)


def export_imf_data_image(request):
    """
    Export the graph as an image (PNG file) that can be downloaded by the user
    """
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = IMFDataForm(request.POST)
        
        # Check if the form data is valid
        if form.is_valid():
            # Extract values from the validated form
            country_code = form.cleaned_data['country_code']  # Get country code (e.g., 'US')
            country_name = form.country_name  # Get country name from form property
            # Combine indicator name with country name for the chart title
            indicator_name = f"{form.indicator_name} - {country_name}"
            indicator_code = form.cleaned_data['indicator_code']  # Get indicator code
            frequency = form.cleaned_data['frequency']  # Get data frequency (M=Monthly, A=Annual)
            start_date = form.cleaned_data['start_date']  # Get start date if provided
            end_date = form.cleaned_data['end_date']  # Get end date if provided
            # Check if user wants to bypass cache for fresh data
            refresh_data = form.cleaned_data.get('refresh_data', False)
            
            try:
                # Retrieve the observation data from IMF
                # Note: You need to add a comma after end_date for the next parameter
                df = IMFData.get_observation(
                    country_code, 
                    indicator_code, 
                    frequency, 
                    start_date, 
                    end_date,  # <-- Add a comma here
                    bypass_cache=refresh_data  # Pass the refresh option
                )
                
                # Convert values to float and round to 2 decimal places for consistent display
                df['value'] = df['value'].astype(float).round(2)
                
                # Create a line chart using Plotly Express
                fig = px.line(df, x='date', y='value', title=indicator_name)
                
                # Update the y-axis format to show numbers with 2 decimal places
                fig.update_yaxes(tickformat='.2f', exponentformat='none')
                
                # Set the hover tooltip to show values with 2 decimal places
                fig.update_traces(hovertemplate='%{y:.2f}')
                
                # Convert the figure to a PNG image in memory
                # width/height set the image dimensions, scale=2 increases DPI for better quality
                img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
                
                # Create an HTTP response with the image content type
                response = HttpResponse(img_bytes, content_type='image/png')
                
                # Generate a filename based on the data being exported
                filename = f"IMF_{indicator_code}_{country_code}_{datetime.datetime.now().strftime('%Y%m%d')}.png"
                
                # Set the response header to make the browser download the file
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
            
            except ValueError as e:
                # If an error occurs, return an HTTP response with the error message
                error_message = str(e)
                return HttpResponse(f"Error: {error_message}", status=400)
    
    # If the request method is not POST, return an error message
    return HttpResponse("Invalid request method", status=400)


def export_imf_data_pdf(request):
    """
    Export IMF data as a PDF report containing both the graph and data table
    """
    # Check if request is POST (form submission)
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = IMFDataForm(request.POST)
        
        # Check if form data is valid
        if form.is_valid():
            # Extract values from the validated form
            country_code = form.cleaned_data['country_code']  # Get country code (e.g., 'US')
            country_name = form.country_name  # Get country name from form property
            indicator_name = form.indicator_name  # Get indicator name
            indicator_code = form.cleaned_data['indicator_code']  # Get indicator code
            frequency = form.cleaned_data['frequency']  # Get frequency (M=Monthly, A=Annual)
            start_date = form.cleaned_data['start_date']  # Get start date if provided
            end_date = form.cleaned_data['end_date']  # Get end date if provided
            # Check if user wants to bypass cache for fresh data
            refresh_data = form.cleaned_data.get('refresh_data', False)
            
            try:
                # Retrieve the observation data from IMF
                # Note: You need to add a comma after end_date for the next parameter
                df = IMFData.get_observation(
                    country_code, 
                    indicator_code, 
                    frequency, 
                    start_date, 
                    end_date,  # <-- Add a comma here
                    bypass_cache=refresh_data  # Pass the refresh option
                )
                
                # Create a BytesIO buffer to build the PDF in memory
                buffer = io.BytesIO()
                
                # Create a PDF document using ReportLab's SimpleDocTemplate
                # letter is a standard page size (8.5x11 inches)
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                
                # Initialize a list to hold the content elements for the PDF
                story = []
                
                # Get the default styles for PDF documents
                styles = getSampleStyleSheet()
                
                # Create a title for the PDF with Heading1 style
                title = Paragraph(f"IMF Data: {indicator_name} - {country_name}", styles['Heading1'])
                story.append(title)  # Add title to the document
                
                # Add metadata information with spacing
                story.append(Spacer(1, 12))  # Add 12 points of vertical space
                
                # Add frequency information (Monthly/Annual)
                story.append(Paragraph(
                    f"<b>Frequency:</b> {'Monthly' if frequency == 'M' else 'Annual'}", 
                    styles['Normal']
                ))
                
                # Add date range information
                story.append(Paragraph(
                    f"<b>Date Range:</b> {start_date} to {end_date}", 
                    styles['Normal']
                ))
                
                # Add export date (current date)
                story.append(Paragraph(
                    f"<b>Export Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d')}", 
                    styles['Normal']
                ))
                
                # Add more vertical space before the graph
                story.append(Spacer(1, 20))
                
                # Create a graph using Plotly and convert it to an image
                fig = px.line(df, x='date', y='value', title=indicator_name)
                fig.update_yaxes(tickformat='.2f', exponentformat='none')  # Format y-axis values
                img_bytes = fig.to_image(format="png", width=600, height=400)  # Convert to PNG
                
                # Save the image to a temporary file
                # Note: On Windows, you might need a different path than /tmp/
                img_path = f"/tmp/temp_graph_{indicator_code}.png"
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)  # Write the image bytes to the temp file
                
                # Add space after the image
                story.append(Spacer(1, 20))
                
                # Create data for the table - start with column headers
                data = [['Date', 'Value']]
                
                # Add each row of data to the table
                for _, row in df.iterrows():  # Iterate through dataframe rows
                    data.append([row['date'], f"{row['value']:.2f}"])  # Format value with 2 decimals
                
                # Create a table with the data and set column widths
                t = Table(data, colWidths=[200, 100])
                
                # Style the table for better appearance
                t.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (1, 0), colors.grey),  # Gray background for header
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),  # White text for header
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),  # Center-align header text
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),  # Bold font for header
                    ('FONTSIZE', (0, 0), (1, 0), 10),  # Font size for header
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),  # Padding below header
                    
                    # Data rows styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # White background for data
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Black grid lines
                ]))
                
                # Add the table to the PDF content
                story.append(t)
                
                # Build the PDF document with all the content
                doc.build(story)
                
                # Get the completed PDF data from the buffer
                pdf_data = buffer.getvalue()
                buffer.close()  # Close the buffer
                
                # Clean up by removing the temporary image file
                os.remove(img_path)
                
                # Create an HTTP response with PDF content type
                response = HttpResponse(pdf_data, content_type='application/pdf')
                
                # Generate a filename based on the data being exported
                filename = f"IMF_{indicator_code}_{country_code}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                
                # Set the response header to make the browser download the file
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
            
            except ValueError as e:
                # If an error occurs, return an HTTP response with the error message
                error_message = str(e)
                return HttpResponse(f"Error: {error_message}", status=400)
    
    # If the request method is not POST, return an error message
    return HttpResponse("Invalid request method", status=400)

@staff_member_required
def debug_imf_api(request):
    """
    Admin view to debug IMF API connection issues
    """
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)
    
    results = {
        'status': 'Running tests...',
        'tests': {}
    }
    
    # Test standard PandaSDMX connection
    try:
        results['tests']['standard_connection'] = {
            'status': 'Testing...'
        }
        
        # Create a fresh IMF request
        imf = sdmx.Request('IMF')
        
        # Try to fetch a dataflow
        flows = imf.dataflow()
        
        # If successful, record the available dataflows
        flow_ids = [f.id for f in flows.dataflow]
        results['tests']['standard_connection'] = {
            'status': 'Success',
            'dataflows': flow_ids[:10],  # First 10 for brevity
            'total_dataflows': len(flow_ids)
        }
    except Exception as e:
        results['tests']['standard_connection'] = {
            'status': 'Failed',
            'error': str(e)
        }
    
    # Test alternative endpoints
    endpoints = [
        'https://sdmxcentral.imf.org/ws/public/sdmxapi/rest',
        'https://sdmxidata.imf.org/sdmx/v2',
        'https://sdmxidata-test.imf.org/ws/public/sdmxapi/rest'
    ]
    
    for endpoint in endpoints:
        try:
            results['tests'][f'endpoint_{endpoint}'] = {
                'status': 'Testing...'
            }
            
            # Try this endpoint
            custom_imf = sdmx.Request('IMF', base_url=endpoint)
            flows = custom_imf.dataflow()
            
            flow_ids = [f.id for f in flows.dataflow]
            results['tests'][f'endpoint_{endpoint}'] = {
                'status': 'Success',
                'dataflows': flow_ids[:10],
                'total_dataflows': len(flow_ids)
            }
        except Exception as e:
            results['tests'][f'endpoint_{endpoint}'] = {
                'status': 'Failed',
                'error': str(e)
            }
    
    # Test with direct requests to see what's happening at HTTP level
    import requests
    for endpoint in endpoints:
        try:
            results['tests'][f'raw_request_{endpoint}'] = {
                'status': 'Testing...'
            }
            
            # Make a direct HTTP request
            response = requests.get(f"{endpoint}/dataflow")
            
            results['tests'][f'raw_request_{endpoint}'] = {
                'status': 'Success' if response.ok else 'Failed',
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', 'unknown'),
                'content_length': len(response.content),
                'preview': response.text[:200] if response.ok else ''
            }
        except Exception as e:
            results['tests'][f'raw_request_{endpoint}'] = {
                'status': 'Failed',
                'error': str(e)
            }
    
    results['status'] = 'Complete'
    return JsonResponse(results)


def world_bank_data(request):
    """
    View for displaying World Bank data (placeholder for future implementation)
    """
    # This is a stub for future implementation of World Bank data functionality
    # Currently just returns a simple context with placeholder text
    
    # Create a context dictionary with placeholder data
    context = {
        'data': 'World Bank Data Overview',
        # Add more context data as needed when implementing this feature
    }
    
    # Render the world_bank_data.html template with the context
    return render(request, 'world_bank_data.html', context)