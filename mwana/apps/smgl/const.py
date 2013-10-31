# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

# location type slugs
LOCTYPE_ZONE = "zone"

# contact type slugs
CTYPE_LAYCOUNSELOR = "cba"
CTYPE_DATACLERK = "dc"
CTYPE_TRIAGENURSE = 'tn'
CTYPE_INCHARGE = 'incharge'
CTYPE_CLINICWORKER = 'worker'

# from forms

REFERRAL_OUTCOME_NOSHOW = "noshow"

# shared messages
DATE_INCORRECTLY_FORMATTED_GENERAL = _("The date you entered for %(date_name)s is incorrectly formatted.  Format should be "
                                       "DD MM YYYY. Please try again.")
DATE_YEAR_INCORRECTLY_FORMATTED = _("The year you entered for date %(date_name)s is incorrectly formatted.  Should be in the format "
                                    "YYYY (four digit year). Please try again.")
DATE_MUST_BE_IN_PAST = _("The date for %(date_name)s must be in the past. Please enter a date earlier than today. You entered %(date)s")
DATE_MUST_BE_IN_FUTURE = _("The date for %(date_name)s must be in the future. Please enter a date after today. You entered %(date)s")

DATE_NOT_OPTIONAL = _("This date is not optional!")
DATE_NOT_NUMBERS = _("Date format should include only numbers: 'dd mm yyyy'")
TIME_INCORRECTLY_FORMATTED = _("The time you entered (%(time)s) is not valid. Time should be a four-digit number, like 1500.")
UNKOWN_ZONE = _("There is no zone with code %(zone)s. Please check your code and try again.")

NOT_REGISTERED=_("This phone number is not registered in the system.")
NOT_REGISTERED_FOR_DATA_ASSOC = _("Sorry, this number is not registered. Please register with the JOIN keyword and try again")
NOT_A_DATA_ASSOCIATE = _("You are not registered as a Data Associate and are not allowed to register mothers!")
MOTHER_NOT_FOUND = _("The mother's ID: %(unique_id)s was not recognized, please check and send again. If the mother was not registered enter 'none' in the place of the ID.")
GENERAL_ERROR = _("Your message is either incomplete or incorrect. Please check and send again.")

# pregnancy messages
LMP_OR_EDD_DATE_REQUIRED = _("Sorry, either the LMP or the EDD must be filled in!")
MOTHER_SUCCESS_REGISTERED = _("Thanks %(name)s! Registration for Mother ID %(unique_id)s is complete!")
NEW_MOTHER_NOTIFICATION = _("A new mother named %(mother)s with ID # %(unique_id)s was registered in your zone. Please visit this mother and take note in your register.")
DUPLICATE_REGISTRATION = _("A mother with ID %(unique_id)s is already registered. Please check the ID and try again.")

# pregnancy follow up messages
FUP_MOTHER_DOES_NOT_EXIST = _("Sorry, the mother you are trying to follow up is not registered in the system. Check the safe motherhood number ( %(unique_id) ) and try again or register her first.")
FOLLOW_UP_COMPLETE = _("Thanks %(name)s! Follow up for Mother ID %(unique_id)s is complete!")

# pregnancy postpartum visit messages
PP_MOTHER_DOES_NOT_EXIST = _("Sorry, the mother you are trying to provide post partum data for is not registered in the system. Check the safe motherhood ID ( %(unique_id) ) and try again or register her first.")
PP_MOTHER_HAS_NOT_DELIVERED = _("Sorry, the mother with ID %(unique_id) you are trying to provide post partum data for has no birth registered.")
PP_NVD_REQUIRED = _("Sorry, the mother with ID %(unique_id) has had only %(num)s post partum followup(s). 3 are required and the NVD is missing.")
PP_COMPLETE = _("Thanks %(name)s! Post Partum visit for Mother ID %(unique_id)s is complete!")

# "told" messages
TOLD_COMPLETE = _("Thanks %(name)s for reminding mother with ID %(unique_id).")
TOLD_MOTHER_HAS_ALREADY_DELIVERED = _('Mother ID %(unique_id)s has already delivered')
TOLD_MOTHER_HAS_NO_NVD = _('Mother ID %(unique_id)s has no scheduled NVD')
TOLD_MOTHER_HAS_NO_REF = _('Mother ID %(unique_id)s has no scheduled REF')

