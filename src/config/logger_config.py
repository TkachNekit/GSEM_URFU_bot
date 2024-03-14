import logging

LOGFILE_PATH = "C:\\Users\\nikit\PycharmProjects\GSEM_URFU_bot\std.log"


def configure_logging(is_debug: bool):
    # Determine log level based on DEBUG environment variable
    log_level = logging.INFO if is_debug else logging.WARNING

    # Configure root logger
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=log_level
    )

    # Create a file handler for error logging
    error_handler = logging.FileHandler(LOGFILE_PATH, mode="w")
    error_handler.setLevel(logging.WARNING)
    error_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    error_handler.setFormatter(error_format)

    # Add the file handler to the root logger
    logging.getLogger("").addHandler(error_handler)
