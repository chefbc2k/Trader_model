import os
import logging
import asyncio
from typing import List
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from django.db import connection, models
from asgiref.sync import sync_to_async
from django.apps import apps  # Correct import

# Load environment variables from the .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CentralizedDataStorage:
    def __init__(self, user_input):
        self.user_input = user_input
        self.logger = logging.getLogger(__name__)

        # Set up database connection from environment variables
        self.db_config = {
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT')
        }

        if not all(self.db_config.values()):
            self.logger.error("Database environment variables are missing.")
            raise EnvironmentError("Missing one or more DB configuration environment variables.")

    async def store(self, ticker: str, table_type: str, data: dict) -> None:
        """
        Dynamically store data for a given ticker in the specified table.
        Data is validated, cleaned, and missing values are handled before storing using Django's ORM.
        """
        # Retrieve the model dynamically for the given table_type
        model_class = self._get_model_for_table_type(table_type)
        
        # Get the list of fields (columns) for the table
        columns = [f.name for f in model_class._meta.fields if f.name != 'id']

        # Handle missing values dynamically before storing data
        data = self._handle_missing_values(data, columns, table_type)

        # Dynamically create or update the model instance
        instance = await self._create_or_update_instance(ticker, model_class, data)

        # Save the instance asynchronously
        await sync_to_async(instance.save)()
        self.logger.info(f"Data stored successfully for {ticker} in {model_class.__name__}")

    def _get_model_for_table_type(self, table_type: str) -> models.Model:
        """Dynamically retrieve the model class for the given table type."""
        try:
            model_name = ''.join(word.capitalize() for word in table_type.split('_'))
            model = apps.get_model('data', model_name)  # Replace 'data' with your actual app label
            return model
        except LookupError:
            self.logger.error(f"Model not found for table type: {table_type}")
            raise ValueError(f"Model not found for table type: {table_type}")

    def _handle_missing_values(self, data: dict, columns: List[str], table_type: str) -> dict:
        """
        Handle missing values based on the user's preferences from user_input and column types.
        """
        handling_method = getattr(self.user_input, 'handling_missing_values', 'fill')
        fill_method = getattr(self.user_input, 'fill_na_method', 'mean')

        def get_default_value(col: str):
            """Provide a default value for missing values based on the column type."""
            if isinstance(data.get(col), (int, float)):
                if fill_method == 'zero':
                    return 0  # Default for numeric is zero
                elif fill_method == 'mean':
                    return self._calculate_mean(col, table_type)
                elif fill_method == 'median':
                    return self._calculate_median(col, table_type)
            if isinstance(data.get(col), str):
                return 'Unknown'  # Default for strings
            return datetime.now().isoformat()  # Default for date fields

        def interpolate_missing_values(data: dict, columns: List[str]) -> dict:
            """Interpolate missing numeric values using pandas."""
            numeric_data = {col: value for col, value in data.items() if isinstance(value, (int, float))}
            series = pd.Series(numeric_data)
            series = series.interpolate(method='linear', limit_direction='both', inplace=False)
            for col, value in series.items():
                data[col] = value
            return data

        # Apply the method selected by the user input
        if handling_method == 'fill':
            # Fill missing values based on the selected fill method (mean, median, or zero)
            for col in columns:
                if col not in data or pd.isnull(data[col]):
                    data[col] = get_default_value(col)

        elif handling_method == 'interpolate':
            # Interpolate missing numeric values
            data = interpolate_missing_values(data, columns)

        elif handling_method == 'drop':
            # Remove columns with missing values
            data = {col: value for col, value in data.items() if not pd.isnull(value)}

        return data

    def _calculate_mean(self, col: str, table_type: str) -> float:
        """Calculate the mean value for the given column from the database."""
        query = f"SELECT AVG({col}) FROM {table_type};"
        result = self._execute_sync_query(query)
        return result[0][0] if result and result[0] else 0

    def _calculate_median(self, col: str, table_type: str) -> float:
        """Calculate the median value for the given column from the database."""
        query = f"SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}) FROM {table_type};"
        result = self._execute_sync_query(query)
        return result[0][0] if result and result[0] else 0

    async def _create_or_update_instance(self, ticker: str, model_class: models.Model, data: dict):
        """
        Dynamically create or update a Django model instance.
        """
        try:
            # Get or create the instance for the given model class and ticker
            ticker_instance, created = await sync_to_async(model_class.objects.get_or_create)(
                ticker=ticker, defaults=data
            )

            # Update other fields in case the instance exists
            for field, value in data.items():
                setattr(ticker_instance, field, value)

            return ticker_instance

        except Exception as e:
            self.logger.error(f"Error creating or updating instance for {ticker} in {model_class.__name__}: {e}")
            raise e

    def _execute_sync_query(self, query: str):
        """Execute a raw SQL query synchronously and return the result."""
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()