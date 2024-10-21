import sys
import os

# Get the absolute path to the plugin directory
plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pytest_manufacturing_api'))

# Add the plugin directory to sys.path
sys.path.insert(0, plugin_dir)

pytest_plugins = ['plugin']