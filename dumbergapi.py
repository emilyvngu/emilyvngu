"""File: dumbergapi.py
Description: API for interacting with the stock data using Yahoo Finance and generating visualizations."""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

class DumbergAPI:
    def __init__(self):
        # Dictionary of companies and their tickers
        self.company_dict = {
            'Apple Inc.': 'AAPL',
            'Microsoft Corp.': 'MSFT',
            'Alphabet Inc. (Google)': 'GOOGL',
            'Amazon.com Inc.': 'AMZN',
            'NVIDIA Corporation': 'NVDA',
            'Tesla Inc.': 'TSLA',
            'Berkshire Hathaway Inc.': 'BRK-B',
            'Meta Platforms Inc. (Facebook)': 'META',
            'Taiwan Semiconductor Manufacturing Company': 'TSM',
            'Johnson & Johnson': 'JNJ'
        }

    def fetch_stock_data(self, ticker):
        '''
        Fetches the latest stock data for the given ticker.
        Parameters:
            ticker (str): The stock ticker symbol.
        Returns:
            tuple: Contains the closing price and opening price of the stock.
        '''
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[0], data['Open'].iloc[0]
        return None, None

    def create_stock_dataframe(self, *tickers):
        """
        Creates a DataFrame with stock data for the given tickers.
        Parameters:
            tickers (tuple): list of stock tickers.
        Returns:
            DataFrame: Pandas DataFrame containing the stock data.
        """
        if not tickers:
            tickers = self.company_dict.keys()
        rows = []
        for company in tickers:
            ticker = self.company_dict.get(company, company)
            current_price, opening_price = self.fetch_stock_data(ticker)
            if current_price is not None and opening_price is not None:
                price_change = current_price - opening_price
                rows.append({
                    'Company': company,
                    'Ticker': ticker,
                    'Current Price': current_price,
                    'Opening Price': opening_price,
                    'Price Change': price_change
                })
        return pd.DataFrame(rows)

    def create_stock_table(self, stock_df):
        '''
        Creates a Plotly table figure from the stock DataFrame.
        Parameters:
            stock_df (DataFrame): DataFrame containing stock data.

        Returns:
            Figure: Plotly Figure representing the stock table.
        '''
        rows = []
        colors = []  
        
        for _, row in stock_df.iterrows():
            status = 'Up' if row['Current Price'] > row['Opening Price'] else 'Down'
            color = '#4af6c3' if status == 'Up' else '#ff433d'  # Green for 'Up', Red for 'Down'
            
            rows.append({'Ticker': row['Ticker'], 'Price': f"${row['Current Price']:.2f}", 'Status': status})
            colors.append(color) 
        
        df = pd.DataFrame(rows)
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns), fill_color='black', font=dict(color='white', size=14)),  
            cells=dict(values=[df[col] for col in df.columns],
                       fill_color='black',  
                       font=dict(color=['white', 'white', colors], size=12))  
        )])
        
        fig.update_layout(template='plotly_dark', width=300)  
        return fig

    def plot_donut_chart(self, selected_companies):
        """ Plots a donut chart for market cap distribution of the selected companies.
            Parameters:
                selected_companies (list): List of selected company names.

            Returns:
                Figure: Plotly Figure representing the donut chart.
        """
        tickers = [self.company_dict[company] for company in selected_companies]
        market_caps = []
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            market_cap = stock.info.get('marketCap', 0) / 1e9  # Convert to billions
            market_caps.append(market_cap)

        fig = go.Figure(go.Pie(
            labels=tickers,
            values=market_caps,
            hole=.3,
            marker=dict(colors=['#ff433d', '#0068ff', '#4af6c3', '#fb8b1e'])
        ))
        fig.update_layout(title='Market Cap Distribution', template='plotly_dark', width=270, height=290)
        return fig

    def plot_performance_chart(self, ticker):
        '''
        Plots a performance chart for the given ticker.
        Parameters:
            ticker (str): The stock ticker symbol.
        Returns:
            Figure: Plotly Figure representing the performance chart of the stock.
        '''
        stock = yf.Ticker(ticker)
        data = stock.history(period='1y')  
        
        if not data.empty:
            data['Returns'] = data['Close'].pct_change().cumsum() * 100  # Calculate cumulative returns
            dates = data.index
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=data['Returns'], mode='lines', line=dict(color='#4af6c3')))
            fig.update_layout(
                title=f'{ticker} Performance (Cumulative Returns)',
                template='plotly_dark',
                width=470,
                height=290,
                xaxis_title='Date',
                yaxis_title='Cumulative Returns (%)'
            )
            return fig
        else:
            return go.Figure()

    def plot_waterfall_chart(self, ticker):
        '''
        Plots a waterfall chart for quarterly performance of the given ticker.
        Parameters:
            ticker (str): The stock ticker symbol.
        Returns:
            Figure: Plotly Figure representing the quarterly performance as a waterfall chart.
        '''
        stock = yf.Ticker(ticker)
        data = stock.history(period='1y')  # Get 1-year historical data for the stock
        
        if not data.empty:
            quarterly_data = data['Close'].resample('Q').last()
            quarterly_changes = quarterly_data.pct_change() * 100  
            
            fig = go.Figure(go.Waterfall(
                x=quarterly_changes.index.strftime('%Y-Q%q'),  
                y=quarterly_changes.dropna(),  
                increasing=dict(marker=dict(color="#4af6c3")),  
                decreasing=dict(marker=dict(color="#ff433d"))   
            ))
            fig.update_layout(
                title=f'{ticker} Quarterly Performance',
                template='plotly_dark',
                width=470,
                height=290,
                xaxis_title='Quarter',
                yaxis_title='Percentage Change (%)'
            )
            return fig
        else:
            return go.Figure()

    def plot_candlestick(self):
        '''
        Plots a candlestick chart for S&P 500 (2023-2024).
        Parameters:
            None
        Returns:
            Figure: Plotly Figure representing the candlestick chart for S&P 500.
        '''
        df = yf.download('^GSPC', start='2023-01-01', end='2024-12-31')
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#4af6c3', decreasing_line_color='#ff433d'
        )])
        fig.update_layout(
            template='plotly_dark',
            title='S&P 500 Stock Prices (2023-2024)',
            width=660,
            height=290,
            xaxis_title='Date',
            yaxis_title='Price'
        )
        return fig