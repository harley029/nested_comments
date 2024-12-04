from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse


from posts.models import Post, Comment
from posts.forms import PostForm, CommentForm


class BaseCommentView(TemplateView):

    def get_post_and_parent_comment(self, kwargs):
        post_id = kwargs.get("pk") or kwargs.get("post_id")
        post = get_object_or_404(Post, pk=post_id)
        parent_comment_id = kwargs.get("parent_comment_id")
        parent_comment = (
            get_object_or_404(Comment, pk=parent_comment_id)
            if parent_comment_id
            else None
        )
        return post, parent_comment

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")


class PostListView(ListView):
    queryset = Post.objects.all()
    context_object_name = "posts"
    paginate_by = 4
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

        page = self.request.GET.get("page", 1)
        paginator = Paginator(top_level_comments, 2)
        try:
            comments_page = paginator.page(page)
        except PageNotAnInteger:
            comments_page = paginator.page(1)
        except EmptyPage:
            comments_page = paginator.page(paginator.num_pages)
        context["comments_page"] = comments_page
        context["comment_form"] = CommentForm(user=self.request.user)
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


class AddCommentView(BaseCommentView):
    template_name = "blog/post/add_comment.html"

    def get(self, request, *args, **kwargs):
        post, _ = self.get_post_and_parent_comment(kwargs)
        form = CommentForm(user=request.user)
        return self.render_to_response({"form": form, "post": post})

    def post(self, request, *args, **kwargs):
        post, _ = self.get_post_and_parent_comment(kwargs)
        if "cancel" in request.POST:
            return redirect("posts:post_detail", pk=post.pk)
        form = CommentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.client_ip = self.get_client_ip(request)
            if request.user.is_authenticated:
                comment.author = request.user
            comment.save()
            # Render the new comment to HTML
            comment_html = render_to_string(
                "blog/post/includes/comment.html",
                {"comment": comment, "post": post, "level": 0},
                request=request,
            )
            return JsonResponse({"success": True, "comment_html": comment_html})
        else:
            # Render form errors to HTML
            errors_html = render_to_string(
                "blog/post/includes/form_errors.html",
                {"form": form},
                request=request,
            )
            return JsonResponse({"success": False, "errors_html": errors_html})


class ReplyCommentView(BaseCommentView):
    template_name = "blog/post/reply_comment.html"

    def get(self, request, *args, **kwargs):
        post, parent_comment = self.get_post_and_parent_comment(kwargs)
        form = CommentForm(
            user=request.user, initial={"parent_comment": parent_comment.id}
        )
        return self.render_to_response(
            {"form": form, "post": post, "parent_comment": parent_comment}
        )

    def post(self, request, *args, **kwargs):
        post, parent_comment = self.get_post_and_parent_comment(kwargs)
        if "cancel" in request.POST:
            return redirect("posts:post_detail", pk=post.pk)
        form = CommentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.parent_comment = parent_comment
            comment.client_ip = self.get_client_ip(request)
            if request.user.is_authenticated:
                comment.author = request.user
            comment.save()
            # Render the new comment to HTML
            comment_html = render_to_string(
                "blog/post/includes/comment.html",
                {"comment": comment, "post": post, "level": 0},
                request=request,
            )
            return JsonResponse({"success": True, "comment_html": comment_html})
        else:
            # Render form errors to HTML
            errors_html = render_to_string(
                "blog/post/includes/form_errors.html",
                {"form": form},
                request=request,
            )
            return JsonResponse({"success": False, "errors_html": errors_html})




class TextFileView(View):
    def get(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if not comment.text_file:
            return HttpResponse("No text file attached to this comment.", status=404)
        try:
            with comment.text_file.open("r") as file:
                file_content = file.read()
        except Exception as e:
            return HttpResponse(f"Error reading the file: {e}", status=500)
        html_content = render_to_string(
            "blog/post/includes/text_file_modal.html", {"file_content": file_content}
        )
        return HttpResponse(html_content, content_type="text/html; charset=utf-8")
