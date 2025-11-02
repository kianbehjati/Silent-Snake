import requests
from socket import getaddrinfo
import aiohttp
class Server:
    """
    server details like city, country, org
    """
    def __init__(self, host: str):
        self.host = host
        self.city = None
        self.country = None
        self.org = None
        self.ip = None
        self.server = None
      
    async def __get_server(self, host):
        """
        fetch server header
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{host}") as resp:
                    return resp.headers.get('Server')
        except Exception as e:
            print(f"Error fetching server header: {e}")

    async def fetch_details(self):
        """
        fetch server details from ipinfo.io
        """
    
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://ipinfo.io/{getaddrinfo(self.host, None)[0][4][0]}/json") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.server = await self.__get_server(self.host)
                        self.city = data.get("city")
                        self.country = data.get("country")
                        self.ip = data.get("ip")
                        self.org = data.get("org")
           
        except Exception as e:
            print(f"Error fetching server details through ipinfo: {e}")

    def __str__(self):
        return f"\nHost: {self.host}\n City: {self.city}\n Country: {self.country}\n Org: {self.org}\n server: {self.server}\n IP: {self.ip}\n"
    
    