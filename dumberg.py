# File: dumberg.py
# Description: Panel-based user interface for exploring stock data using DumbergAPI.

import panel as pn
import plotly.graph_objects as go
from dumbergapi import DumbergAPI
import yfinance as yf

# Initialize Panel extension with Plotly support
pn.extension('plotly')

# Initialize DumbergAPI instance to manage stock data
api = DumbergAPI()

# Create widgets for user interaction
company_selector = pn.widgets.CheckBoxGroup(
    name='Select Companies', 
    options=list(api.company_dict.keys())
)

ticker_input = pn.widgets.TextInput(
    name='Add a Ticker', 
    placeholder='Enter ticker symbol (e.g., AAPL)'
)

add_ticker_button = pn.widgets.Button(
    name='Add Ticker', 
    button_type='primary'
)

def add_ticker(event):
    '''
    Adds a new ticker to the list of tracked companies if valid.
    Parameters:
        event: The event that triggers the function (button click)
    Returns:
        None
    '''
    new_ticker = ticker_input.value.upper()
    if new_ticker and new_ticker not in api.company_dict.values():
        stock = yf.Ticker(new_ticker)  # Fetch stock data from Yahoo Finance
        info = stock.info
        if 'longName' in info:
            company_name = info['longName']
            # Add the ticker to the company dictionary
            api.company_dict[company_name] = new_ticker 
            #update the checklist 
            company_selector.options = list(api.company_dict.keys())  
            #clear the input
            ticker_input.value = ''  
        else:
            pn.state.notifications.error("Invalid Ticker: Unable to find company information.")

# Attach the add ticker function to button click
ticker_input.param.watch(add_ticker, 'value')

def get_theme():
    '''
    Determines the current theme of the application (light or dark).
    Parameters:
        None
    Returns:
        str: 'dark' if dark mode is active, otherwise 'default'.
    '''
    args = pn.state.session_args
    if "theme" in args and args["theme"][0] == b"dark":
        return "dark"
    return "default"

#callback function to update the stock table
@pn.depends(company_selector)
def update_stock_table(selected):
    if selected:
         # Create DataFrame of selected stock data
        stock_df = api.create_stock_dataframe(*selected) 
        return pn.pane.Plotly(api.create_stock_table(stock_df))
    return pn.pane.Markdown("### Please select at least one company.")

# callback function to update the donut chart
@pn.depends(company_selector)
def update_donut_chart(selected):
    if selected:
         # Plot market cap distribution
        return pn.pane.Plotly(api.plot_donut_chart(selected)) 
    return pn.pane.Markdown("### Please select at least one company to view market cap distribution.")

# callback function to Update performance tabs
@pn.depends(company_selector)
def update_performance_tabs(selected):
    if selected:
        tabs = pn.Tabs()
        for ticker in selected:
            # Map company to its ticker
            full_ticker = api.company_dict[ticker] 
            # Plot the company performance
            performance_chart = api.plot_performance_chart(full_ticker) 
            # Create the waterfall chart for company
            waterfall_chart = api.plot_waterfall_chart(full_ticker) 
            tabs.append((ticker, pn.Row(performance_chart, waterfall_chart)))
        return tabs
    return pn.pane.Markdown("### Select a stock to view performance.")

# using the FastListTemplate dashboard structure, make the dashboard
template = pn.template.FastListTemplate(
    title='Dumberg: Bloomberg for Dummies',
    sidebar=[
        pn.pane.Markdown("# Add Custom Ticker"),
        ticker_input,
        add_ticker_button,
        pn.pane.Markdown("# Select Stocks"),
        company_selector, 
        # Include the stock table in the sidebar
        pn.Row(update_stock_table)  
    ],
    main=[
         # Include candlestick and donut charts
        pn.Row(pn.pane.Plotly(api.plot_candlestick()), update_donut_chart), 
        update_performance_tabs 
    ],
    accent_base_color="#fb8b1e",
    header_background="#fb8b1e",
    background_color='#ffffff' if get_theme() == 'default' else '#181818',
    theme_toggle=True
)

# Serve the template application
template.servable()

if __name__ == '__main__':
    pn.serve(template)