import os


def get_env_variable(var_name: str) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        var_name (str): The name of the environment variable to retrieve.

    Raises:
        ValueError: If the environment variable is not set or is empty.

    Returns:
        str: The value of the environment variable.
    """
    value = os.getenv(var_name)
    if not value:
        raise ValueError(
            f"Environment variable\
 {var_name} is not set or is empty."
        )
    return value
