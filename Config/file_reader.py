import os
import pandas as pd
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FileReader:
    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch
        self.observer = Observer()
        self.event_handler = ExcelHandler(self)
        self.failed_files = []  # List to keep track of failed files

    def start(self):
        self.observer.schedule(self.event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        logging.info(f"Monitoring directory: {self.directory_to_watch}")
        try:
            while True:
                time.sleep(1)  # Keep the script running
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def process_file(self, filepath):
        try:
            # Load the Excel file
            xls = pd.ExcelFile(filepath, engine='openpyxl')
            all_data = []

            # Process each sheet based on its name
            for sheet_name in xls.sheet_names:
                logging.info(f"Processing sheet: {sheet_name}")
                df = pd.read_excel(xls, sheet_name=sheet_name)

                # Check the sheet and process its data
                if sheet_name == 'Stock Insights':
                    insights_data = self.process_stock_insights(df)
                    if self.validate_data(insights_data, ['Ticker', 'Current Price', 'Date']):
                        all_data.append(insights_data)
                elif sheet_name == 'Technical Indicators':
                    indicators_data = self.process_technical_indicators(df)
                    if self.validate_data(indicators_data, ['SMA', 'EMA', 'Date']):
                        all_data.append(indicators_data)
                elif sheet_name == 'Trading Signals':
                    signals_data = self.process_trading_signals(df)
                    if self.validate_data(signals_data, ['Signals', 'Date']):
                        all_data.append(signals_data)
                elif sheet_name == 'Summary':
                    summary_data = self.process_summary(df)
                    # Assuming validation is not needed for summary as it's just logged
                    all_data.append(summary_data)
                elif sheet_name == 'Trades':
                    trades_data = self.process_trades(df)
                    if self.validate_data(trades_data, ['Trade ID', 'Executed', 'Ticker', 'Volume', 'Price', 'Date']):
                        all_data.append(trades_data)

            # Combine all validated data into a single DataFrame
            if all_data:
                combined_data = pd.concat(all_data, ignore_index=True)
                logging.info("Combined Data Ready for Model Training:")
                logging.info(combined_data.head())

                # Save the processed data
                self.save_processed_data(combined_data, filepath)
            else:
                logging.warning(f"No valid data found in {filepath}")

        except Exception as e:
            logging.error(f"Error processing {filepath}: {e}")
            self.failed_files.append(filepath)  # Record the failed file

    def process_stock_insights(self, df):
        # Extract and validate Stock Insights data
        extracted_data = []
        for index, row in df.iterrows():
            try:
                data = json.loads(row['data'])
                ticker_symbol = data.get('Ticker Symbol', 'Unknown')
                current_price = data.get('Current Price', {}).get('price', None)
                date = data.get('Date', None)
                if current_price is not None:
                    extracted_data.append({'Ticker': ticker_symbol, 'Current Price': current_price, 'Date': date})
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Error parsing row {index}: {e}")
        return pd.DataFrame(extracted_data)

    def process_technical_indicators(self, df):
        # Extract and validate Technical Indicators data
        extracted_data = []
        for index, row in df.iterrows():
            try:
                data = json.loads(row['data'])
                sma = data.get('sma', None)
                ema = data.get('ema', None)
                date = data.get('date', None)
                if sma is not None and ema is not None:
                    extracted_data.append({'SMA': sma, 'EMA': ema, 'Date': date})
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Error parsing row {index}: {e}")
        return pd.DataFrame(extracted_data)

    def process_trading_signals(self, df):
        # Extract and validate Trading Signals data
        extracted_data = []
        for index, row in df.iterrows():
            try:
                data = json.loads(row['data'])
                signals = data.get('signals', [])
                date = data.get('date', None)
                extracted_data.append({'Signals': signals, 'Date': date})
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Error parsing row {index}: {e}")
        return pd.DataFrame(extracted_data)

    def process_summary(self, df):
        # Process and log Summary data
        logging.info("Summary Data:")
        logging.info(df)
        return df

    def process_trades(self, df):
        # Extract trade information
        extracted_data = []
        for index, row in df.iterrows():
            try:
                trade_data = json.loads(row['data'])
                executed = trade_data.get('executed', False)
                trade_info = {
                    'Trade ID': trade_data.get('id', None),
                    'Executed': executed,
                    'Ticker': trade_data.get('ticker', 'Unknown'),
                    'Volume': trade_data.get('volume', 0),
                    'Price': trade_data.get('price', 0),
                    'Date': trade_data.get('date', None),
                    'Reason': trade_data.get('reason', '') if not executed else 'Executed'
                }
                extracted_data.append(trade_info)
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Error parsing row {index}: {e}")
        return pd.DataFrame(extracted_data)

    def validate_data(self, df, required_columns):
        """
        Validate that the DataFrame contains all required columns and no missing data in these columns.
        """
        if not all(column in df.columns for column in required_columns):
            logging.warning(f"Missing required columns. Expected: {required_columns}, Found: {df.columns}")
            return False

        if df[required_columns].isnull().any().any():
            logging.warning("Missing data detected in required columns.")
            return False

        return True

    def save_processed_data(self, data, original_filepath):
        # Save data to JSON
        json_filename = os.path.splitext(original_filepath)[0] + '_processed.json'
        data.to_json(json_filename, orient='records', date_format='iso')
        logging.info(f"Processed data saved as JSON: {json_filename}")

        # Save data to Excel with a more structured format
        excel_filename = os.path.splitext(original_filepath)[0] + '_processed.xlsx'
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name='Processed Data', index=False)
        logging.info(f"Processed data saved as Excel: {excel_filename}")

    def log_failed_files(self):
        if self.failed_files:
            logging.info("The following files could not be processed and should be checked:")
            for file in self.failed_files:
                logging.info(file)

class ExcelHandler(FileSystemEventHandler):
    def __init__(self, file_reader):
        self.file_reader = file_reader

    def on_created(self, event):
        # Check if the new file is an Excel file
        if not event.is_directory and (event.src_path.endswith('.xlsx') or event.src_path.endswith('.xls')):
            logging.info(f"New file detected: {event.src_path}")
            self.file_reader.process_file(event.src_path)

if __name__ == "__main__":
    usb_drive_path = '/Volumes/TradingData/BackTester'
    file_reader = FileReader(usb_drive_path)
    file_reader.start()
    file_reader.log_failed_files()