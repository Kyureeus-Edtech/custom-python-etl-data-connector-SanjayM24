"""
GreyNoise Community API - ETL Connector
Author: Sanjay M
Roll Number: 3122 22 5001 310

This ETL pipeline extracts data from GreyNoise Community API using 3 different approaches:
1. Single IP Lookup
2. Batch IP Lookup (simulated via multiple calls)
3. Ping/Health Check endpoint
"""

import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import time
import json

# Load environment variables
load_dotenv()

class GreyNoiseETL:
    """ETL Connector for GreyNoise Community API"""
    
    def __init__(self):
        self.api_key = os.getenv('GREYNOISE_API_KEY')
        self.base_url = "https://api.greynoise.io"
        self.headers = {
            'key': self.api_key,
            'Accept': 'application/json'
        }
        
        # MongoDB connection
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(mongo_uri)
        self.db = self.client[os.getenv('MONGODB_DATABASE', 'greynoise_db')]
        
        # Collections for each endpoint
        self.collection_single = self.db['greynoise_single_ip_raw']
        self.collection_batch = self.db['greynoise_batch_ip_raw']
        self.collection_ping = self.db['greynoise_ping_raw']
        
    def extract_single_ip(self, ip_address):
        """
        Endpoint 1: Single IP Lookup
        GET /v3/community/{ip}
        """
        try:
            url = f"{self.base_url}/v3/community/{ip_address}"
            print(f"🔍 Extracting data for IP: {ip_address}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Successfully extracted data for {ip_address}")
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠️  Rate limit reached. Waiting 60 seconds...")
                time.sleep(60)
                return None
            print(f"❌ HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error extracting single IP: {e}")
            return None
    
    def extract_batch_ips(self, ip_list):
        """
        Endpoint 2: Batch IP Lookup (Simulated)
        Multiple calls to /v3/community/{ip}
        """
        try:
            batch_results = []
            print(f"🔍 Extracting batch data for {len(ip_list)} IPs")
            
            for ip in ip_list:
                data = self.extract_single_ip(ip)
                if data:
                    batch_results.append(data)
                    time.sleep(0.5)  # Rate limiting courtesy
            
            print(f"✅ Successfully extracted {len(batch_results)} IPs")
            return batch_results
            
        except Exception as e:
            print(f"❌ Error in batch extraction: {e}")
            return []
    
    def extract_ping_health(self):
        """
        Endpoint 3: API Health Check / Ping
        GET /ping
        """
        try:
            url = f"{self.base_url}/ping"
            print("🔍 Checking API health status...")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print("✅ Successfully retrieved API health status")
            return data
            
        except Exception as e:
            print(f"❌ Error checking API health: {e}")
            return None
    
    def transform_single_ip(self, data):
        """Transform single IP data for MongoDB"""
        if not data:
            return None
            
        transformed = {
            'ip_address': data.get('ip'),
            'is_noise': data.get('noise', False),
            'is_riot': data.get('riot', False),
            'classification': data.get('classification'),
            'name': data.get('name'),
            'link': data.get('link'),
            'last_seen': data.get('last_seen'),
            'message': data.get('message'),
            'ingestion_timestamp': datetime.utcnow(),
            'data_source': 'greynoise_community_api',
            'endpoint_type': 'single_ip_lookup'
        }
        return transformed
    
    def transform_batch_ips(self, batch_data):
        """Transform batch IP data for MongoDB"""
        if not batch_data:
            return []
            
        transformed_batch = []
        for data in batch_data:
            transformed = {
                'ip_address': data.get('ip'),
                'is_noise': data.get('noise', False),
                'is_riot': data.get('riot', False),
                'classification': data.get('classification'),
                'name': data.get('name'),
                'last_seen': data.get('last_seen'),
                'ingestion_timestamp': datetime.utcnow(),
                'data_source': 'greynoise_community_api',
                'endpoint_type': 'batch_ip_lookup'
            }
            transformed_batch.append(transformed)
        
        return transformed_batch
    
    def transform_ping(self, data):
        """Transform ping/health data for MongoDB"""
        if not data:
            return None
            
        transformed = {
            'status': 'healthy' if data else 'unhealthy',
            'response_data': data,
            'check_timestamp': datetime.utcnow(),
            'data_source': 'greynoise_community_api',
            'endpoint_type': 'health_check'
        }
        return transformed
    
    def load_single_ip(self, transformed_data):
        """Load single IP data into MongoDB"""
        try:
            if transformed_data:
                result = self.collection_single.insert_one(transformed_data)
                print(f"✅ Loaded single IP data to MongoDB: {result.inserted_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading single IP to MongoDB: {e}")
            return False
    
    def load_batch_ips(self, transformed_batch):
        """Load batch IP data into MongoDB"""
        try:
            if transformed_batch:
                result = self.collection_batch.insert_many(transformed_batch)
                print(f"✅ Loaded {len(result.inserted_ids)} batch IPs to MongoDB")
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading batch to MongoDB: {e}")
            return False
    
    def load_ping(self, transformed_data):
        """Load ping/health data into MongoDB"""
        try:
            if transformed_data:
                result = self.collection_ping.insert_one(transformed_data)
                print(f"✅ Loaded health check data to MongoDB: {result.inserted_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading ping data to MongoDB: {e}")
            return False
    
    def run_etl_pipeline_single_ip(self, ip_address):
        """Run complete ETL for single IP endpoint"""
        print("\n" + "="*60)
        print("PIPELINE 1: Single IP Lookup")
        print("="*60)
        
        # Extract
        raw_data = self.extract_single_ip(ip_address)
        
        # Transform
        transformed_data = self.transform_single_ip(raw_data)
        
        # Load
        self.load_single_ip(transformed_data)
        
        print("="*60 + "\n")
    
    def run_etl_pipeline_batch_ips(self, ip_list):
        """Run complete ETL for batch IP endpoint"""
        print("\n" + "="*60)
        print("PIPELINE 2: Batch IP Lookup")
        print("="*60)
        
        # Extract
        raw_batch = self.extract_batch_ips(ip_list)
        
        # Transform
        transformed_batch = self.transform_batch_ips(raw_batch)
        
        # Load
        self.load_batch_ips(transformed_batch)
        
        print("="*60 + "\n")
    
    def run_etl_pipeline_ping(self):
        """Run complete ETL for ping/health endpoint"""
        print("\n" + "="*60)
        print("PIPELINE 3: API Health Check")
        print("="*60)
        
        # Extract
        raw_data = self.extract_ping_health()
        
        # Transform
        transformed_data = self.transform_ping(raw_data)
        
        # Load
        self.load_ping(transformed_data)
        
        print("="*60 + "\n")
    
    def run_all_pipelines(self):
        """Run all three ETL pipelines"""
        print("\n🚀 Starting GreyNoise ETL Connector - All Pipelines")
        print("="*60)
        
        # Pipeline 1: Single IP
        self.run_etl_pipeline_single_ip("8.8.8.8")  # Google DNS
        
        # Pipeline 2: Batch IPs
        sample_ips = [
            "1.1.1.1",      # Cloudflare DNS
            "8.8.4.4",      # Google DNS
            "9.9.9.9"       # Quad9 DNS
        ]
        self.run_etl_pipeline_batch_ips(sample_ips)
        
        # Pipeline 3: Health Check
        self.run_etl_pipeline_ping()
        
        print("🎉 All ETL pipelines completed!")
        
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        print("✅ MongoDB connection closed")


def main():
    """Main execution function"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         GreyNoise Community API - ETL Connector          ║
    ║                    3 Endpoint Pipeline                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Initialize ETL connector
    etl = GreyNoiseETL()
    
    try:
        # Run all pipelines
        etl.run_all_pipelines()
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
    finally:
        etl.close()


if __name__ == "__main__":
    main()