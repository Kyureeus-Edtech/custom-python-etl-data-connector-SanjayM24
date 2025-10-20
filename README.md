# GreyNoise Community API - ETL Connector

**Author:** Sanjay M 
**Roll Number:** 3122 22 5001 310  
**API Provider:** GreyNoise Intelligence  

---

## 📋 Overview

This ETL pipeline extracts threat intelligence data from the **GreyNoise Community API**, which provides information about IPs scanning the internet. The connector implements 3 distinct data extraction patterns.

---

## 🎯 API Endpoints Used

### 1. **Single IP Lookup**
- **Endpoint:** `GET /v3/community/{ip}`
- **Purpose:** Query individual IP addresses for noise/RIOT classification
- **Response:** IP classification, last seen date, and metadata
- **Example:** `/v3/community/8.8.8.8`

### 2. **Batch IP Lookup** (Simulated)
- **Endpoint:** Multiple calls to `GET /v3/community/{ip}`
- **Purpose:** Bulk IP lookups with rate limiting
- **Response:** Array of IP classifications
- **Note:** Community API doesn't have native batch endpoint, so we simulate it

### 3. **Health Check / Ping**
- **Endpoint:** `GET /ping`
- **Purpose:** Verify API connectivity and authentication
- **Response:** Service status confirmation
- **Example:** Used for monitoring API availability

---

## 🔑 Authentication

GreyNoise uses **API Key authentication** via headers:

```bash
headers = {
    'key': 'YOUR_API_KEY',
    'Accept': 'application/json'
}
```

### Getting Your API Key:
1. Sign up at [GreyNoise Visualizer](https://www.greynoise.io/viz/signup)
2. Navigate to Account Settings → API Key
3. Copy your Community API key
4. Add to `.env` file

**Community Tier Limits:**
- 50 requests per week
- Shared between API and web interface
- No credit card required

---

## 🗄️ MongoDB Collections

Three collections store data from each endpoint:

1. **`greynoise_single_ip_raw`** - Single IP lookups
2. **`greynoise_batch_ip_raw`** - Batch IP lookups
3. **`greynoise_ping_raw`** - Health check logs

Each document includes:
- Original API response data
- `ingestion_timestamp` (UTC)
- `data_source` identifier
- `endpoint_type` classifier

---

## 🚀 Setup Instructions

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd your-branch-name
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy template and edit
cp .env.template .env
nano .env
```

Add your credentials:
```env
GREYNOISE_API_KEY=your_actual_api_key_here
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=greynoise_db
```

### 4. Install MongoDB
**Ubuntu/Debian:**
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows:**
Download from [MongoDB Download Center](https://www.mongodb.com/try/download/community)

### 5. Run the ETL Pipeline
```bash
python etl_connector.py
```

---

## 📊 Sample Output

```
╔═══════════════════════════════════════════════════════════╗
║         GreyNoise Community API - ETL Connector          ║
║                    3 Endpoint Pipeline                    ║
╚═══════════════════════════════════════════════════════════╝

============================================================
PIPELINE 1: Single IP Lookup
============================================================
🔍 Extracting data for IP: 8.8.8.8
✅ Successfully extracted data for 8.8.8.8
✅ Loaded single IP data to MongoDB: 67abc123...
============================================================

============================================================
PIPELINE 2: Batch IP Lookup
============================================================
🔍 Extracting batch data for 3 IPs
🔍 Extracting data for IP: 1.1.1.1
✅ Successfully extracted data for 1.1.1.1
🔍 Extracting data for IP: 8.8.4.4
✅ Successfully extracted data for 8.8.4.4
✅ Loaded 3 batch IPs to MongoDB
============================================================

============================================================
PIPELINE 3: API Health Check
============================================================
🔍 Checking API health status...
✅ Successfully retrieved API health status
✅ Loaded health check data to MongoDB: 67def456...
============================================================

🎉 All ETL pipelines completed!
✅ MongoDB connection closed
```

---

## 📦 Data Structure Examples

### Single IP Response:
```json
{
  "ip": "8.8.8.8",
  "noise": false,
  "riot": true,
  "classification": "benign",
  "name": "Google Public DNS",
  "link": "https://viz.greynoise.io/riot/8.8.8.8",
  "last_seen": "2024-10-15",
  "message": "Success",
  "ingestion_timestamp": "2025-10-20T10:30:00Z",
  "data_source": "greynoise_community_api",
  "endpoint_type": "single_ip_lookup"
}
```

### Health Check Response:
```json
{
  "status": "healthy",
  "response_data": {"offering": "community"},
  "check_timestamp": "2025-10-20T10:30:05Z",
  "data_source": "greynoise_community_api",
  "endpoint_type": "health_check"
}
```

---

## 🧪 Testing & Validation

The ETL handles:
- ✅ Rate limiting (429 errors with automatic retry)
- ✅ Invalid IP addresses
- ✅ Empty responses
- ✅ Network connectivity errors
- ✅ Authentication failures
- ✅ MongoDB connection issues

### Manual Testing:
```bash
# Test with different IPs
python -c "from etl_connector import GreyNoiseETL; etl = GreyNoiseETL(); etl.run_etl_pipeline_single_ip('1.1.1.1')"

# Verify MongoDB data
mongo
> use greynoise_db
> db.greynoise_single_ip_raw.find().pretty()
```

---

## 🔒 Security Notes

- **Never commit `.env`** - Added to `.gitignore`
- API key is loaded from environment variables only
- No hardcoded credentials in code
- MongoDB connection string configurable

---

## ⚠️ Rate Limiting

Community API: **50 requests/week**

The connector includes:
- 0.5s delays between batch requests
- Automatic rate limit detection (429 response)
- 60-second retry delay on rate limit

**Tip:** Use sparingly and test with small IP lists first!

---

## 🛠️ Customization

### Add Custom IPs:
Edit `main()` function in `etl_connector.py`:
```python
sample_ips = [
    "your.ip.address.1",
    "your.ip.address.2"
]
```

### Change MongoDB Database:
Update `.env`:
```env
MONGODB_DATABASE=your_custom_db_name
```

---

## 📚 Resources

- [GreyNoise Community API Docs](https://docs.greynoise.io/docs/using-the-greynoise-community-api)
- [GreyNoise Signup](https://www.greynoise.io/viz/signup)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [Python Dotenv](https://pypi.org/project/python-dotenv/)

---

## 🐛 Troubleshooting

**Issue:** `requests.exceptions.HTTPError: 401`  
**Solution:** Check API key in `.env` file

**Issue:** `pymongo.errors.ServerSelectionTimeoutError`  
**Solution:** Start MongoDB service

**Issue:** Rate limit exceeded  
**Solution:** Wait 1 hour or upgrade to paid plan

---

## 📝 Commit Format

```
git add .
git commit -m "Add GreyNoise ETL connector - [Your Name] - [Roll Number]"
git push origin your-branch-name
```

---

## ✅ Final Checklist

- [x] Chose GreyNoise Community API
- [x] Secured credentials in `.env`
- [x] Built 3-endpoint ETL pipeline
- [x] Tested with sample IPs
- [x] Added error handling
- [x] Documented all endpoints
- [x] Created this README
- [ ] Add your name and roll number
- [ ] Test pipeline locally
- [ ] Submit Pull Request

---

**Happy Coding! 🚀**