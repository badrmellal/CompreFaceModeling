#!/usr/bin/env python3
"""
Test script to verify door control signal works
"""
import requests
import sys

DOOR_URL = "http://192.168.1.250:5000/controle"

def test_door_signal(autorise: bool):
    """Test door control signal with specified authorization status"""
    signal_type = "OPEN (authorized)" if autorise else "DENY (unauthorized)"
    print(f"\n{'='*50}")
    print(f"Testing door {signal_type} signal")
    print(f"URL: {DOOR_URL}")
    print(f"Sending: {{'autorise': {autorise}}}")
    print('='*50)

    try:
        response = requests.post(
            DOOR_URL,
            json={"autorise": autorise},
            timeout=5
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print(f"✓ SUCCESS - Door {signal_type} signal sent!")
            return True
        else:
            print(f"✗ FAILED - HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ TIMEOUT - Raspberry Pi not responding")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ CONNECTION ERROR - Cannot reach Raspberry Pi")
        print("Make sure:")
        print("  1. Raspberry Pi is on and connected to network")
        print("  2. IP address 192.168.1.250 is correct")
        print("  3. Port 5000 is open")
        print("  4. Flask app is running on the Pi")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Door Control Signal Test")
    print("========================")
    
    # Test both signals
    print("\n[1/2] Testing AUTHORIZED signal (autorise=True)...")
    test_door_signal(True)
    
    print("\n[2/2] Testing UNAUTHORIZED signal (autorise=False)...")
    test_door_signal(False)
