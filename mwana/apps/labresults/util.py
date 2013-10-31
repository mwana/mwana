# vim: ai ts=4 sts=4 et sw=4
from mwana import const


def is_eligible_for_results(connection):
    """
    Whether a person (by connection) meets all the prerequisites
    for receiving lab results
    """
    return connection.contact is not None \
        and connection.contact.is_active \
        and const.get_clinic_worker_type() in connection.contact.types.all() \
        and connection.contact.pin is not None \
        and connection.contact.location is not None


def is_already_valid_connection_type(connection, connection_type):
    """
    Checks to see whether this person is already registered
    at the connection_type level

    ALWAYS RETURNS TRUE AT PRESENT: need to find out why
    """
    return connection.contact is not None \
        and connection.contact.is_active \
        and connection_type in connection.contact.types.all() \
        and connection.contact.pin is not None \
        and connection.contact.location is not None
