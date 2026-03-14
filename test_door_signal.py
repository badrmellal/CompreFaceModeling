#!/usr/bin/env python3
"""
Test script to verify door control signal works for both doors
"""
import requests
import os

DOOR_URL = "http://192.168.1.250:5000/controle"
LEFT_DOOR_ID = os.getenv("LEFT_DOOR_ID", "EMB_PORTE_GAUCHE")
RIGHT_DOOR_ID = os.getenv("RIGHT_DOOR_ID", "EMB_PORTE_DROITE")

def test_door_signal(autorise: bool, door_id: str):
    """Test door control signal with specified authorization status and door id"""
    signal_type = "OPEN (authorized)" if autorise else "DENY (unauthorized)"
    print(f"\n{'='*50}")
    print(f"Testing {door_id} -> {signal_type} signal")
    print(f"URL: {DOOR_URL}")
    payload = {
        "autorise": autorise,
        "door_id": door_id,
        "camera_name": f"Test-{door_id}",
        "camera_location": "EMB",
        "subject_name": "TEST_USER",
        "track_id": "test-track-001"
    }
    print(f"Sending: {payload}")
    print('='*50)

    try:
        response = requests.post(
            DOOR_URL,
            json=payload,
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

    tests = [
        (LEFT_DOOR_ID, True),
        (LEFT_DOOR_ID, False),
        (RIGHT_DOOR_ID, True),
        (RIGHT_DOOR_ID, False),
    ]

    for index, (door_id, autorise) in enumerate(tests, start=1):
        print(f"\n[{index}/{len(tests)}] Testing {door_id} with autorise={autorise}...")
        test_door_signal(autorise, door_id)
