import requests
from requests.exceptions import RequestException


class BaseAPI():


    def __init__(self,rapidapi_key, rapidapi_host):
        self.api_key = rapidapi_key
        self.api_host = rapidapi_host
        
        self.base_headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": rapidapi_host
        }

    def get(self,url,headers,params=None):
        
        response = requests.request("GET", url, headers=headers, params=params)

        self._request_handler(response)

        return response

    def _request_handler(self,response):
        if response.status_code == 200:
            return True
        elif response.status_code == 204:
            self._response_attr_printer(response)
            print("ERROR")
            raise RequestException(f"Error on the API-FOOTBALL server, please inform us")
        else:
            self._response_attr_printer(response)
            print("ERROR")
            raise RequestException(f"SomeError Happened.")

    def _response_attr_printer(self,response):
        print("URL")
        print(response.url)
        print("Headers")
        print(response.headers)
        try:
            print("Params")
            print(response.params)
        except Exception:
            pass

        print("JSON")
        print(response.json())





