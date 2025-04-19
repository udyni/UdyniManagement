from django import forms
from .models import Comment, CommentContent

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['experiment', 'measurement', 'type', 'parent']
        widgets = {
            'experiment': forms.HiddenInput(),
            'measurement': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
        }

class CommentContentForm(forms.ModelForm):
    class Meta:
        model = CommentContent
        fields = ['comment', 'version', 'author', 'timestamp', 'text']
        widgets = {
            'comment': forms.HiddenInput(),
            'version': forms.HiddenInput(),
            'author': forms.HiddenInput(),
            'timestamp': forms.HiddenInput(),
        }