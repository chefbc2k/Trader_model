import unittest
from unittest.mock import patch
import unittest
from unittest.mock import patch
           
from Hybrid_Trading.Inputs.user_input import UserInput
           
from Hybrid_Trading.Inputs.user_input import UserInput

class TestUserInput(unittest.TestCase):
    def setUp(self):
        self.user_input = UserInput()

    @patch('Hybrid_Trading.Inputs.user_input.UserInput.select_preset', return_value={'mode': 'test_mode'})
    @patch('Hybrid_Trading.Inputs.user_input.UserInput.get_options', return_value={'start_date': '2022-01-01', 'end_date': '2022-01-31'})
    def test_unexpected_error_during_validation(self, mock_select_preset, mock_get_options):
        # Mock the load_configurations method to return a valid configuration
        self.user_input.configurations = {'test_mode': {'period_options': ['1D', '5D'], 'interval_options': ['1H', '4H']}}

        # Mock the select_option method to return a valid option
        self.user_input.select_option = lambda option_name, options: options[0]

        # Mock the prompt_for_date method to return a valid date
        self.user_input.prompt_for_date = lambda date_type: '2022-01-01'

        # Mock the validate_user_input method to raise an unexpected error
        self.user_input.validate_user_input = lambda: 1 / 0

        # Call the run method to execute the test
        with self.assertRaises(ZeroDivisionError):
            self.user_input.run()

if __name__ == '__main__':
    unittest.main()
    
    
    class TestUserInputModeSpecificConfigurations(unittest.TestCase):
        def setUp(self):
            self.user_input = UserInput()
    
        @patch('Hybrid_Trading.Inputs.user_input.UserInput.select_preset', return_value={'mode': 'test_mode'})
        @patch('Hybrid_Trading.Inputs.user_input.UserInput.get_options', return_value={
            'start_date': '2022-01-01', 'end_date': '2022-01-31', 'period': '1D', 'interval': '1H', 'percentage': 50
        })
        def test_unexpected_error_during_mode_specific_configurations_assignment(self, mock_select_preset, mock_get_options):
            # Mock the load_configurations method to return a valid configuration
            self.user_input.configurations = {'test_mode': {
                'period_options': ['1D', '5D'], 'interval_options': ['1H', '4H'],
                'percentage_options': [25, 50, 75], 'handle_missing_values_options': ['drop', 'fill', 'interpolate'],
                'fillna_method_options': ['mean', 'median', 'zero'], 'sentiment_type_options': ['bullish', 'bearish', 'neutral']
            }}
    
            # Mock the select_option method to return a valid option
            self.user_input.select_option = lambda option_name, options: options[0]
    
            # Mock the prompt_for_date method to return a valid date
            self.user_input.prompt_for_date = lambda date_type: '2022-01-01'
    
            # Mock the assign_mode_specific_configurations method to raise an unexpected error
            self.user_input.assign_mode_specific_configurations = lambda: 1 / 0
    
            # Call the run method to execute the test
            with self.assertRaises(ZeroDivisionError):
                self.user_input.run()
           
       
    class TestUserInputModeSelection(unittest.TestCase):
               def setUp(self):
                   self.user_input = UserInput()
           
               @patch('Hybrid_Trading.Inputs.user_input.UserInput.select_preset', side_effect=ValueError("Invalid choice"))
               def test_unexpected_error_during_mode_selection(self):
                   # Mock the load_configurations method to return a valid configuration
                   self.user_input.configurations = {'test_mode': {'period_options': ['1D', '5D'], 'interval_options': ['1H', '4H']}}
           
                   # Call the run method to execute the test
                   with self.assertRaises(ValueError):
                       self.user_input.run()
           
    if __name__ == '__main__':
               unittest.main()     
                