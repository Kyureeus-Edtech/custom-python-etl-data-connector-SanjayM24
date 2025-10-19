Weather ETL Data Connector

Student:Sanjay M
Roll Number: 3122 22 5001 310 
Course: Software Architecture
Assignment: Custom Python ETL Data Connector  

Overview

This ETL connector extracts weather data from the OpenWeatherMap API, transforms it for MongoDB compatibility, and loads it into a MongoDB collection. The connector implements secure authentication, error handling, rate limiting, and comprehensive logging.

API Provider

Provider: OpenWeatherMap  
Base URL: `https://api.openweathermap.org/data/2.5`  
Endpoint Used: `/weather`  Authentication: API Key (query parameter)  
Documentation: https://openweathermap.org/api

API Features Used
- Current weather data for multiple cities
- Temperature in Celsius
- Weather conditions, humidity, pressure
- Wind speed and direction
- Geographic coordinates

Project Structure

```
weather-etl-connector/
├── etl_connector.py     
├── requirements.txt     
├── .env.example        
├── .gitignore         
└── README.md          
```
Setup Instructions

1. Clone and Navigate
```bash
git clone [repository-url]
cd [your-branch-name]
```

2. Install Dependencies
```bash
pip install -r requirements.txt
```

3. Get API Key
1. Sign up at https://openweathermap.org/api
2. Generate a free API key
3. Wait 10-15 minutes for key activation

4. Configure Environment
```bash
cp .env.example .env

WEATHER_API_KEY=your_actual_api_key_here
MONGO_URL=mongodb://localhost:27017/
DB_NAME=etl_connectors
```

5. Setup MongoDB
```bash
Follow: https://docs.mongodb.com/manual/installation/
```

## Usage

### Run the ETL Pipeline
```bash
python etl_connector.py
```

### Expected Output
```
2024-01-XX XX:XX:XX - INFO - Starting ETL Pipeline for Weather Data
2024-01-XX XX:XX:XX - INFO - Successfully connected to MongoDB
2024-01-XX XX:XX:XX - INFO - Phase 1: Extracting data from Weather API
2024-01-XX XX:XX:XX - INFO - Successfully extracted data for Chennai
2024-01-XX XX:XX:XX - INFO - Successfully extracted data for Mumbai
...
2024-01-XX XX:XX:XX - INFO - Phase 2: Transforming data
2024-01-XX XX:XX:XX - INFO - Phase 3: Loading data into MongoDB
2024-01-XX XX:XX:XX - INFO - Successfully loaded 8 documents into MongoDB

==================================================
ETL PIPELINE SUMMARY
==================================================
Cities Requested: 8
Records Extracted: 8
Records Transformed: 8
Records Loaded: 8
Duration: 0:00:15.234567
Success: True
==================================================
```

## Data Flow

### 1. Extract Phase
- Connects to OpenWeatherMap API
- Fetches current weather for predefined cities
- Handles API errors, rate limits, and network issues
- Implements request delays for rate limiting

### 2. Transform Phase
- Structures raw JSON into MongoDB-compatible format
- Extracts relevant fields (temperature, weather, coordinates)
- Adds ingestion timestamps for auditing
- Validates data completeness
- Preserves raw data for future reference

### 3. Load Phase
- Connects to MongoDB
- Inserts documents into `weather_connector_raw` collection
- Logs insertion statistics
- Handles database connection errors

## Database Schema

### MongoDB Collection: `weather_connector_raw`

```json
{
  "_id": "ObjectId",
  "city_id": 1275339,
  "city_name": "Mumbai",
  "country": "IN",
  "weather": {
    "main": "Clear",
    "description": "clear sky",
    "icon": "01d"
  },
  "temperature": {
    "current": 28.5,
    "feels_like": 32.1,
    "min": 26.0,
    "max": 31.0
  },
  "humidity": 65,
  "pressure": 1013,
  "visibility": 10000,
  "wind": {
    "speed": 3.5,
    "direction": 230
  },
  "coordinates": {
    "latitude": 19.0144,
    "longitude": 72.8479
  },
  "api_timestamp": "2024-01-XX XX:XX:XX+00:00",
  "ingestion_timestamp": "2024-01-XX XX:XX:XX+00:00",
  "raw_data": { /* Original API response */ }
}
```

## Error Handling

The connector handles various error scenarios:

- **Invalid API Key** (401): Stops execution with clear error message
- **City Not Found** (404): Logs warning and continues with other cities
- **Rate Limit Exceeded** (429): Waits and retries
- **Network Errors**: Logs error and continues with next city
- **Invalid JSON**: Skips malformed responses
- **MongoDB Connection Issues**: Graceful failure with error logging
- **Data Validation**: Skips incomplete records

## Rate Limiting

- Maximum 60 requests per minute (OpenWeatherMap free tier)
- 1-second delay between requests
- Automatic retry on rate limit errors

## Security Features

- API keys stored in environment variables
- `.env` file excluded from version control
- No hardcoded credentials in source code
- MongoDB connection string configurable

## Testing Scenarios

The connector has been tested with:
- Valid API responses
- Invalid API keys
- Non-existent cities
- Network timeouts
- MongoDB connection failures
- Empty API responses
- Rate limit scenarios
- Malformed JSON responses

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| requests | 2.31.0 | HTTP API calls |
| pymongo | 4.6.1 | MongoDB operations |
| python-dotenv | 1.0.0 | Environment variable management |

## Monitoring & Logs

- Comprehensive logging at INFO level
- Execution statistics tracking
- Error categorization and reporting
- Performance timing measurements

## Future Enhancements

- Support for historical weather data
- Data deduplication mechanisms
- Configurable city lists
- Email notifications for failures
- Data quality metrics
- Automated scheduling (cron jobs)

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Solution: Verify API key in .env file and ensure it's activated
   ```

2. **MongoDB Connection Failed**
   ```
   Solution: Ensure MongoDB is running on localhost:27017
   ```

3. **No Data Extracted**
   ```
   Solution: Check internet connection and API service status
   ```
