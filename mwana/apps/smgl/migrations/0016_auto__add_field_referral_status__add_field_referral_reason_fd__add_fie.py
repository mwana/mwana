# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Referral.status'
        db.add_column('smgl_referral', 'status', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True), keep_default=False)

        # Adding field 'Referral.reason_fd'
        db.add_column('smgl_referral', 'reason_fd', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_pec'
        db.add_column('smgl_referral', 'reason_pec', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_ec'
        db.add_column('smgl_referral', 'reason_ec', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_hbp'
        db.add_column('smgl_referral', 'reason_hbp', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_pph'
        db.add_column('smgl_referral', 'reason_pph', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_aph'
        db.add_column('smgl_referral', 'reason_aph', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_pl'
        db.add_column('smgl_referral', 'reason_pl', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_cpd'
        db.add_column('smgl_referral', 'reason_cpd', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Referral.reason_other'
        db.add_column('smgl_referral', 'reason_other', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Referral.status'
        db.delete_column('smgl_referral', 'status')

        # Deleting field 'Referral.reason_fd'
        db.delete_column('smgl_referral', 'reason_fd')

        # Deleting field 'Referral.reason_pec'
        db.delete_column('smgl_referral', 'reason_pec')

        # Deleting field 'Referral.reason_ec'
        db.delete_column('smgl_referral', 'reason_ec')

        # Deleting field 'Referral.reason_hbp'
        db.delete_column('smgl_referral', 'reason_hbp')

        # Deleting field 'Referral.reason_pph'
        db.delete_column('smgl_referral', 'reason_pph')

        # Deleting field 'Referral.reason_aph'
        db.delete_column('smgl_referral', 'reason_aph')

        # Deleting field 'Referral.reason_pl'
        db.delete_column('smgl_referral', 'reason_pl')

        # Deleting field 'Referral.reason_cpd'
        db.delete_column('smgl_referral', 'reason_cpd')

        # Deleting field 'Referral.reason_other'
        db.delete_column('smgl_referral', 'reason_other')


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
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'smgl.deathregistration': {
            'Meta': {'object_name': 'DeathRegistration'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'smgl.facilityvisit': {
            'Meta': {'object_name': 'FacilityVisit'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facility_visits'", 'to': "orm['smgl.PregnantMother']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'visit_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'smgl.pregnantmother': {
            'Meta': {'object_name': 'PregnantMother'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'edd': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'high_risk_history': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'lmp': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'uid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'smgl.preregistration': {
            'Meta': {'object_name': 'PreRegistration'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'has_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'english'", 'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'smgl.referral': {
            'Meta': {'object_name': 'Referral'},
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'form_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'reason_aph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_cpd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_ec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_fd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_hbp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_other': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reason_pph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smsforms.XFormsSession']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        },
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'smsforms.decisiontrigger': {
            'Meta': {'object_name': 'DecisionTrigger'},
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
