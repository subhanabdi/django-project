from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings  # Import settings
from users.models import MyUser
from users.forms import UserCreateForm, UserUpdateForm, CustomerUpdateForm, CustomerProfileForm, CustomPasswordResetForm
from django.contrib.auth.views import PasswordResetView, LogoutView
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from .forms import InviteUserForm
from .utils import generate_invite_token
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework.exceptions import AuthenticationFailed


class MyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """ Mixin for Authentication and User is Admin or not """
    def test_func(self):
        return self.request.user.user_type == 'admin'


class InviteUserView(MyMixin, FormView):
    form_class = InviteUserForm
    template_name = 'users/invite.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user_type = form.cleaned_data['user_type']
        
        # Generate token
        token = generate_invite_token(email)
        
        # Generate registration link with token and user type
        register_url = self.request.build_absolute_uri(reverse('user_app:register')) + f'?token={token}&user_type={user_type}'
        
        # Send email
        send_mail(
            'Invite to Register',
            f'Please register using the following link: {register_url}\nUser Type: {user_type}',
            settings.DEFAULT_FROM_EMAIL,  # Use settings
            [email],
            fail_silently=False,
        )
        
        messages.success(self.request, f'Invitation sent to {email}.')
        return redirect(reverse('user_app:invite'))


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'  # Template for password reset confirmation
    success_url = reverse_lazy('login')  # Redirect URL after successful password reset
    form_class = SetPasswordForm  # Form class for setting a new password
    post_reset_login = False  # Disable automatic login after password reset

    def form_valid(self, form):
        # Hash the password before saving
        form.save()
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    def get_next_page(self):
        return reverse_lazy('user_app:home') 


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    email_template_name = 'users/password_reset_email.html'
    html_email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('user_app:password_reset_done')
    template_name = 'users/password_reset.html'


class MyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """ Mixin for Authentication and User is Admin or not """
    def test_func(self):
        return self.request.user.user_type == 'admin'


@login_required()
def home(request):
    """ Home Page """
    admin_count = MyUser.objects.filter(user_type='admin').count()
    customer_count = MyUser.objects.filter(user_type='customer').count()
    context = {
        'a_count': admin_count,
        'c_count': customer_count,
    }
    return render(request, 'users/home.html', context)



class UserRegistrationView(CreateView):
    """ New User Registration """
    model = MyUser
    form_class = UserCreateForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('user_app:home')

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        user_type = request.GET.get('user_type')
        if token and user_type:
            try:
                UntypedToken(token)  # Validate token
            except AuthenticationFailed:
                messages.error(request, 'The registration link has expired.')
                return redirect(reverse_lazy('user_app:invite'))
        else:
            messages.error(request, 'Invalid registration link.')
            return redirect(reverse_lazy('user_app:invite'))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        password = form.cleaned_data['password']
        user.set_password(password)
        
        # Set user_type from the URL parameter
        user_type = self.request.GET.get('user_type')
        user.user_type = user_type
        
        messages.success(self.request, f"{user.username} is created successfully!")
        user.save()
        return redirect(reverse_lazy('user_app:home'))


class UserListView(MyMixin, ListView):
    """ List of Users for Admin """
    model = MyUser
    template_name = 'users/list.html'
    context_object_name = 'data'


class UserCreateView(MyMixin, CreateView):
    """ Create a new User by Admin """
    model = MyUser
    form_class = UserCreateForm
    template_name = 'users/create.html'
    success_url = reverse_lazy('user_app:list')

    def form_valid(self, form):
        user = form.save(commit=False)
        password = form.cleaned_data['password']
        user.set_password(password)
        messages.success(self.request, f"{user.username} is created successfully!")
        user.save()
        return redirect(reverse_lazy('user_app:list'))


class UserUpdateView(MyMixin, UpdateView):
    """ Update a user by Admin """
    model = MyUser
    form_class = UserUpdateForm
    template_name = 'users/update.html'
    success_url = reverse_lazy('user_app:list')

    def form_valid(self, form):
        super(UserUpdateView, self).form_valid(form)
        messages.success(self.request, f"user is updated successfully!")
        return redirect(reverse_lazy('user_app:list'))


class UserDeleteView(MyMixin, DeleteView):
    """ Delete a user by Admin """
    model = MyUser
    template_name = 'users/delete.html'
    success_url = reverse_lazy('user_app:list')

    def form_valid(self, form):
        super(UserDeleteView, self).form_valid(form)
        messages.warning(self.request, f"user is deleted successfully!")
        return redirect(reverse_lazy('user_app:list'))


class UserProfile(LoginRequiredMixin, UpdateView):
    """ All User Profile Page """
    def get(self, request, **kwargs):
        user = request.user
        data = MyUser.objects.get(id=user.id)
        c_form = CustomerUpdateForm(instance=user)
        p_form = CustomerProfileForm(instance=user.profile)

        context = {
            'data': data,
            'c_form': c_form,
            'p_form': p_form,
        }
        return render(request, 'users/profile.html', context)

    def post(self, request, *args, **kwargs):
        user = request.user
        c_form = CustomerUpdateForm(request.POST, instance=user)
        p_form = CustomerProfileForm(request.POST, request.FILES, instance=user.profile)
        if c_form.is_valid() and p_form.is_valid():
            username = c_form.cleaned_data['username']
            c_form.save()
            p_form.save()
            messages.success(request, f"{username}'s profile has been updated successfully!")
        return redirect(reverse_lazy('user_app:profile', kwargs={'pk': user.id}))
