import asyncio
import os
import sys
import warnings
from pathlib import Path

# Suppress Pydantic serializer warnings from Google ADK
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

def print_header():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("  NAIVE RAG - Local Document Q&A System")
    print("="*60)
    print("\nWhat this program does:")
    print("  • Index your documents locally (PDF, DOCX, TXT)")
    print("  • Ask questions about your documents")
    print("  • Uses Ollama (local AI) - no data leaves your computer")
    print("  • Stores documents in ChromaDB vector database")
    print("="*60 + "\n")

def show_menu():
    """Display main menu options"""
    print("\nWhat would you like to do?\n")
    print("  [1] Index a document")
    print("  [2] Chat with your documents")
    print("  [3] Exit\n")

def index_document():
    """Handle document indexing"""
    print("\n--- Document Indexing ---")
    file_path = input("Enter the full path to your document: ").strip()
    
    # Validate file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return
    
    # Import and run indexing
    try:
        from index import process_document
        print(f"\nProcessing document: {file_path}")
        process_document(file_path)
        print("✓ Document indexed successfully!")
    except Exception as e:
        print(f"❌ Error during indexing: {e}")

def start_chat():
    """Handle chat interface"""
    print("\n--- Chat Mode ---")
    print("Ask questions about your indexed documents.")
    print("Type 'exit' or 'quit' to return to main menu.\n")
    
    try:
        from query import ask_question
        
        while True:
            question = input("You: ").strip()
            
            if question.lower() in ['exit', 'quit', 'back']:
                print("Returning to main menu...\n")
                break
            
            if not question:
                continue
            
            # Get answer
            answer = asyncio.run(ask_question(question))
            print(f"\nAssistant: {answer}\n")
            
    except Exception as e:
        print(f"❌ Error during chat: {e}")

def main():
    """Main program loop"""
    print_header()
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            index_document()
        elif choice == "2":
            start_chat()
        elif choice == "3":
            print("\nGoodbye! 👋\n")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Goodbye! 👋\n")
        sys.exit(0)