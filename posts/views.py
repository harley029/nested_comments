from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import Http404

from posts.models import Post, Comment
from posts.forms import PostForm, CommentForm


class PostListView(ListView):
    queryset = Post.objects.all()
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post/detail.html"
    context_object_name = "post"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = self.object.comments.all()
        context["comments"] = comments
        top_level_comments = self.object.comments.filter(parent_comment__isnull=True)
        context["top_level_comments"] = top_level_comments
        return context


@method_decorator(login_required, name="dispatch")
class AddPostView(TemplateView):
    template_name = "blog/post/add_post.html"

    def get(self, request, *args, **kwargs):
        form = PostForm()
        return self.render_to_response({"form": form})

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return redirect("posts:post_list")
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:post_list")
        return self.render_to_response({"form": form})


class AddCommentView(TemplateView):
    template_name = "blog/post/add_comment.html"

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, pk=post_id)
        form = CommentForm(user=request.user)
        return self.render_to_response({"form": form, "post": post})

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, pk=post_id)
        if "cancel" in request.POST:
            return redirect("posts:post_detail", pk=post_id)
        form = CommentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.client_ip = self.get_client_ip(request)
            if request.user.is_authenticated:
                comment.author = request.user
            comment.save()
            return redirect("posts:post_detail", pk=post_id)
        else:
            return self.render_to_response({"form": form, "post": post})

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class ReplyCommentView(TemplateView):
    template_name = "blog/post/reply_comment.html"

    def get(self, request, *args, **kwargs):
        post_pk = kwargs.get("pk")
        parent_comment_id = kwargs.get("parent_comment_id")
        post = get_object_or_404(Post, pk=post_pk)
        parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
        form = CommentForm(
            user=request.user, initial={"parent_comment": parent_comment.id}
        )
        return self.render_to_response(
            {
                "form": form,
                "post": post,
                "parent_comment": parent_comment,
            }
        )

    def post(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        parent_comment_id = kwargs.get("parent_comment_id")
        post = get_object_or_404(Post, pk=post_id)
        parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
        if "cancel" in request.POST:
            return redirect("posts:post_detail", pk=post_id)
        form = CommentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.parent_comment = parent_comment
            comment.client_ip = self.get_client_ip(request)
            if request.user.is_authenticated:
                comment.author = request.user
            comment.save()
            return redirect("posts:post_detail", pk=post_id)
        else:
            return self.render_to_response(
                {
                    "form": form,
                    "post": post,
                    "parent_comment": parent_comment,
                }
            )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class TextFileView(TemplateView):
    template_name = "blog/post/txt_file_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_id = kwargs.get("comment_id")
        comment = get_object_or_404(Comment, pk=comment_id)
        try:
            with comment.text_file.open("r") as file:
                context["file_content"] = file.read()
        except Exception as e:
            raise Http404(f"Error reading the file: {e}")
        context["post"] = comment.post
        return context