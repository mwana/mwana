# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s


# location type slugs
LOCTYPE_ZONE = "zone"

# contact type slugs
CTYPE_LAYCOUNSELOR = "cba" # TODO: confirm / change if not correct
CTYPE_DATAASSOCIATE = "da"

# shared messages
DATE_INCORRECTLY_FORMATTED_GENERAL = _("The date you entered for %(date_name)s is incorrectly formatted.  Format should be "
                                       "DD MM YYYY. Please try again.")
DATE_YEAR_INCORRECTLY_FORMATTED = _("The year you entered for date %(date_name)s is incorrectly formatted.  Should be in the format "
                                    "YYYY (four digit year). Please try again.")
DATE_NOT_OPTIONAL = _("This date is not optional!")
UNKOWN_ZONE = _("There is no zone with code %(zone)s. Please check your code and try again.")

# pregnancy messages
LMP_OR_EDD_DATE_REQUIRED = _("Sorry, either the LMP or the EDD must be filled in!")
MOTHER_SUCCESS_REGISTERED = _("Thanks %(name)s! Registration for Mother ID %(unique_id)s is complete!")
NEW_MOTHER_NOTIFICATION = _("A new mother named %(mother)s with ID # %(unique_id)s was registered in your zone. Please take note in your register.") 

# pregnancy follow up messages
FUP_MOTHER_DOES_NOT_EXIST = _("Sorry, the mother you are trying to Follow Up is not registered in the system. Please check the UID and try again or register her first.")
FOLLOW_UP_COMPLETE = _("Thanks %(name)s! Follow up for Mother ID %(unique_id)s is complete!")
