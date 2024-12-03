import re
from django import forms
from captcha.fields import CaptchaField
import bleach

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        body = cleaned_data.get("body")

        if title and body:
            if Post.objects.filter(title=title, body=body).exists():
                raise forms.ValidationError("This post is already exists.")
        return cleaned_data


class CommentForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Comment
        fields = [
            "name",
            "email",
            "website",
            "body",
            "image",
            "text_file",
            "captcha",
            "parent_comment",
        ]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            # Удалить анонимные поля для зарегистрированного пользователя
            self.fields.pop("name")
            self.fields.pop("email")
            self.fields.pop("website")
        else:
            # Оставить поля для анонимного пользователя
            self.fields["name"].required = True
            self.fields["email"].required = True
        # Спрятать поле parent_comment
        self.fields["parent_comment"].widget = forms.HiddenInput()

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not re.match(r"^[A-Za-z0-9]+$", name):
            raise forms.ValidationError(
                "Имя должно быть из букв английского алфавита и цыфр."
            )
        return name

    def clean_body(self):
        body = self.cleaned_data["body"]
        allowed_tags = ["a", "code", "i", "strong"]
        allowed_attrs = {"a": ["href", "title"]}
        cleaned_body = bleach.clean(body, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        return cleaned_body

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            from PIL import Image

            img = Image.open(image)
            max_width, max_height = 320, 240
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height))
                img.save(image.file, img.format)
        return image

    def clean_text_file(self):
        text_file = self.cleaned_data.get("text_file")
        if text_file:
            if text_file.size > 102400:  # 100KB
                raise forms.ValidationError("Размер файла не более 100 KB.")
            if not text_file.name.endswith(".txt"):
                raise forms.ValidationError("Разрешены только .txt файлы.")
        return text_file

    def clean(self):
        cleaned_data = super().clean()
        if self.user and self.user.is_authenticated:
            # Не нужно заполнять name и email для зарегистрированных
            if "name" in self.cleaned_data or "email" in self.cleaned_data:
                raise forms.ValidationError(
                    "Authenticated users should not provide name and email."
                )
        else:
            # name и email требуются для анонимных пользователей
            if not cleaned_data.get("name") or not cleaned_data.get("email"):
                raise forms.ValidationError(
                    "Name and email are required for anonymous comments."
                )
