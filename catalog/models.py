from django.contrib.admin.decorators import register
from django.db import models
from django.db.models.base import Model
from django.db.models.fields import CharField
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth.models import User
from datetime import date

import uuid

# Create your models here.
class Genre(models.Model):
    """Model represeting book genre"""

    name = models.CharField(max_length=200, help_text="Enter the genre of the Book (e.g Science Fiction)")

    def __str__(self):
        """String for reprenting the model Object"""
        return self.name

class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200, help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name


        
class Book(models.Model):
    """Model representing the book (but not a specific copy of a book)"""

    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summery = models.TextField(max_length=1000, help_text="Enter the brief discussion of the book")
    isbn = models.CharField('ISBN', max_length=13, unique=True, help_text='13 Character a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text="Select a Genre for this book")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book"""
        return reverse('book_detail', args=[str(self.id)])
    def display_genre(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'

class BookInstance(models.Model):
    """Model representing a specific copy of a Book"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this particular book across whole library')
    book = models.ForeignKey('Book', null=True, on_delete=models.CASCADE)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False


    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default='a', help_text='Book Availability')

    class Meta():
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        """String for representing the model Object"""

        return f'{self.id}({self.book.title})'



class Author(models.Model):
    """ Model representing an Author"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)



    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the url to access the particular instance of the Author"""
        return reverse('author-details', args=[str(self.id)])

    def __str__(self):
        """String for representing the model object"""
        return f'{self.last_name}, {self.first_name}'


class BookInline(admin.TabularInline):
    """Defines format of inline book insertion (used in AuthorAdmin)"""
    model = Book

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration object for Author models.
    Defines:
     - fields to be displayed in list view (list_display)
     - orders fields in detail view (fields),
       grouping the date fields horizontally
     - adds inline addition of books in author view (inlines)
    """
    list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    inlines = [BookInline]


class BookInstanceInline(admin.TabularInline):
    model = BookInstance

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')
    inlines = [BookInstanceInline]

@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_filter = ('book', 'status', 'due_back', 'id')
    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back')
        }),
    )