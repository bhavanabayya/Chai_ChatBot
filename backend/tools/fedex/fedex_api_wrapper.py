import logging
import os
import requests
from dotenv import load_dotenv
from token_service import get_token_for_provider, refresh_token_for_provider

logger = logging.getLogger(__name__)

load_dotenv()

def _request_with_auto_refresh(method, url, headers=None, **kwargs):
    provider = "fedex"
    hdrs = dict(headers or {})
    tok = get_token_for_provider(provider)
    
    if tok and isinstance(tok, dict) and tok.get("access_token"):
        hdrs.setdefault("Authorization", f"Bearer {tok['access_token']}")
    
    logger.debug(f"Making request to {url} with method {method}.")
    resp = requests.request(method.upper(), url, headers=hdrs, **kwargs)
    
    if getattr(resp, "status_code", None) in (401, 403):
        logger.warning(f"Request to {url} failed with status {resp.status_code}. Attempting token refresh.")
        try:
            new_tok = refresh_token_for_provider(provider)
            if new_tok and new_tok.get("access_token"):
                hdrs["Authorization"] = f"Bearer {new_tok['access_token']}"
                logger.info("Token refreshed successfully. Retrying request.")
                resp = requests.request(method.upper(), url, headers=hdrs, **kwargs)
            else:
                logger.error("Failed to get a new access token during refresh.")
        except Exception as e:
            logger.error(f"An exception occurred during token refresh: {e}", exc_info=True)
            raise

    logger.debug(f"Request to {url} completed with status {resp.status_code}.")
    return resp

class FedExWrapper:
    def __init__(self):
        logger.info("Initializing FedExWrapper.")
        self.token_url = "https://apis-sandbox.fedex.com/oauth/token"
        self.shipment_url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
        self.client_id = os.getenv("FEDEX_CLIENT_ID")
        self.client_secret = os.getenv("FEDEX_CLIENT_SECRET")
        self.account_number = os.getenv("FEDEX_ACCOUNT_NUMBER")
        
        # Check for missing environment variables
        if not all([self.client_id, self.client_secret, self.account_number]):
            logger.error("Missing one or more required environment variables for FedEx API (FEDEX_CLIENT_ID, FEDEX_CLIENT_SECRET, FEDEX_ACCOUNT_NUMBER).")
            raise ValueError("Missing required FedEx environment variables.")
        
        try:
            self.token = self.get_token()
        except Exception:
            logger.error("Failed to acquire FedEx token during initialization. The wrapper will be unusable.")
            raise

    def get_token(self):
        logger.info("Requesting FedEx token...")
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            response = _request_with_auto_refresh('post', self.token_url, data=data, auth=(self.client_id, self.client_secret))
            response.raise_for_status() # Raise an exception for bad status codes
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error(f"Access token not found in token response: {token_data}")
                raise Exception("Access token not found in response.")
            logger.info("FedEx token acquired successfully.")
            return access_token
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Failed to get FedEx token due to request error: {req_e}", exc_info=True)
            raise Exception(f"Request error: {req_e}")
        except Exception as e:
            logger.error(f"Failed to get FedEx token. Status: {response.status_code}, Response: {response.text}")
            raise Exception(f"Failed to get FedEx token: {response.status_code} - {response.text}")

    def create_shipment(self):
        logger.info("Attempting to create FedEx shipment.")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "x-locale": "en_US",
        }

        # A sample payload is hardcoded for demonstration purposes, though a real app would use dynamic data.
        payload = {
            "labelResponseOptions": "URL_ONLY",
            "accountNumber": {"value": self.account_number},
            "requestedShipment": {
                "shipDatestamp": "2025-08-01",
                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
                "serviceType": "FEDEX_GROUND",
                "packagingType": "YOUR_PACKAGING",
                "shipper": {
                    "contact": {
                        "personName": "Madison Doe",
                        "companyName": "Test Company 3",
                        "phoneNumber": "1234567890"
                    },
                    "address": {
                        "streetLines": ["1234 Main St"],
                        "city": "Collierville",
                        "stateOrProvinceCode": "TN",
                        "postalCode": "38017",
                        "countryCode": "US"
                    }
                },
                "recipients": [{
                    "contact": {
                        "personName": "Smith Doe",
                        "companyName": "Receiver Corp 3",
                        "phoneNumber": "0987654321"
                    },
                    "address": {
                        "streetLines": ["5678 Market St"],
                        "city": "Memphis",
                        "stateOrProvinceCode": "TN",
                        "postalCode": "38116",
                        "countryCode": "US"
                    }
                }],
                "shippingChargesPayment": {
                    "paymentType": "SENDER"
                },
                "labelSpecification": {
                    "imageType": "PDF",
                    "labelStockType": "PAPER_4X6"
                },
                "requestedPackageLineItems": [{
                    "weight": {"units": "LB", "value": 2},
                    "dimensions": {"length": 10, "width": 5, "height": 5, "units": "IN"}
                }]
            }
        }
        
        logger.debug(f"FedEx shipment payload: {payload}")

        try:
            response = _request_with_auto_refresh('post', self.shipment_url, headers=headers, json=payload)
            response.raise_for_status()
            
            json_data = response.json()
            label_url = None
            try:
                label_url = json_data.get("output", {}).get("transactionShipments", [{}])[0].get("pieceResponses", [{}])[0].get("packageDocuments", [{}])[0].get("url")
            except (IndexError, TypeError):
                logger.warning("Could not extract label URL from successful response.")
                pass

            logger.info("FedEx shipment created successfully.")
            return {
                "success": True,
                "label_url": label_url,
                "error": None
            }

        except requests.exceptions.HTTPError as http_e:
            # Handle specific HTTP errors from the API
            error_response = http_e.response.json()
            logger.error(f"Shipment failed with HTTP error: {http_e.response.status_code}. Response: {error_response}")
            return {
                "success": False,
                "label_url": None,
                "error": error_response.get("errors", [{"message": "Unknown error"}])
            }
        except Exception as e:
            # Catch all other exceptions
            logger.error(f"An unexpected exception occurred during shipment creation: {e}", exc_info=True)
            return {
                "success": False,
                "label_url": None,
                "error": str(e)
            }