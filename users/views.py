from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, userLoginForm, ProfileUpdateForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .decorators import user_not_authenticated
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.db.models.query_utils import Q


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for confirming your email, You can now login")
        return redirect('login')
    else:
        messages.error(request, "Activation link is expired")

    return redirect('home')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account,"
    message = render_to_string("template_activate_account.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f"Dear <b> {user}</b>, please go to your email <b> {to_email}</b> inbox and click on \
                     received activation link to confirm and complete the registration, <b>Note:</b> check your spam folder.")
        
    else:
        messages.error(request, f"Problem sending activation email to {to_email} please check if you type correct email")

@user_not_authenticated
def userRegistrationView(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('home')

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})

@user_not_authenticated
def CustomLoginView(request):
    
    if request.method == 'POST':
        form = userLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Successfully Login in as {request.user.username}')
                return redirect('home')
        
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
    
    form =userLoginForm()

    return render(request, 'users/login.html', {'form': form})

@login_required
def CustomLogoutView(request):
    logout(request)
    messages.info(request, f'You are Logout!!')
    return redirect('home')


def CustomProfileView(request, username):
    if request.user.is_authenticated:
        if request.method == 'POST':
            user = request.user
            form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                user_form = form.save()
                messages.success(request, f"{user_form.username}, Your Profile Was Updated Successfully")
                return redirect('profile', user_form.username)
            
            for error in list(form.errors.values()):
                messages.error(request, error)

        user = get_user_model().objects.filter(username=username).first()
        if user:
            form = ProfileUpdateForm(instance=user)
            return render(request, 'users/profile.html', {'form': form})

        return redirect('home')
    return redirect('home')


@login_required
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully Changed Your Password')
            return redirect('login')
        
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
                
    form = SetPasswordForm(user)
    return render(request, 'users/password_reset_confirm.html', {'form': form})


@user_not_authenticated
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset Request"
                message = render_to_string("users/template_reset_password.html", {
                    'user': associated_user,
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    'protocol': 'https' if request.is_secure() else 'http'
                })
                email = EmailMessage(subject, message, to=[associated_user.email])
                if email.send():
                    messages.success(request, 
                         """
                            <h2>Password Reset Sent</h2>
                            <p>
                                we've emailed you instruction for setting your password, if account exist with the email entered.
                                You should receive them shortly,<br> If you don't receive an email, please make sure you have entered correct email you registered with,
                                and also check your spam folder.
                            </p>
                         """
                         )
                else:
                    messages.error(request, 'Problem sending password reset email <b>SERVER BUSY</b>')
                
            return redirect('home')
        
        for error in list(form.errors.values()):
            messages.error(request, error)
            
    form = PasswordResetForm()
    return render(
        request=request, 
        template_name='users/password_reset.html', 
        context={'form': form})

def passwordResetConfirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save() 
                messages.success(request, 'Your password has been successfully reset. You may now log in.')
                return redirect('login')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
        form = SetPasswordForm(user)
        return render(request, 'users/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')

    messages.success(request, 'Something went wrong and you have been redirected to homepage')
    return redirect('home')