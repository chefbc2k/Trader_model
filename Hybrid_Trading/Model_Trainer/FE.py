import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from Hybrid_Trading.Log.Logging_Master import LoggingMaster

ogger = LoggingMaster("FeatureEngineer").get_logger()
class FeatureEngineer:
    def __init__(self, user_input):
        self.user_input = user_input
     

    def weighted_features(self, df):
        # Historical data (Intraday and Daily)
        df['weighted_open'] = df['historical_open'] * 0.4
        df['weighted_high'] = df['historical_high'] * 0.4
        df['weighted_low'] = df['historical_low'] * 0.4
        df['weighted_close'] = df['historical_close'] * 0.5
        df['weighted_volume'] = df['historical_volume'] * 0.3
        df['weighted_adjClose'] = df.get('historical_adjClose', pd.Series(0)) * 0.5
        df['weighted_changePercent'] = df.get('historical_changePercent', pd.Series(0)) * 0.2
        df['weighted_unadjustedVolume'] = df.get('historical_unadjustedVolume', pd.Series(0)) * 0.3
        df['weighted_change'] = df.get('historical_change', pd.Series(0)) * 0.2
        df['weighted_vwap'] = df.get('historical_vwap', pd.Series(0)) * 0.4

        # Financial Ratios
        df['weighted_debtEquityRatio'] = df['ratios_debtEquityRatio'] * 0.4
        df['weighted_returnOnAssets'] = df['ratios_returnOnAssets'] * 0.6
        df['weighted_returnOnEquity'] = df['ratios_returnOnEquity'] * 0.5
        df['weighted_returnOnCapitalEmployed'] = df['ratios_returnOnCapitalEmployed'] * 0.5
        df['weighted_currentRatio'] = df['ratios_currentRatio'] * 0.5
        df['weighted_quickRatio'] = df['ratios_quickRatio'] * 0.4
        df['weighted_cashRatio'] = df['ratios_cashRatio'] * 0.4
        df['weighted_grossProfitMargin'] = df['ratios_grossProfitMargin'] * 0.5
        df['weighted_operatingProfitMargin'] = df['ratios_operatingProfitMargin'] * 0.5
        df['weighted_pretaxProfitMargin'] = df['ratios_pretaxProfitMargin'] * 0.5
        df['weighted_netProfitMargin'] = df['ratios_netProfitMargin'] * 0.6
        df['weighted_effectiveTaxRate'] = df['ratios_effectiveTaxRate'] * 0.4
        df['weighted_netIncomePerEBT'] = df['ratios_netIncomePerEBT'] * 0.5
        df['weighted_ebtPerEbit'] = df['ratios_ebtPerEbit'] * 0.4
        df['weighted_ebitPerRevenue'] = df['ratios_ebitPerRevenue'] * 0.4
        df['weighted_debtRatio'] = df['ratios_debtRatio'] * 0.5
        df['weighted_longTermDebtToCapitalization'] = df['ratios_longTermDebtToCapitalization'] * 0.4
        df['weighted_totalDebtToCapitalization'] = df['ratios_totalDebtToCapitalization'] * 0.4
        df['weighted_interestCoverage'] = df['ratios_interestCoverage'] * 0.6
        df['weighted_cashFlowToDebtRatio'] = df['ratios_cashFlowToDebtRatio'] * 0.5
        df['weighted_companyEquityMultiplier'] = df['ratios_companyEquityMultiplier'] * 0.4
        df['weighted_receivablesTurnover'] = df['ratios_receivablesTurnover'] * 0.4
        df['weighted_payablesTurnover'] = df['ratios_payablesTurnover'] * 0.4
        df['weighted_inventoryTurnover'] = df['ratios_inventoryTurnover'] * 0.4
        df['weighted_fixedAssetTurnover'] = df['ratios_fixedAssetTurnover'] * 0.4
        df['weighted_assetTurnover'] = df['ratios_assetTurnover'] * 0.4
        df['weighted_operatingCashFlowPerShare'] = df['ratios_operatingCashFlowPerShare'] * 0.5
        df['weighted_freeCashFlowPerShare'] = df['ratios_freeCashFlowPerShare'] * 0.5
        df['weighted_cashPerShare'] = df['ratios_cashPerShare'] * 0.5
        df['weighted_payoutRatio'] = df['ratios_payoutRatio'] * 0.4
        df['weighted_operatingCashFlowSalesRatio'] = df['ratios_operatingCashFlowSalesRatio'] * 0.5
        df['weighted_freeCashFlowOperatingCashFlowRatio'] = df['ratios_freeCashFlowOperatingCashFlowRatio'] * 0.4
        df['weighted_cashFlowCoverageRatios'] = df['ratios_cashFlowCoverageRatios'] * 0.5
        df['weighted_shortTermCoverageRatios'] = df['ratios_shortTermCoverageRatios'] * 0.4
        df['weighted_capitalExpenditureCoverageRatio'] = df['ratios_capitalExpenditureCoverageRatio'] * 0.5
        df['weighted_dividendPaidAndCapexCoverageRatio'] = df['ratios_dividendPaidAndCapexCoverageRatio'] * 0.4
        df['weighted_dividendPayoutRatio'] = df['ratios_dividendPayoutRatio'] * 0.4
        df['weighted_priceBookValueRatio'] = df['ratios_priceBookValueRatio'] * 0.4
        df['weighted_priceToBookRatio'] = df['ratios_priceToBookRatio'] * 0.4
        df['weighted_priceToSalesRatio'] = df['ratios_priceToSalesRatio'] * 0.4
        df['weighted_priceEarningsRatio'] = df['ratios_priceEarningsRatio'] * 0.5
        df['weighted_priceToFreeCashFlowsRatio'] = df['ratios_priceToFreeCashFlowsRatio'] * 0.4
        df['weighted_priceToOperatingCashFlowsRatio'] = df['ratios_priceToOperatingCashFlowsRatio'] * 0.4
        df['weighted_priceCashFlowRatio'] = df['ratios_priceCashFlowRatio'] * 0.4
        df['weighted_priceEarningsToGrowthRatio'] = df['ratios_priceEarningsToGrowthRatio'] * 0.5
        df['weighted_priceSalesRatio'] = df['ratios_priceSalesRatio'] * 0.4
        df['weighted_dividendYield'] = df['ratios_dividendYield'] * 0.5
        df['weighted_enterpriseValueMultiple'] = df['ratios_enterpriseValueMultiple'] * 0.4
        df['weighted_priceFairValue'] = df['ratios_priceFairValue'] * 0.5

        # Key Metrics
        df['weighted_revenuePerShare'] = df['metrics_revenuePerShare'] * 0.5
        df['weighted_netIncomePerShare'] = df['metrics_netIncomePerShare'] * 0.5
        df['weighted_operatingCashFlowPerShare'] = df['metrics_operatingCashFlowPerShare'] * 0.6
        df['weighted_freeCashFlowPerShare'] = df['metrics_freeCashFlowPerShare'] * 0.6
        df['weighted_cashPerShare'] = df['metrics_cashPerShare'] * 0.5
        df['weighted_bookValuePerShare'] = df['metrics_bookValuePerShare'] * 0.5
        df['weighted_tangibleBookValuePerShare'] = df['metrics_tangibleBookValuePerShare'] * 0.5
        df['weighted_shareholdersEquityPerShare'] = df['metrics_shareholdersEquityPerShare'] * 0.5
        df['weighted_interestDebtPerShare'] = df['metrics_interestDebtPerShare'] * 0.5
        df['weighted_marketCap'] = df['metrics_marketCap'] * 0.5
        df['weighted_enterpriseValue'] = df['metrics_enterpriseValue'] * 0.4
        df['weighted_peRatio'] = df['metrics_peRatio'] * 0.5
        df['weighted_priceToSalesRatio'] = df['metrics_priceToSalesRatio'] * 0.5
        df['weighted_evToSales'] = df['metrics_evToSales'] * 0.4
        df['weighted_enterpriseValueOverEBITDA'] = df['metrics_enterpriseValueOverEBITDA'] * 0.4
        df['weighted_evToOperatingCashFlow'] = df['metrics_evToOperatingCashFlow'] * 0.4
        df['weighted_evToFreeCashFlow'] = df['metrics_evToFreeCashFlow'] * 0.4
        df['weighted_earningsYield'] = df['metrics_earningsYield'] * 0.5
        df['weighted_freeCashFlowYield'] = df['metrics_freeCashFlowYield'] * 0.5
        df['weighted_debtToEquity'] = df['metrics_debtToEquity'] * 0.4
        df['weighted_debtToAssets'] = df['metrics_debtToAssets'] * 0.4
        df['weighted_netDebtToEBITDA'] = df['metrics_netDebtToEBITDA'] * 0.5
        df['weighted_currentRatio'] = df['metrics_currentRatio'] * 0.5
        df['weighted_interestCoverage'] = df['metrics_interestCoverage'] * 0.5
        df['weighted_incomeQuality'] = df['metrics_incomeQuality'] * 0.5
        df['weighted_dividendYield'] = df['metrics_dividendYield'] * 0.5
        df['weighted_payoutRatio'] = df['metrics_payoutRatio'] * 0.4
        df['weighted_salesGeneralAndAdministrativeToRevenue'] = df['metrics_salesGeneralAndAdministrativeToRevenue'] * 0.4
        df['weighted_researchAndDevelopmentToRevenue'] = df['metrics_researchAndDevelopmentToRevenue'] * 0.4
        df['weighted_intangiblesToTotalAssets'] = df['metrics_intangiblesToTotalAssets'] * 0.4
        df['weighted_capexToOperatingCashFlow'] = df['metrics_capexToOperatingCashFlow'] * 0.4
        df['weighted_capexToRevenue'] = df['metrics_capexToRevenue'] * 0.4
        df['weighted_capexToDepreciation'] = df['metrics_capexToDepreciation'] * 0.4
        df['weighted_stockBasedCompensationToRevenue'] = df['metrics_stockBasedCompensationToRevenue'] * 0.4
        df['weighted_grahamNumber'] = df['metrics_grahamNumber'] * 0.5
        df['weighted_roic'] = df['metrics_roic'] * 0.5
        df['weighted_returnOnTangibleAssets'] = df['metrics_returnOnTangibleAssets'] * 0.5
        df['weighted_grahamNetNet'] = df['metrics_grahamNetNet'] * 0.5
        df['weighted_workingCapital'] = df['metrics_workingCapital'] * 0.5
        df['weighted_tangibleAssetValue'] = df['metrics_tangibleAssetValue'] * 0.5
        df['weighted_netCurrentAssetValue'] = df['metrics_netCurrentAssetValue'] * 0.5
        df['weighted_investedCapital'] = df['metrics_investedCapital'] * 0.5
        df['weighted_averageReceivables'] = df['metrics_averageReceivables'] * 0.4
        df['weighted_averagePayables'] = df['metrics_averagePayables'] * 0.4
        df['weighted_averageInventory'] = df['metrics_averageInventory'] * 0.4
        df['weighted_daysSalesOutstanding'] = df['metrics_daysSalesOutstanding'] * 0.4
        df['weighted_daysPayablesOutstanding'] = df['metrics_daysPayablesOutstanding'] * 0.4
        df['weighted_daysOfInventoryOnHand'] = df['metrics_daysOfInventoryOnHand'] * 0.4
        df['weighted_receivablesTurnover'] = df['metrics_receivablesTurnover'] * 0.4
        df['weighted_payablesTurnover'] = df['metrics_payablesTurnover'] * 0.4
        df['weighted_inventoryTurnover'] = df['metrics_inventoryTurnover'] * 0.4
        df['weighted_roe'] = df['metrics_roe'] * 0.5
        df['weighted_capexPerShare'] = df['metrics_capexPerShare'] * 0.4

        # Upgrades/Downgrades Data
        df['weighted_newsPublisher'] = df['upgrades_downgrades_newsPublisher'].apply(self.assign_news_weight)
        df['weighted_gradingCompany'] = df['upgrades_downgrades_gradingCompany'].apply(self.assign_grading_weight)
        df['weighted_action'] = df['upgrades_downgrades_action'].apply(self.assign_action_weight)
        df['weighted_priceWhenPosted'] = df['upgrades_downgrades_priceWhenPosted'] * 0.5

        return df

    def assign_news_weight(self, publisher):
        # Assign weights based on the publisher
        weights = {
            'Wall Street Journal': 1.0,
            'Bloomberg': 0.9,
            'CNBC': 0.8,
            'Reuters': 0.85,
            'MarketWatch': 0.75,
            'StockTwits': 0.5,
            'Other': 0.6  # Default weight for less-known publishers
        }
        return weights.get(publisher, weights['Other'])

    def assign_grading_weight(self, grading_company):
        # Assign weights based on the grading company
        weights = {
            'Moody\'s': 1.0,
            'S&P': 0.9,
            'Fitch': 0.85,
            'Morningstar': 0.8,
            'Other': 0.6  # Default weight for less-known grading companies
        }
        return weights.get(grading_company, weights['Other'])

    def assign_action_weight(self, action):
        # Assign weights based on the action taken (upgrade, downgrade, etc.)
        weights = {
            'Upgrade': 1.0,
            'Downgrade': -1.0,
            'Reaffirm': 0.5,
            'Other': 0.2  # Default weight for less-known actions
        }
        return weights.get(action, weights['Other'])

    def scale_features(self, df):
        # Apply scaling using StandardScaler
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df)
        return pd.DataFrame(df_scaled, columns=df.columns)

    def normalize_features(self, df):
        # Apply normalization using MinMaxScaler
        normalizer = MinMaxScaler()
        df_normalized = normalizer.fit_transform(df)
        return pd.DataFrame(df_normalized, columns=df.columns)
    def run_feature_engineer(self, df):
        """
        Orchestrates the feature engineering process.
        - Applies weighted features
        - Scales the features
        - Optionally normalizes the features based on user input

        Args:
            df (DataFrame): Input data containing the raw features.

        Returns:
            DataFrame: Processed DataFrame with engineered features.
        """
        self.logger.info("Starting feature engineering process.")
        
        try:
            # Step 1: Apply weighted features
            df = self.weighted_features(df)
            self.logger.info("Weighted features applied successfully.")
            
            # Step 2: Scale the features
            df = self.scale_features(df)
            self.logger.info("Feature scaling completed.")

            # Step 3: Normalize features (optional based on user input)
            if self.user_input.get('normalize', False):
                df = self.normalize_features(df)
                self.logger.info("Feature normalization completed.")

            self.logger.info("Feature engineering process completed.")
            return df
        except Exception as e:
            self.logger.error(f"Feature engineering process failed: {str(e)}")
            raise