# lookup messages
LOOK_MOTHER_DOES_NOT_EXIST = _('Sorry, the mother you are trying to lookup does not exist. Please check the supplied zone id, first and last name values.')
LOOK_COMPLETE = _("The Mother ID is %(unique_id)s.")

# referrals
REFERRAL_RESPONSE = _("Thanks %(name)s! Referral for Mother ID %(unique_id)s is complete!")

REFERRAL_NOTIFICATION = _("A referral for Mother ID %(unique_id)s has been sent from %(facility)s. Please expect the mother. Reason: %(reason)s. Time: %(time)s. Emergency: %(is_emergency)s")
REFERRAL_OUTCOME_RESPONSE = _("Thanks %(name)s! Referral outcome for Mother ID %(unique_id)s was received.")
REFERRAL_OUTCOME_NOTIFICATION = _("This is outcome for Mother ID %(unique_id)s sent on %(date)s: mother is %(mother_outcome)s, Baby is %(baby_outcome)s, Mode of delivery was %(delivery_mode)s.")
REFERRAL_OUTCOME_NOTIFICATION_NOSHOW = _("This is outcome for Mother ID %(unique_id)s sent on %(date)s: mother did not show up.")
REFERRAL_NOT_FOUND = _("No referrals for Mother ID %(unique_id)s were found. Please check the mother's ID.")
REFERRAL_ALREADY_RESPONDED = _("The latest referral for Mother ID %(unique_id)s was already responded to. Please check the mother's ID.")

AMB_OUTCOME_ORIGINATING_LOCATION_INFO = _("We have been notified of the patient outcome for patient with unique_id: %(unique_id)s. Outcome: %(outcome)s")
AMB_OUTCOME_NO_OUTCOME = _("Kindly register OUTCOME for Mother :%(unique_id)s.  Please send an outcome!")

# death registration
DEATH_REG_RESPONSE = _("Thanks %(name)s! the Facility/Community death for mother with ID %(unique_id) has been registered.")
DEATH_ALREADY_REGISTERED = ("Death for mother with ID %(unique_id)s and type  %(person)s has already been registered")

# reminders
REMINDER_FU_DUE = _("Mother named %(name)s with ID # %(unique_id)s is due to visit health center %(loc)s for a follow-up visit.")
REMINDER_NON_EMERGENCY_REFERRAL = _("Mother named %(name)s with ID # %(unique_id)s should visit hospital %(loc)s as referred.")
REMINDER_EMERGENCY_REFERRAL = _("Please submit outcome SMS (REFOUT) for mother with ID %(unique_id)s referred on %(date)s from %(loc)s")
REMINDER_UPCOMING_DELIVERY = "Mother named %(name)s with ID # %(unique_id)s is due for delivery on %(date)s please follow-up visit."
REMINDER_PP_DUE = _("Mother named %(name)s with ID # %(unique_id)s is due to visit health center %(loc)s for a postpartum visit in %(num)s days.")
REMINDER_PP_MISSED = _("Mother named %(name)s with ID # %(unique_id)s is overdue to visit health center %(loc)s for a postpartum visit.")
REMINDER_SYP_TREATMENT_DUE = _("This is a reminder: Mother named %(name)s should visit the health center for follow-up on %(date)s")

# LEAVE
LEAVE_COMPLETE = _("Thanks %(name)s. You have deactivated your account.")
DEACTIVATED = _("This phone number has been deactivated.")

# IN
IN_COMPLETE = _("Thanks %(name)s. Welcome back!")
IN_REACTIVATE = _("Your account has been reactivated. Welcome back!")

# OUT
OUT_COMPLETE = _("Thanks %(name)s. Your account will be re-activated on %(date)s.")

# Syphilis
SYP_TEST_COMPLETE = _("Thanks %(name)s. A Syphilis Test Result has been recorded for %(unique_id)s. Please register the first treatment when it is given.")
SYP_TREATMENT_COMPLETE = _("Thanks %(name)s. A Syphilis Treatment has been recorded for %(unique_id)s.")

# MISC OUTBOUND SCHEDULED MESSAGES
INACTIVE_CONTACT = _("Our records indicate that you have not sent a single SMS for 14 days. You will be contacted on this matter soon by a representative")
EXPECTED_EDDS = _("We want to inform you that according to our records, your clinic should expect %(edd_count)s of mothers in the next 7 days.")
