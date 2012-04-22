# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'PregnantMother.medical_history'
        db.delete_column('smgl_pregnantmother', 'medical_history')

        # Deleting field 'PregnantMother.name'
        db.delete_column('smgl_pregnantmother', 'name')

        # Deleting field 'PregnantMother.gravitas_data'
        db.delete_column('smgl_pregnantmother', 'gravitas_data')

        # Deleting field 'PregnantMother.age'
        db.delete_column('smgl_pregnantmother', 'age')

        # Deleting field 'PregnantMother.referral'
        db.delete_column('smgl_pregnantmother', 'referral')

        # Adding field 'PregnantMother.first_name'
        db.add_column('smgl_pregnantmother', 'first_name', self.gf('django.db.models.fields.CharField')(default='First Name', max_length=160), keep_default=False)

        # Adding field 'PregnantMother.last_name'
        db.add_column('smgl_pregnantmother', 'last_name', self.gf('django.db.models.fields.CharField')(default='Last Name', max_length=160), keep_default=False)

        # Adding field 'PregnantMother.high_risk_history'
        db.add_column('smgl_pregnantmother', 'high_risk_history', self.gf('django.db.models.fields.CharField')(default=' ', max_length=160), keep_default=False)

        # Changing field 'PregnantMother.reason_for_visit'
        db.alter_column('smgl_pregnantmother', 'reason_for_visit', self.gf('django.db.models.fields.CharField')(default=' ', max_length=160))

        # Changing field 'PregnantMother.contact'
        db.alter_column('smgl_pregnantmother', 'contact_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['rapidsms.Contact']))


    def backwards(self, orm):
        
        # Adding field 'PregnantMother.medical_history'
        db.add_column('smgl_pregnantmother', 'medical_history', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True), keep_default=False)

        # Adding field 'PregnantMother.name'
        db.add_column('smgl_pregnantmother', 'name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True), keep_default=False)

        # Adding field 'PregnantMother.gravitas_data'
        db.add_column('smgl_pregnantmother', 'gravitas_data', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True), keep_default=False)

        # Adding field 'PregnantMother.age'
        db.add_column('smgl_pregnantmother', 'age', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'PregnantMother.referral'
        db.add_column('smgl_pregnantmother', 'referral', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Deleting field 'PregnantMother.first_name'
        db.delete_column('smgl_pregnantmother', 'first_name')

        # Deleting field 'PregnantMother.last_name'
        db.delete_column('smgl_pregnantmother', 'last_name')

        # Deleting field 'PregnantMother.high_risk_history'
        db.delete_column('smgl_pregnantmother', 'high_risk_history')

        # Changing field 'PregnantMother.reason_for_visit'
        db.alter_column('smgl_pregnantmother', 'reason_for_visit', self.gf('django.db.models.fields.CharField')(max_length=160, null=True))

        # Changing field 'PregnantMother.contact'
        db.alter_column('smgl_pregnantmother', 'contact_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rapidsms.Contact'], null=True))


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
        'smgl.facilityvisit': {
            'Meta': {'object_name': 'FacilityVisit'},
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
            'lmp': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'next_visit': ('django.db.models.fields.DateField', [], {}),
            'reason_for_visit': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'uid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'smgl.xformkeywordhandler': {
            'Meta': {'object_name': 'XFormKeywordHandler'},
            'function_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['smgl']
