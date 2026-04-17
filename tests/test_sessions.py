import asyncio
import os
import sys
from requestez import Session as StandardSession
from requestez.asynchronous import Session as StandardAsyncSession
from requestez.kurl import Session as KurlSession, AsyncSession as KurlAsyncSession

async def test_async_sessions():
    print("\n--- Testing Async Sessions ---")
    
    # Test Standard Async (httpx)
    print("Testing Standard Async...")
    async with StandardAsyncSession() as s:
        status, _, _ = await s.get("https://httpbin.org/get")
        print(f"Standard Async GET: {status}")
        assert status == 200

    # Test Kurl Async (curl_cffi)
    print("Testing Kurl Async...")
    # Using default chrome124
    async with KurlAsyncSession() as s:
        status, _, _ = await s.get("https://httpbin.org/get")
        print(f"Kurl Async GET: {status}")
        assert status == 200
        
        # Test impersonation on a specialist site
        print("Testing Kurl Async Impersonation...")
        status, _, body = await s.get("https://tls.browserleaks.com/json")
        print(f"Kurl Impersonation GET: {status}")
        assert status == 200
        # If body is json, we could check ja3_hash

def test_sync_sessions():
    print("\n--- Testing Sync Sessions ---")
    
    # Test Standard Sync (requests)
    print("Testing Standard Sync...")
    s1 = StandardSession()
    resp = s1.get("https://httpbin.org/get", text=False)
    print(f"Standard Sync GET: {resp.status_code}")
    assert resp.status_code == 200
    
    # Test Kurl Sync (curl_cffi)
    print("Testing Kurl Sync...")
    s2 = KurlSession() # chrome124 default
    resp = s2.get("https://httpbin.org/get", text=False)
    print(f"Kurl Sync GET: {resp.status_code}")
    assert resp.status_code == 200

    # Test Downloader Mixin (Sync)
    print("Testing Downloader (Sync)...")
    s1.download("https://httpbin.org/image/png", "test.png")
    assert os.path.exists("test.png")
    os.remove("test.png")
    print("Downloader test passed.")

if __name__ == "__main__":
    # Ensure project root is in path for imports if run from tests/
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    try:
        test_sync_sessions()
        asyncio.run(test_async_sessions())
        print("\nAll session types verified successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        sys.exit(1)
