from django.contrib import admin
from .models import PujaCategory, Puja, PurohitPujaPackage

@admin.register(PujaCategory)
class PujaCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Puja)
class PujaAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_duration_hours', 'typical_venues')
    list_filter = ('category',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(PurohitPujaPackage)
class PurohitPujaPackageAdmin(admin.ModelAdmin):
    list_display = ('purohit', 'puja', 'price', 'duration_hours', 'venues', 'includes_samagri')
    list_filter = ('includes_samagri', 'puja__category')
    search_fields = ('purohit__name', 'puja__name')
