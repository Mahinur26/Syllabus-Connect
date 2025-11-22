#!/usr/bin/env python3
"""
Quick script to re-parse an existing syllabus.
Run this to trigger parsing for syllabi that were uploaded before the parsing feature was added.
"""

import requests
import sys

API_URL = "http://localhost:8000"

def list_syllabi(user_id):
    """List all syllabi for a user"""
    response = requests.get(f"{API_URL}/syllabi/{user_id}")
    if response.status_code == 200:
        syllabi = response.json()
        print(f"\n📚 Found {len(syllabi)} syllabi:")
        for i, syllabus in enumerate(syllabi, 1):
            print(f"\n{i}. {syllabus['name']}")
            print(f"   ID: {syllabus['id']}")
            print(f"   Uploaded: {syllabus.get('upload_date', 'Unknown')}")
        return syllabi
    else:
        print(f"❌ Error: {response.text}")
        return []

def reparse_syllabus(syllabus_id):
    """Trigger re-parsing of a syllabus"""
    print(f"\n🔄 Re-parsing syllabus {syllabus_id}...")
    response = requests.post(f"{API_URL}/syllabi/{syllabus_id}/reparse")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Parsed {data['items_count']} items")
        print(f"\nItems found:")
        for item in data['items']:
            print(f"  • [{item['category']}] {item['name']} - Due: {item['due_date']}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def get_items(syllabus_id):
    """Get items for a syllabus"""
    response = requests.get(f"{API_URL}/syllabi/{syllabus_id}/items")
    if response.status_code == 200:
        items = response.json()
        print(f"\n📋 Found {len(items)} items:")
        for item in items:
            print(f"  • [{item['category']}] {item['name']} - Due: {item['due_date']}")
        return items
    else:
        print(f"❌ Error: {response.text}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <user_id>           # List syllabi")
        print(f"  python3 {sys.argv[0]} <user_id> reparse   # Re-parse all syllabi")
        print(f"  python3 {sys.argv[0]} <syllabus_id> parse # Parse specific syllabus")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # List syllabi for user
        user_id = sys.argv[1]
        syllabi = list_syllabi(user_id)
        
        if syllabi:
            print(f"\n💡 To re-parse a syllabus, run:")
            print(f"   python3 {sys.argv[0]} <syllabus_id> parse")
    
    elif len(sys.argv) == 3:
        command = sys.argv[2]
        
        if command == "reparse":
            # Re-parse all syllabi for user
            user_id = sys.argv[1]
            syllabi = list_syllabi(user_id)
            
            if syllabi:
                for syllabus in syllabi:
                    reparse_syllabus(syllabus['id'])
                    print("\n" + "="*50)
        
        elif command == "parse":
            # Parse specific syllabus
            syllabus_id = sys.argv[1]
            reparse_syllabus(syllabus_id)
        
        elif command == "items":
            # Get items for syllabus
            syllabus_id = sys.argv[1]
            get_items(syllabus_id)
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Valid commands: reparse, parse, items")
