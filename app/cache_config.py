import pandasdmx as sdmx
import requests_cache
from datetime import timedelta
import warnings
import os

class EconomicDataCache:
    """
    Manages caching strategies for economic data APIs with storage optimization.
    """
    
    def __init__(self):
        """
        Initialize the cache with different strategies for metadata vs time series data.
        """
        self.cache_enabled = False
        self.api_version = 'legacy'
        
        try:
            # Set up cache directory in user's home folder
            cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'macroeconomics')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create cached sessions
            self.metadata_cache = requests_cache.CachedSession(
                cache_name=os.path.join(cache_dir, 'metadata_cache'),
                expire_after=timedelta(days=7),
                allowable_methods=('GET',)
            )
            
            self.data_cache = requests_cache.CachedSession(
                cache_name=os.path.join(cache_dir, 'data_cache'),
                expire_after=timedelta(hours=24),
                allowable_methods=('GET',)
            )
            
            # Initialize IMF API clients - WITHOUT passing the session directly
            # We'll set the session separately due to API constraints
            self.metadata_imf = sdmx.Request('IMF')
            self.data_imf = sdmx.Request('IMF')
            
            # Now set the sessions manually
            self.metadata_imf.session = self.metadata_cache
            self.data_imf.session = self.data_cache
            
            self.cache_enabled = True
            
        except Exception as e:
            warnings.warn(f"Cache initialization failed: {e}. Using uncached requests.")
            self.metadata_imf = sdmx.Request('IMF')
            self.data_imf = sdmx.Request('IMF')
    
    def get_metadata_request(self):
        """Returns a request object for metadata with longer cache life"""
        return self.metadata_imf
    
    def get_data_request(self):
        """Returns a request object for data with shorter cache life"""
        return self.data_imf
    
    def get_fresh_request(self):
        """Returns a fresh request object that bypasses cache"""
        return sdmx.Request('IMF')

# Create the singleton instance
cache_manager = EconomicDataCache()