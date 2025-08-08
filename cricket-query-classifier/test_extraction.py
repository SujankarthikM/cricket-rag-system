#!/usr/bin/env python3
"""
Test script for ESPNCricinfo data extraction
"""
import asyncio
from data_extraction.cricinfo_scraper import CricinfoPlayerScraper

def test_single_player():
    """Test extraction for a single player"""
    
    # Create scraper
    scraper = CricinfoPlayerScraper(output_dir="cricket_data")
    
    # Test with Virat Kohli's ID
    player_id = 253802  # Virat Kohli
    
    print(f"🏏 Testing data extraction for player ID: {player_id}")
    print("This will extract batting and bowling stats for all formats...")
    print("(Test, ODI, T20I, First-class)")
    
    try:
        # Extract data
        player_data = scraper.extract_player_data(player_id)
        
        # Show summary
        summary = scraper.get_player_summary(player_id)
        print(f"\\n📊 Extraction Summary:")
        print(f"  Player ID: {summary['player_id']}")
        print(f"  Formats: {summary['formats_available']}")
        print(f"  Total Tables: {summary['total_tables']}")
        
        # Show table counts by format
        for key, value in summary.items():
            if '_tables' in key:
                print(f"  {key}: {value}")
        
        print(f"\\n✅ Data successfully extracted and saved!")
        print(f"📁 Check the 'cricket_data' folder for JSON files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        return False

def test_multiple_players():
    """Test extraction for multiple players"""
    
    scraper = CricinfoPlayerScraper(output_dir="cricket_data")
    
    # Popular cricket players
    players = {
        253802: "Virat Kohli",
        34102: "Rohit Sharma", 
        28081: "MS Dhoni"
    }
    
    print(f"🏏 Testing extraction for {len(players)} players:")
    for player_id, name in players.items():
        print(f"  {player_id}: {name}")
    
    try:
        # Extract data for all players
        all_data = scraper.extract_multiple_players(list(players.keys()))
        
        print(f"\\n📊 Extraction completed for {len(all_data)} players")
        
        # Show summaries
        for player_id in players.keys():
            summary = scraper.get_player_summary(player_id)
            if 'error' not in summary:
                print(f"\\n{players[player_id]} ({player_id}):")
                print(f"  Formats: {summary['formats_available']}")
                print(f"  Total Tables: {summary['total_tables']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during batch extraction: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 ESPNCricinfo Data Extraction Test\\n")
    
    # Ask user what to test
    choice = input("Choose test:\\n1. Single player (Virat Kohli)\\n2. Multiple players\\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = test_single_player()
    elif choice == "2":
        success = test_multiple_players()
    else:
        print("Invalid choice. Testing single player by default...")
        success = test_single_player()
    
    if success:
        print("\\n🎉 Test completed successfully!")
        print("\\n📋 Next steps:")
        print("  1. Check the JSON files in 'cricket_data' folder")
        print("  2. Use the data to build your database")
        print("  3. Create database schema based on extracted fields")
    else:
        print("\\n⚠️  Test failed. Please check the error messages above.")