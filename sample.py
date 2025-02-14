import uasyncio as asyncio
import socket

def http_response(status, content_type, body):
   return (f"HTTP/1.1 {status}\r\n"
           f"Content-Type: {content_type}\r\n"
           f"Content-Length: {len(body)}\r\n"
           f"Connection: close\r\n\r\n"
           f"{body}")

async def handle_request(reader, writer):
   request_line = await reader.readline()
   request = request_line.decode().strip()
   print("Request:", request)
   
   if not request:
       await writer.aclose()
       return
   
   method, path, _ = request.split(" ", 2)
   
   if path == "/":
       response = http_response("200 OK", "text/html", "<html><body><h1>Welcome</h1></body></html>")
   elif path == "/rest":
       response = http_response("200 OK", "application/json", '{"message": "Hello, REST!"}')
   elif path == "/metrics":
       response = http_response("200 OK", "text/plain", "uptime_seconds 1234\nrequests_total 42")
   elif path == "/health":
       response = http_response("200 OK", "text/plain", "OK")
   else:
       response = http_response("404 Not Found", "text/plain", "Not Found")
   
   await writer.awrite(response.encode())
   await writer.aclose()

async def run_server():
   server = await asyncio.start_server(handle_request, "0.0.0.0", 80)
   async with server:
       await server.serve_forever()

asyncio.run(run_server())

