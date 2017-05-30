# vim: ai ts=4 sts=4 et sw=4

_ = lambda s: s
WELCOME_MSG_A = "Welcome to the mother baby service reminder program. From now we will support you until you have given birth. We will send text messages on health education and remind you to attend your 8 ANC regularly and use skilled healthcare providers at delivery. Kind regards. MoH"
WELCOME_MSG_B = "International experts recommend 8 clinic visits during pregnancy to make sure you and your baby are healthy. Your first visit should be at 16 weeks at the latest. Ask for iron and folic acid tablets. To stop messages please dial"
MISCARRIAGE_MSG = "We feel sorry that your pregnancy has ended up with a miscarriage. It's unfortunate but some miscarriages occur because the baby was not ready to live. Talk to family and friends for support and try again after 6 months."
STILL_BITH_MSG = "It's unfortunate that your baby could not survive. We are sorry for that. The health care provider who assisted you at delivery can help understand why that happened and when you can start trying again. Losing a baby is very difficult. Talk to family and friends for support."

EDUCATIONAL_MESSAGES = (
    (12,
     "12 weeks: go for ANC1 visit for a full checkup. Ask about iron and folic acid to help you get the proper nutrition. Stop messages with 555555"),
    (15,
     "Avoid taking medicine without healthcare worker's advice.  Follow their advice for your and baby's health. Please go for ANC2 visit. Stop messages with 555555"),
    (20,
     "5 months: You should feel baby kicking.  Please go for ANC3. Ask your health worker how to protect baby and yourself from tetanus. Stop messages with 555555"),
    (26,
     "26 weeks pregnant time for ANC4. Remember: wash your hands after handling animals, using the latrine and before cooking/handling food. Stop messages with 555555"),
    (28,
     "7 months pregnant: your growing baby needs iron. Take iron pills and drink milk, eat fruits, vegetables, eggs and meat or fish. Stop messages with 555555"),
    (30,
     "ANC5: ANC visits help in early detection and treatment of pregnancy problems. Make delivery plan. What facility you will deliver in? Stop messages with 555555"),
    (33,
     "Complications occur sometimes when giving birth. It's best to try and have your baby at the clinic, that way there'll be help at hand. Stop messages with 555555"),
    (33,
     "Do you know what transport can take you to the clinic? Make your birth plans today!! Ask your family to help you. Stop messages with 555555"),
    (34,
     "Please go for ANC6. If the bag of water surrounding your baby breaks, your baby is at risk of infection or the cord may come out before baby birth. These, bleeding or swelling can be danger signs, go to the clinic immediately. Stop messages with 555555"),
    (35,
     "Low back pain, gradual abdominal pains and passage of blood stained mucous might be signs of labour (the baby is ready to get born). Make sure you can get to the clinic in time or fetch your birth attendant. Don't wait. Stop messages with 555555"),
    (36, "Time for ANC7 visit. Use this check - up to ask questions about the birth. Stop messages with 555555"),
    (37,
     "Delivery is near. Have you planned where you will deliver? It is important to deliver at a health facility with skilled attendants. Stop messages with 555555"),
    (38,
     "ANC7 visit: after delivery it is important to attend postnatal care. Complications can still occur after baby is born. Stop messages with 555555"),
    (39,
     "Breastfeeding is best: it is safe, nutritious, clean, readily available, prevents illness, and helps baby grow strong. Start breastfeeding soon after delivery and let baby suckle whenever s/he wants. Stop messages with 555555"),
    (40,
     "If you have not delivered please go for ANC8 visit. If you have delivered, please visit the clinic for postnatal care."),
    (40,
     "If you have had a home delivery, visit PNC within two days after delivery. This provides opportunity to immunize your baby. Stop messages with 555555"),
    (42,
     "Congratulations, your baby is here! If you have not taken your baby to OPV0 for his/her first vaccinations please do so immediately! Stop messages with 555555"),
    (42,
     "Give baby the best: breastfeed. If s/he refuses to feed - has difficulty breathing - is either too hot or too cold or doesn't respond go the clinic immediately"),
    (44,
     "Please take your baby to the clinic for OPV1. The vaccinations your baby will receive are critical to protect him/her from diseases. Stop messages with 555555"),
    (48,
     "Please take baby to the clinic for further vaccinations and growth monitoring. The is critical to protect him/her from diseases. Stop messages with 555555"),
    (52,
     "Please take baby to the clinic for OPV3 , other vaccinations and growth monitoring. Ask your clinician about safe foods for your baby. Stop messages with 555555"),
    (76, "Please take baby for his/her measles shots. Stop messages with 555555"),
    (78, "This is the final message. Please keep taking baby for further checkups according to your under 5 card."),
    (78, "We wish you and your family all the best for your future! Remember to eat lots of fruits and vegetables"),

)
DEMO_FAIL = "Sorry you must be registered with a clinic or specify in your message to initiate a demo of ANC Messages. To specify a clinic send: DEMO <CLINIC_CODE>"