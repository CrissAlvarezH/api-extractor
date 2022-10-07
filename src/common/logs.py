import logging


def reset_logging(config_id: str):
    # Remove all handlers associated with the root logger object
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format=f"ID:{config_id[:4]} %(process)s %(name)-10s %(levelname)s: %(message)s"
    )
