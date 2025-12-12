#!/usr/bin/env python3
"""
Setup script for Chat with Notes RAG Application
This script helps users set up the environment and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner."""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║              📚 Chat with Your Notes                ║
    ║           RAG Application Setup Script              ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        print("Please install Python 3.8+ and try again.")
        sys.exit(1)
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def create_virtual_environment():
    """Create and activate virtual environment."""
    venv_name = "rag_env"
    
    if Path(venv_name).exists():
        print(f"📁 Virtual environment '{venv_name}' already exists")
        return venv_name
    
    print(f"🔧 Creating virtual environment '{venv_name}'...")
    try:
        subprocess.run([sys.executable, "-m", "venv", venv_name], check=True)
        print(f"✅ Virtual environment '{venv_name}' created successfully")
        return venv_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        sys.exit(1)

def get_activation_command(venv_name):
    """Get the command to activate virtual environment."""
    system = platform.system().lower()
    
    if system == "windows":
        return f"{venv_name}\\Scripts\\activate"
    else:
        return f"source {venv_name}/bin/activate"

def install_dependencies(venv_name):
    """Install required dependencies."""
    system = platform.system().lower()
    
    # Determine pip executable path
    if system == "windows":
        pip_cmd = os.path.join(venv_name, "Scripts", "pip")
    else:
        pip_cmd = os.path.join(venv_name, "bin", "pip")
    
    print("📦 Installing dependencies...")
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("You can try installing manually with:")
        print(f"  {get_activation_command(venv_name)}")
        print(f"  pip install -r requirements.txt")
        sys.exit(1)

def setup_environment_file():
    """Set up environment configuration file."""
    env_file = ".env"
    example_file = ".env.example"
    
    if Path(env_file).exists():
        print(f"📝 Environment file '{env_file}' already exists")
        return
    
    if Path(example_file).exists():
        print(f"📝 Creating '{env_file}' from '{example_file}'...")
        
        # Copy example file
        with open(example_file, 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        print(f"✅ Environment file '{env_file}' created")
        print("⚠️  IMPORTANT: Edit '.env' file and add your OpenAI API key!")
        
    else:
        print(f"⚠️  Warning: '{example_file}' not found")
        print("You'll need to create a '.env' file manually with your OpenAI API key")

def create_directories():
    """Create necessary directories."""
    dirs = ["uploads", "vector_db"]
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"📁 Created directory: {dir_name}")
        else:
            print(f"📁 Directory already exists: {dir_name}")

def print_next_steps(venv_name):
    """Print instructions for next steps."""
    activation_cmd = get_activation_command(venv_name)
    
    next_steps = f"""
    ╔══════════════════════════════════════════════════════╗
    ║                   🎉 Setup Complete!                ║
    ╚══════════════════════════════════════════════════════╝
    
    📋 Next Steps:
    
    1️⃣  Activate your virtual environment:
        {activation_cmd}
    
    2️⃣  Edit the .env file and add your OpenAI API key:
        OPENAI_API_KEY=your_actual_api_key_here
        
        Get your API key from: https://platform.openai.com/api-keys
    
    3️⃣  Run the application:
        streamlit run streamlit_app.py
    
    4️⃣  Open your browser to: http://localhost:8501
    
    ╔══════════════════════════════════════════════════════╗
    ║                  📚 Happy Learning!                 ║
    ║         Upload documents and start chatting!        ║
    ╚══════════════════════════════════════════════════════╝
    
    💡 Tips:
    - Start with small PDF or text files (under 10MB)
    - Ask specific questions about your documents
    - Check the sidebar for document management options
    
    🆘 Need Help?
    - Check README.md for detailed instructions
    - Visit: https://github.com/your-username/chat-with-notes
    
    """
    
    print(next_steps)

def main():
    """Main setup function."""
    print_banner()
    
    # Check system requirements
    check_python_version()
    
    # Set up virtual environment
    venv_name = create_virtual_environment()
    
    # Install dependencies
    install_dependencies(venv_name)
    
    # Set up environment configuration
    setup_environment_file()
    
    # Create necessary directories
    create_directories()
    
    # Print next steps
    print_next_steps(venv_name)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)