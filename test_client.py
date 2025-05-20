#!/usr/bin/env python3
"""
Test client for Utec API authentication.
This script tests different authentication approaches with the Utec API.
"""

import json
import logging
import uuid
import sys
import requests
from requests.exceptions import RequestException
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("utec_test")

# API Constants
API_URL = "https://api.u-tec.com/action"
OAUTH_AUTHORIZE_URL = "https://oauth.u-tec.com/authorize"
OAUTH_TOKEN_URL = "https://oauth.u-tec.com/token"
OAUTH_SCOPE = "openapi"
OAUTH_REDIRECT_URI = "http://localhost:9501"

def test_auth_method4(client_id, client_secret):
    """Test authentication approach 4 with the Utec API (authorization code flow)."""
    logger.info("Testing authentication with Utec API - Method 4 (OAuth2 authorize endpoint)")
    session = requests.Session()
    
    # Build the authorization URL
    params = {
        "response_type": "code",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": OAUTH_SCOPE,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "state": str(uuid.uuid4())
    }
    
    auth_url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    logger.debug(f"Authorization URL: {auth_url}")
    
    try:
        # Make a GET request to the authorization URL
        response = session.get(auth_url)
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response URL: {response.url}")
        
        # Check if there was a redirect
        if len(response.history) > 0:
            logger.debug(f"Redirect history: {[r.url for r in response.history]}")
        
        # Try to find a code parameter in the response URL
        response_params = urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)
        code = response_params.get('code', [None])[0]
        
        if code:
            logger.info(f"Got authorization code: {code}")
            
            # Exchange the code for a token
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": OAUTH_REDIRECT_URI
            }
            
            token_response = session.post(OAUTH_TOKEN_URL, data=token_data)
            
            logger.debug(f"Token response status code: {token_response.status_code}")
            logger.debug(f"Token response headers: {token_response.headers}")
            
            try:
                token_result = token_response.json()
                logger.debug(f"Token response body: {json.dumps(token_result, indent=2)}")
                
                access_token = token_result.get("access_token")
                if access_token:
                    logger.info("Successfully obtained access token")
                    return access_token
            except json.JSONDecodeError:
                logger.error(f"Could not parse token response as JSON: {token_response.text}")
        else:
            logger.debug(f"Response body: {response.text}")
            logger.error("No authorization code found in the response URL")
        
        return None
            
    except RequestException as e:
        logger.error(f"Request exception: {e}")
        return None

def test_auth_direct_token_method5(client_id, client_secret):
    """Test authentication approach 5 with the Utec API (direct token request)."""
    logger.info("Testing authentication with Utec API - Method 5 (Direct token request with authorization code grant)")
    session = requests.Session()
    
    # Try to get a token directly
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": OAUTH_SCOPE
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    logger.debug(f"Token request data: {token_data}")
    
    try:
        token_response = session.post(OAUTH_TOKEN_URL, headers=headers, data=token_data)
        
        logger.debug(f"Token response status code: {token_response.status_code}")
        logger.debug(f"Token response headers: {token_response.headers}")
        
        try:
            token_result = token_response.json()
            logger.debug(f"Token response body: {json.dumps(token_result, indent=2)}")
            
            access_token = token_result.get("access_token")
            if access_token:
                logger.info("Successfully obtained access token")
                return access_token
            else:
                logger.error("No access token found in the response")
        except json.JSONDecodeError:
            logger.error(f"Could not parse token response as JSON: {token_response.text}")
        
        return None
            
    except RequestException as e:
        logger.error(f"Request exception: {e}")
        return None

def test_get_devices(session, access_token):
    """Test getting devices with the access token."""
    logger.info("Testing device listing with the access token")
    
    # Update session headers with token
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    
    device_request = {
        "header": {
            "namespace": "Uhome.Device",
            "name": "List",
            "messageId": str(uuid.uuid4()),
            "payloadVersion": "1"
        },
        "payload": {}
    }
    
    try:
        logger.debug(f"Device list request: {json.dumps(device_request, indent=2)}")
        response = session.post(API_URL, json=device_request)
        
        logger.debug(f"Response status code: {response.status_code}")
        
        try:
            result = response.json()
            logger.debug(f"Response body: {json.dumps(result, indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"Device listing failed with status code {response.status_code}")
                return False
            
            devices = result.get("payload", {}).get("devices", [])
            logger.info(f"Successfully retrieved {len(devices)} devices")
            
            # Print device details
            for i, device in enumerate(devices):
                logger.info(f"Device {i+1}:")
                logger.info(f"  ID: {device.get('id')}")
                logger.info(f"  Name: {device.get('name')}")
                logger.info(f"  Type: {device.get('type')}")
            
            return True
            
        except json.JSONDecodeError:
            logger.error(f"Could not parse response as JSON: {response.text}")
            return False
            
    except RequestException as e:
        logger.error(f"Request exception: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} CLIENT_ID CLIENT_SECRET")
        sys.exit(1)
    
    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    
    # Try each authentication method
    logger.info("Trying multiple authentication methods...")
    
    # Method 4 - Authorization endpoint
    access_token = test_auth_method4(client_id, client_secret)
    if access_token:
        logger.info("Method 4 succeeded!")
        session = requests.Session()
        success = test_get_devices(session, access_token)
        if success:
            logger.info("Method 4: Device listing succeeded")
            sys.exit(0)
        else:
            logger.warning("Method 4: Authentication worked but device listing failed")
    
    # Method 5 - Direct token request
    access_token = test_auth_direct_token_method5(client_id, client_secret)
    if access_token:
        logger.info("Method 5 succeeded!")
        session = requests.Session()
        success = test_get_devices(session, access_token)
        if success:
            logger.info("Method 5: Device listing succeeded")
            sys.exit(0)
        else:
            logger.warning("Method 5: Authentication worked but device listing failed")
    
    logger.error("All authentication methods failed")
    sys.exit(1)

if __name__ == "__main__":
    main()