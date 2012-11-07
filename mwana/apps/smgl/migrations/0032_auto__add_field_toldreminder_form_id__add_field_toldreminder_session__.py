# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'ToldReminder.form_id'
        db.add_column('smgl_toldreminder', 'form_id', self.gf('django.db.models.fields.CharField')(default=1, max_length=100), keep_default=False)

        # Adding field 'ToldReminder.session'
        db.add_column('smgl_toldreminder', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smsforms.XFormsSession']), keep_default=False)

        # Adding field 'ToldReminder.mother_uid'
        db.add_column('smgl_toldreminder', 'mother_uid', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'PreRegistration.form_id'
        db.add_column('smgl_preregistration', 'form_id', self.gf('django.db.models.fields.CharField')(default=1, max_length=100), keep_default=False)

        # Adding field 'PreRegistration.session'
        db.add_column('smgl_preregistration', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smsforms.XFormsSession']), keep_default=False)

        # Adding field 'DeathRegistration.form_id'
        db.add_column('smgl_deathregistration', 'form_id', self.gf('django.db.models.fields.CharField')(default=1, max_length=100), keep_default=False)

        # Adding field 'DeathRegistration.session'
        db.add_column('smgl_deathregistration', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smsforms.XFormsSession']), keep_default=False)

        # Adding field 'BirthRegistration.form_id'
        db.add_column('smgl_birthregistration', 'form_id', self.gf('django.db.models.fields.CharField')(default=1, max_length=100), keep_default=False)

        # Adding field 'BirthRegistration.session'
        db.add_column('smgl_birthregistration', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smsforms.XFormsSession']), keep_default=False)

        # Adding field 'ReminderNotification.form_id'
        db.add_column('smgl_remindernotification', 'form_id', self.gf('django.db.models.fields.CharField')(default=1, max_length=100), keep_default=False)

        # Adding field 'ReminderNotification.session'
        db.add_column('smgl_remindernotification', 'session', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['smsforms.XFormsSession']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'ToldReminder.form_id'
        db.delete_column('smgl_toldreminder', 'form_id')

        # Deleting field 'ToldReminder.session'
        db.delete_column('smgl_toldreminder', 'session_id')

        # Deleting field 'ToldReminder.mother_uid'
        db.delete_column('smgl_toldreminder', 'mother_uid')

        # Deleting field 'PreRegistration.form_id'
        db.delete_column('smgl_preregistration', 'form_id')

        # Deleting field 'PreRegistration.session'
        db.delete_column('smgl_preregistration', 'session_id')

        # Deleting field 'DeathRegistration.form_id'
        db.delete_column('smgl_deathregistration', 'form_id')

        # Deleting field 'DeathRegistration.session'
        db.delete_column('smgl_deathregistration', 'session_id')

        # Deleting field 'BirthRegistration.form_id'
        db.delete_column('smgl_birthregistration', 'form_id')

        # Deleting field 'BirthRegistration.session'
        db.delete_column('smgl_birthregistration', 'session_id')

        # Deleting field 'ReminderNotification.form_id'
        db.delete_column('smgl_remindernotification', 'form_id')

        # Deleting field 'ReminderNotification.session'
        db.delete_column('smgl_remindernotification', 'session_id')


    models = {
        'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'formplayer.xform': {
            'Meta': {'object_name': 'XForm'},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uiversion': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
            'has_independent_printer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'send_live_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'exists_in': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plural': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'singular': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': "orm['contactsplus.ContactType']"}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'smgl.ambulanceoutcome': {
            'Meta': {'object_name': 'AmbulanceOutcome'},
            'ambulance_request': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.AmbulanceRequest']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'outcome': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'outcome_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'smgl.ambulancerequest': {
            'Meta': {'object_name': 'AmbulanceRequest'},
            'ambulance_driver': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ambulance_driver'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True', 'blank': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'er_iniator'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'danger_sign': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'from_location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'from_location'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'other_recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'other_recipient'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'received_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'receiving_facility': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'receiving_facility'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'receiving_facility_recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'receiving_facility_recipient'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'requested_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'triage_nurse': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'triage_nurse'", 'null': 'True', 'to': "orm['rapidsms.Contact']"})
        },
        'smgl.ambulanceresponse': {
            'Meta': {'object_name': 'AmbulanceResponse'},
            'ambulance_request': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.AmbulanceRequest']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'responded_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'responder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'response': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'smgl.birthregistration': {
            'Meta': {'object_name': 'BirthRegistration'},
            'complications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"})
        },
        'smgl.deathregistration': {
            'Meta': {'object_name': 'DeathRegistration'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'smgl.facilityvisit': {
            'Meta': {'object_name': 'FacilityVisit'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facility_visits'", 'to': "orm['smgl.PregnantMother']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visit_date': ('django.db.models.fields.DateField', [], {})
        },
        'smgl.pregnantmother': {
            'Meta': {'object_name': 'PregnantMother'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'lmp': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_cmp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_csec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_gd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_hbp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_none': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_oth': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_reason_psb': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pregnant_mother_zones'", 'null': 'True', 'to': "orm['locations.Location']"})
        },
        'smgl.preregistration': {
            'Meta': {'object_name': 'PreRegistration'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'has_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'english'", 'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'smgl.referral': {
            'Meta': {'object_name': 'Referral'},
            'baby_outcome': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'from_facility': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'referrals_made'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode_of_delivery': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_outcome': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'mother_showed': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'reason_aph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_cpd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_ec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_fd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_hbp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_oth': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reminded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'responded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.TimeField', [], {'null': 'True'})
        },
        'smgl.remindernotification': {
            'Meta': {'object_name': 'ReminderNotification'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_notifications'", 'to': "orm['rapidsms.Contact']"}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'smgl.toldreminder': {
            'Meta': {'object_name': 'ToldReminder'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smsforms.decisiontrigger': {
            'Meta': {'object_name': 'DecisionTrigger'},
            'context_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'final_response': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trigger_keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['formplayer.XForm']"})
        },
        'smsforms.xformssession': {
            'Meta': {'object_name': 'XFormsSession'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'xform_sessions'", 'to': "orm['rapidsms.Connection']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ended': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'error_msg': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'has_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'trigger': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.DecisionTrigger']"})
        }
    }

    complete_apps = ['smgl']
