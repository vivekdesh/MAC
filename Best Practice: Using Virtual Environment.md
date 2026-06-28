Best Practice: Using Virtual Environments
For managing dependencies in your Python projects, it's highly recommended to use a virtual environment. This creates an isolated environment for your project, so packages installed for one project don't interfere with others.

Here’s how you could set one up for this project:

Navigate to your project directory:

bash
cd /Users/vivek/ICICI_Direct/binance/
Create a virtual environment:

bash
/opt/homebrew/bin/python3 -m venv venv
This creates a new folder named venv in your project directory.

Activate the virtual environment:

bash
source venv/bin/activate
Your terminal prompt will change to show that you are now in the (venv) environment.