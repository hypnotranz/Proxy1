import httpx
import logging
from fastapi import HTTPException
from models.envelope import Envelope

class ForwardService:
    def __init__(self, registry_service_url):
        self.registry_service_url = registry_service_url

    async def forward_request(self, envelope: Envelope):
        logging.error(f"forward_request: Received envelope : {envelope}")
        service_name = envelope.endpoint_service_name
        logging.error(f"forward_request: service_name : {service_name}")
        service_url=""

        # Call the get_service_url endpoint to get the service URL
        async with httpx.AsyncClient() as client:
            try:
                logging.error(f"forward_request: get_service_url  :{self.registry_service_url}/get_service_url/{service_name}")

                response = await client.get(f"{self.registry_service_url}/get_service_url/{service_name}")
                logging.error(f"forward_request: get_service_url  :: {response}")

                response.raise_for_status()
                service_url = response.json().get("url").get("url")  # Extract the URL correctly from JSON response
                if not service_url:
                    raise ValueError("Service URL not found in response")
            except (httpx.HTTPStatusError, ValueError) as e:
                logging.error(f"Failed to retrieve service URL for {service_name}: {str(e)}")
                # raise HTTPException(status_code=500, detail="Failed to retrieve service URL")

        if service_url:
            # Ensure service_url is a string and construct the full URL
            endpoint_full_url = f"{service_url}{envelope.endpoint_path}"  # Construct the full URL as a string
            logging.error(f"Attempting to call: {endpoint_full_url}")
            logging.error(f"Attempting using payload: {envelope}")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=envelope.endpoint_request_type,
                        url=endpoint_full_url,  # Useenvelope the constructed full URL
                        headers=envelope.endpoint_headers,
                        params=envelope.endpoint_params,
                        json=envelope.endpoint_body
                    )
                    response.raise_for_status()
                    #logging.error(f"forward_request: response: {response.json()}")

                    return response.json()
            except httpx.RequestError as e:
                logging.error(f"Request to {endpoint_full_url} failed: {str(e)}")
                # raise HTTPException(status_code=500, detail=str(e))
        else:
            logging.error(f"forward_request: service_name : {service_name} not found")
            raise HTTPException(status_code=404, detail="Service not found")
