from django.db import models
from django.contrib.auth.models import User, Permission
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from geonode.contrib.services.enumerations import SERVICE_TYPES, SERVICE_METHODS
from geonode.core.security.models import PermissionLevelMixin
from geonode.core.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.core.people.models import Contact, Role

class Service(models.Model, PermissionLevelMixin):
    """
    Service Class to represent remote Geo Web Services
    """
    
    type = models.CharField(max_length=4, choices=SERVICE_TYPES)
    method = models.CharField(max_length=1, choices=SERVICE_METHODS)
    base_url = models.URLField(verify_exists=False, unique=True) # with service, version and request etc stripped off 
    version = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True) #Should force to slug?
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    abstract = models.TextField(null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)
    online_resource = models.URLField(verify_exists = False, null=True, blank=True)
    fees = models.CharField(max_length=1000, null=True, blank=True)
    access_contraints = models.CharField(max_length=255, null=True, blank=True)
    connection_params = models.TextField(null=True, blank=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    workspace_ref = models.URLField(verify_exists = False, null=True, blank=True)
    store_ref = models.URLField(verify_exists = False, null=True, blank=True)
    resources_ref = models.URLField(verify_exists = False, null = True, blank = True)
    contacts = models.ManyToManyField(Contact, through='ServiceContactRole')
    owner = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    first_noanswer = models.DateTimeField(null=True, blank=True)
    noanswer_retries = models.PositiveIntegerField(null=True, blank=True)
    uuid = models.CharField(max_length=36, null=True, blank=True)
    external_id = models.IntegerField(null=True, blank=True)

    # Supported Capabilities
    
    def __unicode__(self):
        return self.name

    def layers(self):
        """Return a list of all the child layers (resources) for this Service"""
        pass 

    def get_absolute_url(self):
        return '/services/%i' % self.id
        
    class Meta:
        # custom permissions, 
        # change and delete are standard in django
        permissions = (('view_service', 'Can view'), 
                       ('change_service_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'service_readonly'
    LEVEL_WRITE = 'service_readwrite'
    LEVEL_ADMIN = 'service_admin'
    
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN) 

class ServiceContactRole(models.Model):
    """
    ServiceContactRole is an intermediate model to bind Contacts and Services and apply roles.
    """
    contact = models.ForeignKey(Contact)
    service = models.ForeignKey(Service)
    role = models.ForeignKey(Role)

def post_save_service(instance, sender, created, **kwargs):
    if created:
        instance.set_default_permissions()    

def pre_delete_service(instance, sender, **kwargs):
    if instance.method == 'H':
        gn = Layer.objects.gn_catalog
        gn.control_harvesting_task('stop', [instance.external_id]) 
        gn.control_harvesting_task('remove', [instance.external_id]) 

signals.pre_delete.connect(pre_delete_service, sender=Service)
signals.post_save.connect(post_save_service, sender=Service)
