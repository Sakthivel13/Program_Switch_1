# In service.py - replace the get_can_configuration function

def get_can_configuration() -> Dict[str, Any]:
    """
    Get CAN interface configuration with guaranteed keys.
    Returns dict with at least 'can_interface' and 'bitrate' keys.
    """
    default_config = {
        "can_interface": "PCAN_USBBUS1",
        "bitrate": 500000,
    }

    if not CAN_UTILS_AVAILABLE:
        return default_config.copy()

    try:
        # Use can_utils.get_can_config if available
        if get_can_config is not None:
            config = get_can_config()
            # Ensure both keys exist
            return {
                "can_interface": config.get("can_interface", default_config["can_interface"]),
                "bitrate": config.get("bitrate", default_config["bitrate"]),
            }
        
        # Fallback to individual values
        interface = get_config_value("can_interface")
        bitrate = get_config_value("can_bitrate")
        vci_mode = get_config_value("vci_mode", "").lower()

        # Determine interface based on vci_mode if not set
        if not interface:
            if vci_mode == "socketcan":
                interface = "can0"
            else:
                interface = default_config["can_interface"]

        return {
            "can_interface": interface or default_config["can_interface"],
            "bitrate": int(bitrate) if bitrate else default_config["bitrate"],
        }

    except Exception as e:
        _log_error(f"Error getting CAN configuration: {e}")
        return default_config.copy()
