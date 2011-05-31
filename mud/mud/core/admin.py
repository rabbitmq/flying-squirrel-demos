from django.contrib import admin
from .models import Room, Exit, Char, Connection

class SrcInline(admin.TabularInline):
    verbose_name_plural = 'Exits'
    model = Exit
    fk_name = "src"
    extra = 1

class DstInline(admin.TabularInline):
    verbose_name_plural = 'Entries'
    model = Exit
    fk_name = "dst"
    extra = 1

class RoomAdmin(admin.ModelAdmin):
    inlines = [SrcInline, DstInline]

admin.site.register(Room, RoomAdmin)


admin.site.register(Exit)

admin.site.register(Char)

admin.site.register(Connection)

