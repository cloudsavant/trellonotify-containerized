"""
Testing the configuration management functions
"""

import pytest
import yaml
from main import load_config, get_secret

# Sample configuration for testing
sample_config = {
    "secrets": {
        "TRELLO_KEY": "your_trello_key",
        "TRELLO_TOKEN": "your_trello_token",
        "TRELLO_LIST_ID": "your_trello_list_id",
        "SLACK_API_TOKEN": "your_slack_api_token",
        "SLACK_CHANNEL_ID": "your_slack_channel_id",
    },
    "db": {"DB_FILE": "db.csv"},
}



@pytest.fixture(scope="module")
def config_file(tmpdir_factory):
    '''
    Create a temporary configuration file with sample configuration
    '''
    temp_config_file = tmpdir_factory.mktemp("data").join("config.yaml")
    with open(temp_config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return config_file


def test_load_config(temp_config_file, monkeypatch):
    '''
    Test loading the configuration from a temporary file
    '''
    # Set the CONFIG_PATH environment variable to the path of the temporary config file
    monkeypatch.setenv("CONFIG_PATH", str(temp_config_file))

    # Load the configuration
    config = load_config()

    # Assert that the loaded configuration matches the sample configuration
    assert config == sample_config


def test_get_secret(temp_config_file, monkeypatch):
    '''
    Test retrieving secrets from the configuration
    '''
    # Set the CONFIG_PATH environment variable to the path of the temporary config file
    monkeypatch.setenv("CONFIG_PATH", str(temp_config_file))

    # Load the configuration
    config = load_config()

    # Test retrieving secrets
    assert get_secret("TRELLO_KEY") == "your_trello_key"
    assert get_secret("TRELLO_TOKEN") == "your_trello_token"
    assert get_secret("TRELLO_LIST_ID") == "your_trello_list_id"
    assert get_secret("SLACK_API_TOKEN") == "your_slack_api_token"
    assert get_secret("SLACK_CHANNEL_ID") == "your_slack_channel_id"

    # Test retrieving a non-existent secret
    with pytest.raises(
        ValueError, match="Secret NON_EXISTENT_SECRET not found in configuration"
    ):
        get_secret("NON_EXISTENT_SECRET")
