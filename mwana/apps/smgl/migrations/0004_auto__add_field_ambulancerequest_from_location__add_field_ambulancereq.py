# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'AmbulanceRequest.from_location'
        db.add_column('smgl_ambulancerequest', 'from_location', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='from_location', null=True, to=orm['locations.Location']), keep_default=False)

        # Adding field 'AmbulanceRequest.ambulance_driver'
        db.add_column('smgl_ambulancerequest', 'ambulance_driver', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ambulance_driver', null=True, to=orm['rapidsms.Contact']), keep_default=False)

        # Adding field 'AmbulanceRequest.ad_confirmed'
        db.add_column('smgl_ambulancerequest', 'ad_confirmed', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'AmbulanceRequest.ad_confirmed_on'
        db.add_column('smgl_ambulancerequest', 'ad_confirmed_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'AmbulanceRequest.triage_nurse'
        db.add_column('smgl_ambulancerequest', 'triage_nurse', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='triage_nurse', null=True, to=orm['rapidsms.Contact']), keep_default=False)

        # Adding field 'AmbulanceRequest.tn_confirmed'
        db.add_column('smgl_ambulancerequest', 'tn_confirmed', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'AmbulanceRequest.tn_confirmed_on'
        db.add_column('smgl_ambulancerequest', 'tn_confirmed_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'AmbulanceRequest.other_recipient'
        db.add_column('smgl_ambulancerequest', 'other_recipient', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='other_recipient', null=True, to=orm['rapidsms.Contact']), keep_default=False)

        # Adding field 'AmbulanceRequest.receiving_facility'
        db.add_column('smgl_ambulancerequest', 'receiving_facility', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='receiving_facility', null=True, to=orm['locations.Location']), keep_default=False)

        # Adding field 'AmbulanceRequest.requested_on'
        db.add_column('smgl_ambulancerequest', 'requested_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2012, 4, 23, 9, 30, 23, 343000), blank=True), keep_default=False)

        # Adding field 'AmbulanceRequest.sent_response'
        db.add_column('smgl_ambulancerequest', 'sent_response', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'AmbulanceRequest.from_location'
        db.delete_column('smgl_ambulancerequest', 'from_location_id')

        # Deleting field 'AmbulanceRequest.ambulance_driver'
        db.delete_column('smgl_ambulancerequest', 'ambulance_driver_id')

        # Deleting field 'AmbulanceRequest.ad_confirmed'
        db.delete_column('smgl_ambulancerequest', 'ad_confirmed')

        # Deleting field 'AmbulanceRequest.ad_confirmed_on'
        db.delete_column('smgl_ambulancerequest', 'ad_confirmed_on')

        # Deleting field 'AmbulanceRequest.triage_nurse'
        db.delete_column('smgl_ambulancerequest', 'triage_nurse_id')

        # Deleting field 'AmbulanceRequest.tn_confirmed'
        db.delete_column('smgl_ambulancerequest', 'tn_confirmed')

        # Deleting field 'AmbulanceRequest.tn_confirmed_on'
        db.delete_column('smgl_ambulancerequest', 'tn_confirmed_on')

        # Deleting field 'AmbulanceRequest.other_recipient'
        db.delete_column('smgl_ambulancerequest', 'other_recipient_id')

        # Deleting field 'AmbulanceRequest.receiving_facility'
        db.delete_column('smgl_ambulancerequest', 'receiving_facility_id')

        # Deleting field 'AmbulanceRequest.requested_on'
        db.delete_column('smgl_ambulancerequest', 'requested_on')

        # Deleting field 'AmbulanceRequest.sent_response'
        db.delete_column('smgl_ambulancerequest', 'sent_response')


    models = {
        'contactsplus.contacttype': {
            'Meta': {'object_name': 'ContactType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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
        'smgl.ambulancerequest': {
            'Meta': {'object_name': 'AmbulanceRequest'},
            'ad_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ad_confirmed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ambulance_driver': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ambulance_driver'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True', 'blank': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'er_iniator'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'danger_sign': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'from_location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'from_location'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smgl.PregnantMother']", 'null': 'True', 'blank': 'True'}),
            'mother_uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'other_recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'other_recipient'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'receiving_facility': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'receiving_facility'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'requested_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'sent_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tn_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tn_confirmed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'triage_nurse': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'triage_nurse'", 'null': 'True', 'to': "orm['rapidsms.Contact']"})
        },
        'smgl.facilityvisit': {
            'Meta': {'object_name': 'FacilityVisit'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facility_visits'", 'to': "orm['smgl.PregnantMother']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'visit_date': ('django.db.models.fields.DateField', [], {})
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
            'facility_code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'facility_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'english'", 'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['smgl']
