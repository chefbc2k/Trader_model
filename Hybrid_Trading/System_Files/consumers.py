from asyncio.log import logger
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from datetime import datetime

# 1. Portfolio Consumer (Handles portfolio management via WebSocket)
class PortfolioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Clean up on disconnect
        pass

    async def receive(self, text_data):
        # Parse incoming trade data
        form_data = json.loads(text_data)
        ticker = form_data.get('ticker')
        quantity = form_data.get('quantity')
        price = form_data.get('price')
        action = form_data.get('action')

        # Simulate trade execution logic
        await self.send(text_data=json.dumps({
            'status': 'success',
            'message': f'{action.capitalize()} {quantity} shares of {ticker} at ${price}.'
        }))

# 2. Backtest Progress Consumer (Real-time progress updates during backtesting)
class BacktestProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['session'].session_key
        self.group_name = f'backtest_{self.session_id}'
        
        # Join group for backtest updates
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group on disconnect
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive backtest updates from the group
    async def send_backtest_results(self, event):
        message = event['message']
        await self.send(text_data=message)

# 3. User Input Consumer (Processes form data sent through WebSocket)
class UserInputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("UserInputConsumer: Attempting to connect")
        try:
            await self.accept()
            logger.info("UserInputConsumer: Connection accepted")
        except Exception as e:
            logger.error(f"UserInputConsumer: Connection failed with error: {e}")

    async def disconnect(self, close_code):
        logger.info(f"UserInputConsumer: Disconnected with code {close_code}")

    async def receive(self, text_data):
        logger.info(f"UserInputConsumer: Received data: {text_data}")
        try:
            # Import models inside the method to ensure Django is ready
            from Hybrid_Trading.Trading.models import TradeResults, PerformanceMetrics, Signals

            # Process the received data
            form_data = json.loads(text_data)
            for progress in range(0, 101, 10):
                await self.send(text_data=json.dumps({
                    'progress': progress,
                    'message': f'Processing form data: {progress}% completed'
                }))
                await asyncio.sleep(1)

            await self.send(text_data=json.dumps({
                'status': 'completed',
                'message': 'User input processed successfully.'
            }))
            logger.info("UserInputConsumer: Processing completed successfully")
        except Exception as e:
            logger.error(f"UserInputConsumer: Error processing data: {e}")
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': f"Error: {str(e)}"
            }))
# 4. Orchestration Consumer (Handles model training orchestration via WebSocket)

class ModelTrainerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Handle WebSocket disconnection if needed
        pass

    async def receive(self, text_data):
        # Parse the received WebSocket data (assuming task_id and user_input are received)
        data = json.loads(text_data)
        task_id = data.get('task_id')
        user_input = data.get('user_input')

        # Simulate model training process and send progress updates via WebSocket
        await self.run_model_trainer(task_id, user_input)

    async def run_model_trainer(self, task_id, user_input):
        """
        Simulates the model training process and sends progress updates.
        Replace this logic with actual model training orchestration.
        """
        try:
            for progress in range(0, 101, 10):
                # Simulate processing and send progress updates
                await self.send(text_data=json.dumps({
                    'progress': progress,
                    'message': f'Training model for task {task_id}: {progress}% complete'
                }))
                await asyncio.sleep(1)  # Simulate delay

            # Once training is complete, send a completion message
            await self.send(text_data=json.dumps({
                'status': 'completed',
                'message': f'Task {task_id} completed successfully.'
            }))
        except Exception as e:
            # Handle any errors during training
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': f"Error during model training: {str(e)}"
            }))
# 5. Trade Execution Consumer (Executes trades in real-time via WebSocket)
class TradeExecutionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Parse incoming trade data
        trade_data = json.loads(text_data)
        ticker = trade_data.get('ticker')
        quantity = trade_data.get('quantity')
        price = trade_data.get('price')
        action = trade_data.get('action')

        # Simulate trade execution
        await self.send(text_data=json.dumps({
            'status': 'success',
            'message': f'{action.capitalize()} {quantity} shares of {ticker} at ${price}.'
        }))

# 6. Chart Data Consumer (Handles dynamic chart data updates via WebSocket)
class ChartDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Parse chart parameters from WebSocket
        chart_params = json.loads(text_data)
        x_axis = chart_params.get('x_axis')
        y_axis = chart_params.get('y_axis')
        chart_type = chart_params.get('chart_type')

        # Simulate chart data generation
        chart_data = {
            'labels': ["Jan", "Feb", "Mar", "Apr"],  # Example labels
            'values': [10, 20, 30, 40]  # Example values
        }

        await self.send(text_data=json.dumps(chart_data))

# 7. Results Consumer (Handles fetching and updating trade results via WebSocket)
class ResultsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Import models inside the method
        from Hybrid_Trading.Trading.models import TradeResults, PerformanceMetrics, Signals
        # Now you can use the models safely
        # Parse incoming request for results data
        data = json.loads(text_data)
        tickers = data.get('tickers', [])
        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)

        try:
            if tickers:
                # Simulate fetching data for the requested tickers
                trade_results = TradeResults.objects.filter(ticker__in=tickers)
                performance_metrics = PerformanceMetrics.objects.filter(ticker__in=tickers)
                signals = Signals.objects.filter(ticker__in=tickers)

                # Apply date filtering if provided
                if start_date and end_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    trade_results = trade_results.filter(executed_at__range=(start_date, end_date))
                    performance_metrics = performance_metrics.filter(calculated_at__range=(start_date, end_date))
                    signals = signals.filter(date__range=(start_date, end_date))

                # Prepare and send results data back via WebSocket
                await self.send(text_data=json.dumps({
                    'trade_data': list(trade_results.values('final_action', 'quantity', 'current_price', 'executed_at')),
                    'performance_data': list(performance_metrics.values(
                        'sharpe_ratio', 'sortino_ratio', 'max_drawdown', 'volatility', 'annualized_return'
                    )),
                    'signal_data': list(signals.values('date', 'dynamic_decision')),
                    'status': 'success'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'error': 'No tickers provided',
                    'status': 'error'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e),
                'status': 'error'
            }))
            
class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("EchoConsumer: Attempting to connect")
        try:
            await self.accept()
            logger.info("EchoConsumer: Connection accepted")
        except Exception as e:
            logger.error(f"EchoConsumer: Connection failed: {e}")

    async def disconnect(self, close_code):
        logger.info(f"EchoConsumer: Disconnected with code {close_code}")

    async def receive(self, text_data):
        logger.info(f"EchoConsumer: Received data: {text_data}")
        try:
            # Parse the incoming JSON data
            data = json.loads(text_data)
            # Echo back the received message
            await self.send(text_data=json.dumps(data))
            logger.info("EchoConsumer: Echoed back the data")
        except json.JSONDecodeError as e:
            logger.error(f"EchoConsumer: JSON decode error: {e}")
            await self.send(json.dumps({
                'status': 'error',
                'message': f"Error: {str(e)}"
            }))