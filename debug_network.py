"""
Network & Database Connectivity Diagnostic for GitHub Actions
"""
import socket
import os
import sys
import psycopg2
from urllib.parse import urlparse

def check_dns(hostname):
    print(f"\n🔍 Testing DNS Resolution: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ Resolved to: {ip}")
        return ip
    except Exception as e:
        print(f"   ❌ DNS Failed: {e}")
        return None

def check_tcp(hostname, port, ip=None):
    print(f"\n🔍 Testing TCP Connection: {hostname}:{port}")
    target = ip or hostname
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((target, int(port)))
        if result == 0:
            print(f"   ✅ Port {port} is OPEN")
            return True
        else:
            print(f"   ❌ Port {port} is CLOSED/FILTERED (Err: {result})")
            print("      -> Likely Security Group blocking IP")
            return False
    except Exception as e:
        print(f"   ❌ TCP Error: {e}")
        return False
    finally:
        sock.close()

def check_db_auth(db_url):
    print(f"\n🔍 Testing Database Authentication")
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()
        print("   ✅ Authentication Successful! (Ready to write)")
        return True
    except psycopg2.OperationalError as e:
        print(f"   ❌ Auth Failed: {e}")
        return False

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL env var missing!")
        # Try constructing from parts if DATABASE_URL not set
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        port = os.getenv("DB_PORT", "5432")
        
        if host and user:
            print(f"   ℹ️ Constructing from Secrets: Host={host}, User={user}, DB={dbname}")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        else:
            sys.exit(1)

    # Parse URL
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        # Run Checks
        ip = check_dns(host)
        if ip:
            tcp_ok = check_tcp(host, port, ip)
            if tcp_ok:
                check_db_auth(db_url)
    except Exception as e:
        print(f"❌ Parse Error: {e}")
