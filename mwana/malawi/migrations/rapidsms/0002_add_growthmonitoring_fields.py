# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Contact.last_updated'
        db.add_column('rapidsms_contact', 'last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.date(2011, 2, 1), blank=True), keep_default=False)

        # Adding field 'Contact.errors'
        db.add_column('rapidsms_contact', 'errors', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=5), keep_default=False)

        # Adding field 'Contact.status'
        db.add_column('rapidsms_contact', 'status', self.gf('django.db.models.fields.CharField')(default='A', max_length=1), keep_default=False)

        # Adding field 'Contact.interviewer_id'
        db.add_column('rapidsms_contact', 'interviewer_id', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=10, null=True, blank=True), keep_default=False)

        # Adding field 'Contact.first_name'
        db.add_column('rapidsms_contact', 'first_name', self.gf('django.db.models.fields.CharField')(default='', max_length=30, blank=True), keep_default=False)

        # Adding field 'Contact.last_name'
        db.add_column('rapidsms_contact', 'last_name', self.gf('django.db.models.fields.CharField')(default='', max_length=30, blank=True), keep_default=False)

        # Changing field 'Contact.alias'
        db.alter_column('rapidsms_contact', 'alias', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20))

        # Adding unique constraint on 'Contact', fields ['alias']
        db.create_unique('rapidsms_contact', ['alias'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Contact', fields ['alias']
        db.delete_unique('rapidsms_contact', ['alias'])

        # Deleting field 'Contact.last_updated'
        db.delete_column('rapidsms_contact', 'last_updated')

        # Deleting field 'Contact.errors'
        db.delete_column('rapidsms_contact', 'errors')

        # Deleting field 'Contact.status'
        db.delete_column('rapidsms_contact', 'status')

        # Deleting field 'Contact.interviewer_id'
        db.delete_column('rapidsms_contact', 'interviewer_id')

        # Deleting field 'Contact.first_name'
        db.delete_column('rapidsms_contact', 'first_name')

        # Deleting field 'Contact.last_name'
        db.delete_column('rapidsms_contact', 'last_name')

        # Changing field 'Contact.alias'
        db.alter_column('rapidsms_contact', 'alias', self.gf('django.db.models.fields.CharField')(max_length=100))


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
        'rapidsms.app': {
            'Meta': {'object_name': 'App'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
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
            'alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '5'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interviewer_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_help_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contacts'", 'blank': 'True', 'to': "orm['contactsplus.ContactType']"})
        }
    }

    complete_apps = ['rapidsms']
