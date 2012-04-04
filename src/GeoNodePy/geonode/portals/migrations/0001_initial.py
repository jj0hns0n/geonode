# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Portal'
        db.create_table('portals_portal', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=150, db_index=True)),
        ))
        db.send_create_signal('portals', ['Portal'])

        # Adding model 'PortalContextItem'
        db.create_table('portals_portalcontextitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('portal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portals.Portal'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=150, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('portals', ['PortalContextItem'])

        # Adding unique constraint on 'PortalContextItem', fields ['portal', 'name']
        db.create_unique('portals_portalcontextitem', ['portal_id', 'name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'PortalContextItem', fields ['portal', 'name']
        db.delete_unique('portals_portalcontextitem', ['portal_id', 'name'])

        # Deleting model 'Portal'
        db.delete_table('portals_portal')

        # Deleting model 'PortalContextItem'
        db.delete_table('portals_portalcontextitem')


    models = {
        'portals.portal': {
            'Meta': {'object_name': 'Portal'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'})
        },
        'portals.portalcontextitem': {
            'Meta': {'unique_together': "(('portal', 'name'),)", 'object_name': 'PortalContextItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '150', 'db_index': 'True'}),
            'portal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portals.Portal']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['portals']
