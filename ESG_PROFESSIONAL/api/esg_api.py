"""
REST API Module for Third-Party ESG Platform Integration

Provides JSON/CSV endpoints for:
- All company risk data
- Sector-level aggregations
- ML model performance
- Top-N highest risk companies
"""

import pandas as pd
import json
from datetime import datetime

class ESGAPI:
    """API handler for ESG risk data"""
    
    def __init__(self):
        self.data = None
        self.ml_results = None
        self.best_model = None
    
    def set_data(self, df, ml_results=None, best_model=None):
        """Set the current dataset and ML results"""
        self.data = df
        self.ml_results = ml_results
        self.best_model = best_model
    
    def get_risk_all(self, format='json'):
        """
        GET /api/v1/risk/all
        Returns all company scores and classifications
        """
        if self.data is None:
            return {'error': 'No data available'}
        
        output_cols = [
            'ticker', 'company_name', 'sector', 'esg_score', 
            'environmental_score', 'social_score', 'governance_score',
            'risk_score', 'risk_label', 'risk_level',
            'market_cap', 'beta', 'debt_to_equity', 'profit_margin',
            'data_source', 'last_updated'
        ]
        
        available_cols = [c for c in output_cols if c in self.data.columns]
        df_export = self.data[available_cols].copy()
        
        if format == 'csv':
            return df_export.to_csv(index=False)
        else:
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'total_companies': len(df_export),
                'data': df_export.to_dict(orient='records')
            }
    
    def get_risk_sector(self):
        """
        GET /api/v1/risk/sector
        Returns aggregated sector-level risk metrics
        """
        if self.data is None:
            return {'error': 'No data available'}
        
        sector_stats = self.data.groupby('sector').agg({
            'risk_score': ['mean', 'median', 'std', 'min', 'max'],
            'esg_score': ['mean', 'median'],
            'ticker': 'count'
        }).round(4)
        
        sector_stats.columns = ['_'.join(col).strip() for col in sector_stats.columns.values]
        sector_stats = sector_stats.reset_index()
        sector_stats.rename(columns={'ticker_count': 'company_count'}, inplace=True)
        
        # Add risk distribution
        risk_dist = self.data.groupby(['sector', 'risk_label']).size().unstack(fill_value=0)
        risk_dist = risk_dist.reset_index()
        
        sector_data = pd.merge(sector_stats, risk_dist, on='sector', how='left')
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'sectors': len(sector_data),
            'data': sector_data.to_dict(orient='records')
        }
    
    def get_model_compare(self):
        """
        GET /api/v1/model/compare
        Returns ML model performance summary
        """
        if self.ml_results is None:
            return {'error': 'No ML results available'}
        
        models_summary = []
        for model_name, results in self.ml_results.items():
            models_summary.append({
                'model': model_name,
                'accuracy': round(results['mean'] * 100, 2),
                'accuracy_std': round(results['std'] * 100, 2),
                'is_best': (model_name == self.best_model)
            })
        
        # Sort by accuracy
        models_summary.sort(key=lambda x: x['accuracy'], reverse=True)
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_models': len(models_summary),
            'best_model': self.best_model,
            'best_accuracy': max([m['accuracy'] for m in models_summary]),
            'models': models_summary
        }
    
    def get_risk_top(self, n=50):
        """
        GET /api/v1/risk/top?n=50
        Returns top-N highest risk companies
        """
        if self.data is None:
            return {'error': 'No data available'}
        
        n = min(n, len(self.data))
        top_risk = self.data.nlargest(n, 'risk_score')
        
        output_cols = [
            'ticker', 'company_name', 'sector', 'risk_score', 'risk_label',
            'esg_score', 'beta', 'debt_to_equity', 'data_source'
        ]
        
        available_cols = [c for c in output_cols if c in top_risk.columns]
        df_export = top_risk[available_cols].copy()
        df_export['rank'] = range(1, len(df_export) + 1)
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'requested_n': n,
            'returned': len(df_export),
            'data': df_export.to_dict(orient='records')
        }
    
    def generate_api_doc(self):
        """Generate API documentation"""
        return {
            'title': 'ESG Risk Intelligence API',
            'version': '1.0.0',
            'description': 'REST API for ESG risk data and ML model insights',
            'endpoints': [
                {
                    'path': '/api/v1/risk/all',
                    'method': 'GET',
                    'description': 'All company scores and classifications',
                    'parameters': [
                        {'name': 'format', 'type': 'string', 'values': ['json', 'csv'], 'default': 'json'}
                    ],
                    'example': '/api/v1/risk/all?format=json'
                },
                {
                    'path': '/api/v1/risk/sector',
                    'method': 'GET',
                    'description': 'Aggregated sector-level risk metrics',
                    'parameters': [],
                    'example': '/api/v1/risk/sector'
                },
                {
                    'path': '/api/v1/model/compare',
                    'method': 'GET',
                    'description': 'ML model performance summary',
                    'parameters': [],
                    'example': '/api/v1/model/compare'
                },
                {
                    'path': '/api/v1/risk/top',
                    'method': 'GET',
                    'description': 'Top-N highest risk companies',
                    'parameters': [
                        {'name': 'n', 'type': 'integer', 'default': 50, 'max': 100}
                    ],
                    'example': '/api/v1/risk/top?n=50'
                }
            ]
        }

# Global API instance
api = ESGAPI()
