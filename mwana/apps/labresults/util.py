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
           
        
