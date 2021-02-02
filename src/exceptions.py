class NotVotedError(Exception):
    """ Called when a user has not voted. """
    pass


class CustomCommandError(Exception):
    """ Generic command error. """
    pass
