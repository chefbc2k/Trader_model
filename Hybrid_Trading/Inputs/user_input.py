import logging
import json
from datetime import datetime

from Hybrid_Trading.Inputs.Input_Config import load_configurations
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

# Setup logging for this module
logging_master = LoggingMaster("main")
logger = logging_master.get_logger()

class UserInput:
    def __init__(self):
        self.configurations = load_configurations()
        self.args = self.select_preset()
        self.mode = self.args['mode']
        self.assign_mode_specific_configurations()
        self.validate_user_input()

    def select_preset(self):
        try:
            print("Select a mode:")
            modes = list(self.configurations.keys())
            for idx, mode in enumerate(modes, 1):
                print(f"{idx}. {mode}")

            choice = input("Enter the number corresponding to your choice: ")
            mode = modes[int(choice) - 1]
            print(f"Selected mode: {mode}")
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid choice. Defaulting to 'full_run'. Error: {e}")
            mode = "full_run"

        args = self.get_options(mode)
        args['mode'] = mode
        return args

    def prompt_for_date(self, date_type):
        while True:
            date_str = input(f"Enter the {date_type} (YYYY-MM-DD): ")
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                logger.warning(f"Invalid {date_type}. Please enter a valid date in YYYY-MM-DD format.")

    def get_options(self, mode):
        config = self.configurations[mode]
        options = {}

        # Prompt for start date and end date first
        start_date = self.prompt_for_date("start date")
        end_date = self.prompt_for_date("end date")
        options['start_date'] = start_date
        options['end_date'] = end_date

        # Calculate the duration in days
        duration_days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        options['duration_days'] = duration_days

        # Prompt for period and interval
        options['period'] = self.select_option('period', config['period_options'])
        options['interval'] = self.select_option('interval', config['interval_options'])

        # Prompt for percentage of tickers to process
        percentage = self.select_option('percentage', config['percentage_options'])
        options['percentage'] = int(percentage)

        # Calculate the number of tickers based on percentage and the total number of tickers from another module
        total_tickers = 100  # Placeholder, replace with the actual number of tickers
        tickers_to_process = int(total_tickers * (options['percentage'] / 100))
        options['tickers'] = ["Ticker1", "Ticker2"][:tickers_to_process]  # Replace with actual tickers

        # Prompt for other options
        for option_name, option_values in config.items():
            if option_name not in ['interval_options', 'period_options', 'duration_days', 'percentage_options'] and "options" in option_name:
                options[option_name.replace("_options", "")] = self.select_option(option_name, option_values)

        return options

    def select_option(self, option_name, options):
        print(f"\nSelect {option_name.replace('_options', '').replace('_', ' ')}:")
        for idx, option in enumerate(options, 1):
            print(f"{idx}. {option}")

        choice = input(f"Enter the number corresponding to your choice for {option_name.replace('_options', '').replace('_', ' ')}: ")
        try:
            selected_option = options[int(choice) - 1]
            logger.debug(f"User selected {selected_option} for {option_name}")
            return selected_option
        except (IndexError, ValueError) as e:
            logger.warning(f"Invalid choice for {option_name}. Defaulting to the first option: {options[0]}. Error: {e}")
            return options[0]

    def assign_mode_specific_configurations(self):
        config = self.configurations[self.mode]

        self.tickers = self.args.get('tickers')
        self.interval = self.args.get('interval')
        self.duration = self.args.get('duration_days')
        self.start_date = self.args.get('start_date')
        self.end_date = self.args.get('end_date')
        self.period = self.args.get('period')
        self.percentage = self.args.get('percentage')

        if self.mode in ["backtester", "day_trader", "full_run"]:
            self.handle_missing_values = self.args.get('handle_missing_values')
            self.fillna_method = self.args.get('fillna_method')
            self.sentiment_type = self.args.get('sentiment_type')

        elif self.mode == "sentiment_analysis":
            self.sentiment_type = self.args.get('sentiment_type')
            self.frequency = self.args.get('frequency')
            self.sentiment_score_threshold = self.args.get('sentiment_score_threshold')
            self.market_cap_filter = self.args.get('market_cap_filter')
            self.sector = self.args.get('sector')
            self.region = self.args.get('region')
            self.time_of_day = self.args.get('time_of_day')
            self.analyst_consensus = self.args.get('analyst_consensus')
            self.sentiment_momentum = self.args.get('sentiment_momentum')

    def validate_user_input(self):
        # Basic validation
        if not isinstance(self.mode, str) or self.mode not in self.configurations:
            raise ValueError("Invalid mode selected.")
        if not isinstance(self.tickers, list) or not all(isinstance(ticker, str) for ticker in self.tickers):
            raise ValueError("Tickers must be a list of strings.")
        if not isinstance(self.interval, str):
            raise ValueError("Interval must be a string.")
        if not isinstance(self.duration, int):
            raise ValueError("Duration must be an integer representing the number of days.")
        if not isinstance(self.start_date, str):
            raise ValueError("Start date must be a string.")
        if not isinstance(self.end_date, str):
            raise ValueError("End date must be a string.")
        if not isinstance(self.period, str):
            raise ValueError("Period must be a string.")

        if self.mode in ["backtester", "day_trader", "full_run"]:
            if self.handle_missing_values not in ["drop", "fill", "interpolate"]:
                raise ValueError("Handle missing values option is invalid.")
            if self.fillna_method not in ["mean", "median", "zero"]:
                raise ValueError("Fill NA method is invalid.")
            if self.sentiment_type not in ["bullish", "bearish", "neutral"]:
                raise ValueError("Sentiment type must be 'bullish', 'bearish', or 'neutral'.")

        elif self.mode == "sentiment_analysis":
            if self.sentiment_type not in ["bullish", "bearish", "neutral"]:
                raise ValueError("Sentiment type must be 'bullish', 'bearish', or 'neutral'.")
            if self.frequency not in ["daily", "weekly", "monthly"]:
                raise ValueError("Frequency must be 'daily', 'weekly', or 'monthly'.")
            if not isinstance(self.sentiment_score_threshold, float) or not (0 <= self.sentiment_score_threshold <= 1):
                raise ValueError("Sentiment score threshold must be a float between 0 and 1.")
            if self.market_cap_filter not in ["small", "medium", "large", "all"]:
                raise ValueError("Market cap filter must be 'small', 'medium', 'large', or 'all'.")
            if self.sector not in [
                "technology", "healthcare", "finance", "energy", "utilities", "materials",
                "consumer_discretionary", "consumer_staples", "industrials", "real_estate", "communication_services"
            ]:
                raise ValueError("Invalid sector option.")
            if self.region not in ["USA", "Europe", "Asia", "Global"]:
                raise ValueError("Region must be 'USA', 'Europe', 'Asia', or 'Global'.")
            if self.time_of_day not in ["morning", "afternoon", "evening"]:
                raise ValueError("Time of day must be 'morning', 'afternoon', or 'evening'.")
            if self.analyst_consensus not in ["buy", "hold", "sell"]:
                raise ValueError("Analyst consensus must be 'buy', 'hold', or 'sell'.")
            if self.sentiment_momentum not in ["increasing", "decreasing", "steady"]:
                raise ValueError("Sentiment momentum must be 'increasing', 'decreasing', or 'steady'.")

    def save_configurations(self, file_path='config.json'):
        # Save current configurations to a JSON file
        try:
            with open(file_path, 'w') as config_file:
                json.dump(self.args, config_file, indent=4)
            logger.info(f"Configurations saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving configurations: {e}")

    def load_configurations(self, file_path='config.json'):
        # Load configurations from a JSON file
        try:
            with open(file_path, 'r') as config_file:
                self.args = json.load(config_file)
            self.assign_mode_specific_configurations()
            self.validate_user_input()
            logger.info(f"Configurations loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    user_input = UserInput()
    user_input.validate_user_input()

    user_details = {
        "Mode": user_input.mode,
        "Tickers": user_input.tickers,
        "Interval": user_input.interval,
        "Duration": user_input.duration,
        "Start Date": user_input.start_date,
        "End Date": user_input.end_date,
        "Period": user_input.period,
        "Percentage": user_input.percentage
    }

    if user_input.mode in ["backtester", "day_trader", "full_run"]:
        user_details.update({
            "Handle Missing Values": user_input.handle_missing_values,
            "Fill NA Method": user_input.fillna_method,
            "Sentiment Type": user_input.sentiment_type
        })

    elif user_input.mode == "sentiment_analysis":
        user_details.update({
            "Sentiment Type": user_input.sentiment_type,
            "Frequency": user_input.frequency,
            "Sentiment Score Threshold": user_input.sentiment_score_threshold,
            "Market Cap Filter": user_input.market_cap_filter,
            "Sector": user_input.sector,
            "Region": user_input.region,
            "Time of Day": user_input.time_of_day,
            "Analyst Consensus": user_input.analyst_consensus,
            "Sentiment Momentum": user_input.sentiment_momentum
        })

    # Log the user details
    for key, value in user_details.items():
        logger.info(f"{key}: {value}")

    # Save the configurations (optional)
    user_input.save_configurations()

    # You can also load configurations like this (optional)
    user_input.load_configurations()

    # Return the structured user details (if needed for further processing)
    def get_user_details():
        return user_details

    # Example of calling get_user_details
    details = get_user_details()
    logger.debug(f"User details: {details}")