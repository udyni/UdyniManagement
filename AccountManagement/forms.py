from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import forms as auth_forms
from django.conf import settings # import the settings file
import ldap


class SetPasswordForm(auth_forms.SetPasswordForm):
    # Override save method to save to LDAP
    def save(self):
        # Connecto to LDAP
        try:
            # Initialize connection
            l = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)

            # Set connection options
            for k, v in settings.AUTH_LDAP_CONNECTION_OPTIONS:
                l.set_option(k, v)

            if hasattr(self, 'old_password'):
                # Password change
                l.simple_bind_s("uid={0:s},ou=People,dc=udyni,dc=lab", self.cleaned_data['old_password'])
                l.passwd_s("uid={0:s},ou=People,dc=udyni,dc=lab", self.cleaned_data['old_password'], self.cleaned_data["new_password1"])

            else:
                # Password reset
                l.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
                l.passwd_s("uid={0:s},ou=People,dc=udyni,dc=lab", None, self.cleaned_data["new_password1"])

        except ldap.LDAPError as e:
            # TODO: handle errors
            pass


class PasswordChangeForm(SetPasswordForm):
    """
    A form that lets a user change their password by entering their old
    password.
    """

    error_messages = {
        **SetPasswordForm.error_messages,
        "password_incorrect": "Your old password was entered incorrectly. Please enter it again.",
    }
    old_password = forms.CharField(
        label="Old password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )

    field_order = ["old_password", "new_password1", "new_password2"]

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password


class RegistrationForm(forms.Form):
    pass
