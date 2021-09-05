import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from catalog import models
from catalog import forms
from catalog.forms import RenewBookForm, ReturnBookForm, IssueBookForm

from .models import Author, Book, BookInstance, Genre

# Create your views here.

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all books on loan. Only visible to users with can_mark_returned permission."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'


def index(request):
    """View function for Home Page of Site"""

    #Generate counts of some of the main Objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_genres = Genre.objects.count()

    #Available Books ( status = 'a')
    num_instances_available = BookInstance.objects.filter(status='a').count()
    
    #The 'all()' is implied by default
    num_authors = Author.objects.count()

    # Number of visits to this view as counted in the session variable
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books' : num_books,
        'num_instances' : num_instances,
        'num_instances_available' : num_instances_available,
        'num_authors' : num_authors,
        'num_genres'  : num_genres,
        'num_visits'  : num_visits
    }

    #Render the HTML Template with data in the context variable context
    return render(request, 'index.html', context=context)


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def book_return(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = ReturnBookForm(request.POST)
        if form.is_valid():
            book_instance.status = form.cleaned_data['status']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed') )

    else:
        status = BookInstance.LOAN_STATUS[2]
        form = ReturnBookForm(initial={'status': status})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_return.html', context)


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def book_issue(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            book_instance.status = form.cleaned_data['status']
            book_instance.borrower = form.cleaned_data['borrower']
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed') )

    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        status = BookInstance.LOAN_STATUS[2]
        form = IssueBookForm(initial={'status': status, 'renewal_date':proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_issue.html', context)