from django.contrib import admin
import BdayApp.models
# Register your models here.

admin.site.register(BdayApp.models.Category)
admin.site.register(BdayApp.models.SubCategory)
admin.site.register(BdayApp.models.GiftStore)