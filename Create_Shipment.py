import requests
import os

SHIPMENT_URL = "https://apis-sandbox.fedex.com/ship/v1/shipments"


ACCOUNT_NUMBER = os.getenv("FEDEX_ACCOUNT_NUMBER")

def create_shipment(token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-locale": "en_US",
    }

    payload = {
  "labelResponseOptions": "URL_ONLY",
  "accountNumber": {
    "value": ACCOUNT_NUMBER,
  },
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
      "weight": {
        "units": "LB",
        "value": 2
      },
      "dimensions": {
        "length": 10,
        "width": 5,
        "height": 5,
        "units": "IN"
      }
    }]
  }
}


    response = requests.post(SHIPMENT_URL, headers=headers, json=payload)

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        # Attach the raw response from FedEx to debug via agent
        return {
            "error": str(err),
            "details": response.text,
            "status_code": response.status_code
        }
