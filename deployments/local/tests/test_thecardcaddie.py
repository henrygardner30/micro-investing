"""
Test script for The Card Caddie Reward Calculation API.

All API key information and documentation is available at: thecardcaddie.com

Usage:
    python test_cardcaddie.py
"""

import requests
import json
import csv
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'https://thecardcaddie.com')
API_KEY = os.getenv('THECARDCADDIE_API_KEY', '')

def calculate_reward(card: str, merchant: str, amount: float) -> Optional[Dict[str, Any]]:
    """
    Function to test reward calculation for a single credit card transaction via The Card Caddie API.
    Returns a dictionary with reward details or None if request fails.
    
    @PARAMS:
        - card     -> name of the credit card (must be added to your account at thecardcaddie.com)
        - merchant -> merchant 
        - amount   -> transaction amount in dollars
    """
    # current api endpoint
    url = f"{API_BASE_URL}/api/v1/calculate-reward"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # required payload for the api endpoint
    # category is optional - if provided, uses category-based lookup; otherwise uses domain lookup
    payload = {
        "card": card,
        "merchant": merchant,
        "amount": amount
        # "category": "Dining"  # Optional: uncomment to test category-based lookup
    }
    
    # attempt to get reward details 
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            return data.get("reward")
        else:
            print(f"Error: {data.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def process_transactions_csv(csv_file: str) -> None:
    """
    Function to process a csv file of credit card transactions and calculate total investable rewards amount.
    Returns nothing (prints results to console).
    
    @PARAMS:
        - csv_file -> Path to CSV file with columns: date, amount, card, merchant, category
    """
    
    total_investable = 0.0
    transactions_processed = 0
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            print("\nProcessing transactions...")
            print("-" * 80)
            
            # collect the info from each row
            for row in reader:
                date = row.get('date')
                amount = float(row.get('amount', 0))
                card = row.get('card')
                merchant = row.get('merchant')
                
                # grab the reward for the transaction
                reward = calculate_reward(card, merchant, amount)
                
                if reward:
                    reward_value = reward['value']
                    total_investable += reward_value
                    transactions_processed += 1
                    
                    print(f"{date} | {card[:25]:25} | {merchant[:20]:20} | "
                          f"${amount:7.2f} | {reward['rate']:4} | ${reward_value:7.4f}")
                else:
                    print(f"{date} | {card[:25]:25} | {merchant[:20]:20} | "
                          f"${amount:7.2f} | ERROR")
            
            print("-" * 80)
            print(f"\nTotal transactions processed: {transactions_processed}")
            print(f"Total investable amount: ${total_investable:.4f}")
            
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
    except Exception as e:
        print(f"Error processing CSV: {e}")

def main():
    """
    Function to run comprehensive tests of The Card Caddie API including single transactions and CSV processing.
    """
    
    print("=" * 80)
    print("The Card Caddie API Test")
    print("=" * 80)
    
    # test 1: single transaction
    print("\nTest 1: Single Transaction")
    print("-" * 80)
    
    test_transactions = [
        {
            "card": "Chase Sapphire Preferred",
            "merchant": "starbucks",
            "amount": 25.00
        },
        {
            "card": "Wells Fargo Active Cash",
            "merchant": "amazon.com",
            "amount": 120.49
        }
    ]
    
    for txn in test_transactions:
        print(f"\nTransaction: ${txn['amount']:.2f} at {txn['merchant']} with {txn['card']}")
        
        reward = calculate_reward(
            card=txn['card'],
            merchant=txn['merchant'],
            amount=txn['amount']
        )
        
        if reward:
            print(f"[SUCCESS] Reward calculated successfully!")
            print(f"   Card: {reward['cardName']}")
            print(f"   Reward Rate: {reward['rate']}")
            print(f"   Category: {reward['category']}")
            print(f"   Category Source: {reward.get('categorySource', 'N/A')}")
            print(f"   Reward Value: ${reward['value']:.4f}")
        else:
            print(f"[ERROR] Failed to calculate reward")
    
    # test 2: process CSV file (if exists)
    print("\n" + "=" * 80)
    print("Test 2: Process CSV File")
    print("=" * 80)
    
    csv_file = "transactions.csv"
    
    # create sample csv if it doesn't exist
    try:
        with open(csv_file, 'x') as f:
            # fill in example data for the csv file for testing
            f.write("date,amount,card,merchant,category\n")
            f.write("2025-02-01,23.15,Chase Sapphire Preferred,starbucks.com,Dining\n")
            f.write("2025-02-01,120.49,Wells Fargo Active Cash,amazon.com,Shopping\n")
            f.write("2025-02-02,8.75,Fidelity Rewards,bagel-shop.com,Dining\n")
            f.write("2025-02-02,45.00,Chase Sapphire Preferred,united.com,Travel\n")
        print(f"Created sample CSV file: {csv_file}")

    # if the file already exists, use it instead of creating a new one
    except FileExistsError:
        pass
    
    # get the rewards with the transactions
    process_transactions_csv(csv_file)
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    # check if API key is set
    if not API_KEY or API_KEY == "cc_your_api_key_here":
        print("\n[WARNING] ERROR: API key not found for The Card Caddie API!")
        print("   1. Go to https://thecardcaddie.com/profile")
        print("   2. Generate a new API key")
        print("   3. Add it to your .env file:")
        print("      THECARDCADDIE_API_KEY=cc_your_key_here")
        print()
    else:
        main()