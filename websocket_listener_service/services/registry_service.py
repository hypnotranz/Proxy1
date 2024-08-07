import logging
import httpx
import asyncio
from fastapi import HTTPException
from models.register_request import RegisterRequest
from models.deregister_request import DeregisterRequest

class RegistryService:

    def __init__(self, service_registry, connection_id):
        self.service_registry = service_registry
        self.connection_id = connection_id

    async def fetch_openapi_json(self, openapi_url: str):
        retries = 5

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(openapi_url)
                    response.raise_for_status()
                    openapi_json = response.json()
                    logging.info(f"Successfully loaded OpenAPI JSON from {openapi_url}")
                    return openapi_json
            except (httpx.ConnectError, httpx.HTTPStatusError, Exception) as e:
                logging.error(f"Failed to load OpenAPI JSON: {e}")
                if attempt < retries - 1:
                    logging.info(f"Retrying to fetch OpenAPI JSON (Attempt {attempt + 1}/{retries})...")
                    await asyncio.sleep(2)
        logging.warning("OpenAPI JSON could not be loaded. Proceeding with registration without OpenAPI JSON.")
        return None

    async def register_service(self, request: RegisterRequest):
        logging.error(f"Registering service: {request.service_name} with OpenAPI URL: {request.openapi_url}")
        if not request.openapi_url:
            raise HTTPException(status_code=400, detail="OpenAPI URL is required")

        openapi_json = await self.fetch_openapi_json(request.openapi_url)
        logging.error(f"OpenAPI Contents: {openapi_json}")

        if not openapi_json or 'servers' not in openapi_json or not openapi_json['servers']:
            logging.error("OpenAPI JSON must include servers information")
            raise HTTPException(status_code=400, detail="OpenAPI JSON must include servers information")

        request.openapi_json = openapi_json

        service_info = {
            'openapi_url': request.openapi_url,
            'openapi_json': openapi_json
        }
        self.service_registry[request.service_name] = service_info
        logging.error(f"Updated service registry: {self.service_registry}")

    async def deregister_service(self, request: DeregisterRequest):
        if request.service_name in self.service_registry:
            logging.info(f"Deregistering service: {request.service_name}")
            del self.service_registry[request.service_name]
            logging.info(f"Updated service registry: {self.service_registry}")

    async def get_registered_services(self):
        logging.info(f"Fetching registered services: {self.service_registry}")
        services_view = []

        for service_name, service_info in self.service_registry.items():
            openapi_json = service_info.get('openapi_json')
            endpoints = self.extract_endpoints(openapi_json) if openapi_json else []

            service_view = {
                "service_name": service_name,
                "endpoints": endpoints
            }
            services_view.append(service_view)

        return services_view

    async def get_service_base_url(self, service_name):
        logging.error(f"Seeking {service_name} ")

        if service_name in self.service_registry:
            service_info = self.service_registry[service_name]
            openapi_json = service_info.get('openapi_json')

            if openapi_json and 'servers' in openapi_json and openapi_json['servers']:
                host = openapi_json['servers'][0].get('url')
                return {"url": host}
            else:
                logging.error("Servers list is empty or not present in the OpenAPI JSON")
        else:
            logging.error(f"Service {service_name} not found")

    def extract_endpoints(self, openapi_json):
        endpoints = []
        if openapi_json:
            paths = openapi_json.get('paths', {})
            components = openapi_json.get('components', {}).get('schemas', {})

            for path, path_info in paths.items():
                for method, method_info in path_info.items():
                    methods = [method.upper()]
                    parameters = self.extract_parameters(method_info)
                    request_body = self.extract_request_body(method_info, components)
                    endpoint = {
                        "path": path,
                        "methods": methods,
                        "parameters": parameters,
                        "requestBody": request_body
                    }
                    endpoints.append(endpoint)
        return endpoints

    def extract_parameters(self, method_info):
        parameters = []

        for param in method_info.get('parameters', []):
            parameters.append({
                "name": param.get('name', ''),
                "type": param.get('schema', {}).get('type', 'string'),
                "required": param.get('required', False),
                "in": param.get('in', 'query')
            })
        return parameters

    def extract_request_body(self, method_info, components):
        request_body = method_info.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            for content_type, content_info in content.items():
                schema_ref = content_info.get('schema', {}).get('$ref')
                schema = self.resolve_schema_ref(schema_ref, components) if schema_ref else content_info.get('schema', {})
                return {
                    "contentType": content_type,
                    "schema": schema
                }
        return {}

    def resolve_schema_ref(self, ref, components):
        if ref and ref.startswith('#/components/schemas/'):
            schema_name = ref.split('/')[-1]
            return components.get(schema_name, {})
        return {}

    async def forward_request(self, endpoint_service_name, endpoint_path, endpoint_request_type, endpoint_body):
        service_url_info = await self.get_service_base_url(endpoint_service_name)
        url = f"{service_url_info['url']}{endpoint_path}"

        async with httpx.AsyncClient() as client:
            if endpoint_request_type.upper() == 'GET':
                response = await client.get(url, json=endpoint_body)
            elif endpoint_request_type.upper() == 'POST':
                response = await client.post(url, json=endpoint_body)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

        return response.json()
