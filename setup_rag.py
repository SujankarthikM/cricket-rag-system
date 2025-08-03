#!/usr/bin/env python3
"""
Quick setup script for Cricket RAG System
"""

import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Packages installed successfully!")

def test_installation():
    """Test if all components can be imported"""
    print("🧪 Testing installation...")
    
    try:
        from rag_system.data_ingestion import DataIngestion
        from rag_system.vector_store import VectorStore
        print("✅ RAG components imported successfully!")
        
        # Test basic functionality
        vector_store = VectorStore()
        stats = vector_store.get_collection_stats()
        print(f"✅ Vector store initialized: {stats['total_documents']} documents")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Warning during initialization: {e}")
    
    return True

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    
    dirs_to_create = [
        Path("chroma_db"),
        Path("logs")
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)
        print(f"   Created: {dir_path}")
    
    print("✅ Directories created!")

def main():
    """Main setup function"""
    print("🏏 Cricket RAG System Setup")
    print("=" * 50)
    
    try:
        # Install requirements
        install_requirements()
        
        # Setup directories
        setup_directories()
        
        # Test installation
        if test_installation():
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Ingest your data:")
            print("   python main.py ingest")
            print("\n2. Start the API server:")
            print("   python main.py api")
            print("\n3. Test search:")
            print("   python main.py search 'your query here'")
            print("\n4. View API docs at: http://localhost:8000/docs")
        else:
            print("\n❌ Setup failed. Please check the error messages above.")
            return 1
    
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())