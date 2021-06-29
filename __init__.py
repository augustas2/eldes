"""
Eldes Alarms custom component.
This component implements the bare minimum that a component should implement.
Configuration:
To use the hello_world component you will need to add the following to your
configuration.yaml file.
eldes:
"""

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "eldes"


def setup(hass, config):
    """Set up a skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    hass.states.set('eldes.Eldes', 'Works!')

    # Return boolean to indicate that initialization was successfully.
    return True