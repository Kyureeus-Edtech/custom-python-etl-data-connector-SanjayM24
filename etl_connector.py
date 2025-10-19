# ETL Weather Data Connector
# Student: [Your Name Here] - Roll No: [Your Roll Number]
# SSN College - Software Architecture Assignment

import os
import requests
import json
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
import time
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherETLConnector:
    """
    ETL Connector for OpenWeatherMap API
    Extracts weather data, transforms it for MongoDB, and loads it into database
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # API Configuration
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # MongoDB Configuration
        # MongoDB Configuration
        self.mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('DB_NAME', 'etl_connectors')
        self.collection_name = 'weather_connector_raw'
        
        # Rate limiting
        self.requests_per_minute = 60
        self.request_delay = 60 / self.requests_per_minute
        
        # Validate required environment variables
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
        
        # Initialize MongoDB connection
        self.mongo_client = None
        self.db = None
        self.collection = None
        
    def connect_to_mongodb(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            self.mongo_client = MongoClient(self.mongo_url)
            self.db = self.mongo_client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def extract_weather_data(self, cities: List[str]) -> List[Dict]:
        """
        Extract weather data from OpenWeatherMap API
        
        Args:
            cities: List of city names to fetch weather for
            
        Returns:
            List of raw API responses
        """
        extracted_data = []
        
        for city in cities:
            try:
                # Prepare API request
                endpoint = f"{self.base_url}/weather"
                params = {
                    'q': city,
                    'appid': self.api_key,
                    'units': 'metric'  # Get temperature in Celsius
                }
                
                # Make API request with error handling
                response = requests.get(endpoint, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully extracted data for {city}")
                    extracted_data.append(data)
                    
                elif response.status_code == 401:
                    logger.error("API key is invalid or expired")
                    break
                    
                elif response.status_code == 404:
                    logger.warning(f"City '{city}' not found")
                    
                elif response.status_code == 429:
                    logger.warning("Rate limit exceeded, waiting...")
                    time.sleep(60)  # Wait 1 minute
                    continue
                    
                else:
                    logger.error(f"API request failed for {city}: {response.status_code}")
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error for {city}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response for {city}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for {city}: {e}")
                continue
        
        logger.info(f"Total records extracted: {len(extracted_data)}")
        return extracted_data
    
    def transform_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transform raw API data for MongoDB compatibility
        
        Args:
            raw_data: List of raw API responses
            
        Returns:
            List of transformed documents ready for MongoDB
        """
        transformed_data = []
        
        for record in raw_data:
            try:
                # Create transformed document
                transformed_record = {
                    # Basic identifiers
                    'city_id': record.get('id'),
                    'city_name': record.get('name'),
                    'country': record.get('sys', {}).get('country'),
                    
                    # Weather information
                    'weather': {
                        'main': record.get('weather', [{}])[0].get('main'),
                        'description': record.get('weather', [{}])[0].get('description'),
                        'icon': record.get('weather', [{}])[0].get('icon')
                    },
                    
                    # Temperature data
                    'temperature': {
                        'current': record.get('main', {}).get('temp'),
                        'feels_like': record.get('main', {}).get('feels_like'),
                        'min': record.get('main', {}).get('temp_min'),
                        'max': record.get('main', {}).get('temp_max')
                    },
                    
                    # Additional metrics
                    'humidity': record.get('main', {}).get('humidity'),
                    'pressure': record.get('main', {}).get('pressure'),
                    'visibility': record.get('visibility'),
                    
                    # Wind data
                    'wind': {
                        'speed': record.get('wind', {}).get('speed'),
                        'direction': record.get('wind', {}).get('deg')
                    },
                    
                    # Coordinates
                    'coordinates': {
                        'latitude': record.get('coord', {}).get('lat'),
                        'longitude': record.get('coord', {}).get('lon')
                    },
                    
                    # Timestamps
                    'api_timestamp': datetime.fromtimestamp(
                        record.get('dt', 0), tz=timezone.utc
                    ),
                    'ingestion_timestamp': datetime.now(timezone.utc),
                    
                    # Original data for audit
                    'raw_data': record
                }
                
                # Data validation
                if transformed_record['city_name'] and transformed_record['temperature']['current']:
                    transformed_data.append(transformed_record)
                    logger.debug(f"Transformed data for {transformed_record['city_name']}")
                else:
                    logger.warning(f"Skipped incomplete record: {record.get('name', 'Unknown')}")
                    
            except Exception as e:
                logger.error(f"Error transforming record: {e}")
                continue
        
        logger.info(f"Total records transformed: {len(transformed_data)}")
        return transformed_data
    
    def load_data(self, transformed_data: List[Dict]) -> int:
        """
        Load transformed data into MongoDB collection
        
        Args:
            transformed_data: List of transformed documents
            
        Returns:
            Number of documents successfully inserted
        """
        if not transformed_data:
            logger.warning("No data to load into MongoDB")
            return 0
        
        try:
            # Insert documents into MongoDB
            result = self.collection.insert_many(transformed_data)
            inserted_count = len(result.inserted_ids)
            
            logger.info(f"Successfully loaded {inserted_count} documents into MongoDB")
            
            # Log sample of inserted data
            if inserted_count > 0:
                sample_doc = self.collection.find_one({'_id': result.inserted_ids[0]})
                logger.info(f"Sample inserted document: {sample_doc['city_name']}")
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"Failed to load data into MongoDB: {e}")
            return 0
    
    def run_etl_pipeline(self, cities: List[str]) -> Dict:
        """
        Run the complete ETL pipeline
        
        Args:
            cities: List of cities to fetch weather data for
            
        Returns:
            Dictionary with pipeline statistics
        """
        logger.info("Starting ETL Pipeline for Weather Data")
        start_time = datetime.now()
        
        stats = {
            'start_time': start_time,
            'cities_requested': len(cities),
            'records_extracted': 0,
            'records_transformed': 0,
            'records_loaded': 0,
            'success': False
        }
        
        try:
            # Connect to MongoDB
            if not self.connect_to_mongodb():
                return stats
            
            # Extract Phase
            logger.info("Phase 1: Extracting data from Weather API")
            raw_data = self.extract_weather_data(cities)
            stats['records_extracted'] = len(raw_data)
            
            # Transform Phase
            logger.info("Phase 2: Transforming data")
            transformed_data = self.transform_data(raw_data)
            stats['records_transformed'] = len(transformed_data)
            
            # Load Phase
            logger.info("Phase 3: Loading data into MongoDB")
            loaded_count = self.load_data(transformed_data)
            stats['records_loaded'] = loaded_count
            
            # Mark as successful if we loaded at least one record
            stats['success'] = loaded_count > 0
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
        
        finally:
            # Close MongoDB connection
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("MongoDB connection closed")
        
        # Calculate duration
        stats['end_time'] = datetime.now()
        stats['duration'] = stats['end_time'] - stats['start_time']
        
        # Log final statistics
        logger.info("ETL Pipeline completed")
        logger.info(f"Statistics: {stats}")
        
        return stats

def main():
    """Main execution function"""
    # List of cities to fetch weather data for
    cities = [
        "Chennai",
        "Mumbai", 
        "Delhi",
        "Bangalore",
        "Kolkata",
        "Hyderabad",
        "Pune",
        "Ahmedabad"
    ]
    
    try:
        # Initialize and run ETL connector
        connector = WeatherETLConnector()
        stats = connector.run_etl_pipeline(cities)
        
        # Print summary
        print("\n" + "="*50)
        print("ETL PIPELINE SUMMARY")
        print("="*50)
        print(f"Cities Requested: {stats['cities_requested']}")
        print(f"Records Extracted: {stats['records_extracted']}")
        print(f"Records Transformed: {stats['records_transformed']}")
        print(f"Records Loaded: {stats['records_loaded']}")
        print(f"Duration: {stats['duration']}")
        print(f"Success: {stats['success']}")
        print("="*50)
        
        # Exit code based on success
        return 0 if stats['success'] else 1
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())