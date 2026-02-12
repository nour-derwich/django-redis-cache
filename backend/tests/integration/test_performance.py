import time
import requests

API_URL = "http://localhost:8000/api/products/"

def benchmark(iterations=10):
    times = []
    for i in range(iterations):
        start = time.time()
        response = requests.get(API_URL)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Request {i+1}: {elapsed:.4f}s")
    
    print(f"\nAverage: {sum(times)/len(times):.4f}s")
    print(f"First request (cache miss): {times[0]:.4f}s")
    print(f"Cached requests avg: {sum(times[1:])/len(times[1:]):.4f}s")

benchmark()