# Main Imports
import random

# Django Imports
from django.shortcuts import render, get_object_or_404, HttpResponse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.contrib.auth.models import User
from django.db.models import Count

# My Module Imports
from authentication.models import BasicUserProfile, Follower
from .models import Tweet, TweetLike, TweetComment
from hashtag.models import Topic
from notification.models import NotificationLike

from utils.session_utils import get_current_user, get_current_user_profile
from utils.base_utils import left_nav_tweet_form_processing
from utils.base_utils import mobile_tweet_form_processing
from utils.base_utils import get_who_to_follow
from utils.base_utils import get_topics_to_follow


def index(request):
    """this is an index redicrector page"""

    # Get the current users
    current_basic_user = get_current_user(request, User, ObjectDoesNotExist)

    current_basic_user_profile = get_current_user_profile(
        request,
        User,
        BasicUserProfile,
        ObjectDoesNotExist
    )

    if current_basic_user == None:
        return HttpResponseRedirect("/auth/signup/")
    else:
        return HttpResponseRedirect("/home/0/")


def home(request, page):
    """this is the homepage of the site and is an proxy redirector"""

    # Get the current users
    current_basic_user = get_current_user(request, User, ObjectDoesNotExist)
    if current_basic_user is None:
        return HttpResponseRedirect("/auth/signup/")

    current_basic_user_profile = get_current_user_profile(
        request,
        User,
        BasicUserProfile,
        ObjectDoesNotExist
    )

    # Handle tweet forms from different sections
    if request.method == 'POST':
        # Home page tweet form
        if request.POST.get("home_page_tweet_form_submit_btn"):
            tweet_content = request.POST.get("tweet_content")
            tweet_image = request.FILES.get("tweet_image")
            
            if tweet_content or tweet_image:
                new_tweet = Tweet(
                    user=current_basic_user_profile, 
                    content=tweet_content,
                    image=tweet_image
                )
                new_tweet.save()
                return HttpResponseRedirect("/home/0/")
        
        # Left nav tweet form
        elif request.POST.get("hidden_panel_tweet_submit_btn"):
            tweet_content = request.POST.get("tweet_content")
            tweet_image = request.FILES.get("tweet_image")
            
            if tweet_content or tweet_image:
                new_tweet = Tweet(
                    user=current_basic_user_profile, 
                    content=tweet_content,
                    image=tweet_image
                )
                new_tweet.save()
                return HttpResponseRedirect("/home/0/")
        
        # Mobile tweet form
        elif request.POST.get("mobile_hidden_tweet_submit_btn"):
            tweet_content = request.POST.get("tweet_content")
            tweet_image = request.FILES.get("tweet_image")
            
            if tweet_content or tweet_image:
                new_tweet = Tweet(
                    user=current_basic_user_profile, 
                    content=tweet_content,
                    image=tweet_image
                )
                new_tweet.save()
                return HttpResponseRedirect("/home/0/")
        
        # Search form
        elif request.POST.get("right_nav_search_submit_btn"):
            search_input = request.POST.get("search_input")
            if search_input:
                return HttpResponseRedirect("/search/" + str(search_input) + "/")
        
        # Follow user
        elif request.POST.get("base_who_to_follow_submit_btn"):
            hidden_user_id = request.POST.get("hidden_user_id")
            try:
                followed_user = BasicUserProfile.objects.get(id=hidden_user_id)
                
                # Check if already following
                if not Follower.objects.filter(
                    follower=current_basic_user_profile,
                    following=followed_user
                ).exists():
                    new_follow = Follower(
                        following=followed_user, 
                        follower=current_basic_user_profile,
                    )
                    new_follow.save()
                
                return HttpResponseRedirect("/home/0/")
            except ObjectDoesNotExist:
                pass
        
        # Like tweet
        elif request.POST.get("tweet_cell_like_submit_btn"):
            current_tweet_id = request.POST.get("hidden_tweet_id")
            try:
                current_tweet = Tweet.objects.get(id=current_tweet_id)
                
                # Check if already liked
                if not TweetLike.objects.filter(
                    tweet=current_tweet,
                    liker=current_basic_user_profile
                ).exists():
                    new_like = TweetLike(
                        tweet=current_tweet,
                        liker=current_basic_user_profile
                    )
                    new_like.save()
                    
                    # Create notification if not liking own tweet
                    if current_tweet.user != current_basic_user_profile:
                        new_notification = NotificationLike(
                            notified=current_tweet.user,
                            notifier=current_basic_user_profile,
                            tweet=current_tweet,
                        )
                        new_notification.save()
                
                return HttpResponseRedirect("/home/0/")
            except ObjectDoesNotExist:
                pass
        
        # View tweet comments
        elif request.POST.get("tweet_cell_comment_submit_btn"):
            current_tweet_id = request.POST.get("hidden_tweet_id")
            return HttpResponseRedirect("/tweet/" + str(current_tweet_id) + "/")

    # Get followings and own profile for tweet feed
    followings = Follower.objects.filter(follower=current_basic_user_profile).values_list('following', flat=True)
    users_to_include = list(followings) + [current_basic_user_profile.id]
    
    # Pagination setup
    try:
        current_page = int(page)
    except (ValueError, TypeError):
        current_page = 0
        
    tweets_per_page = 46
    previous_page = max(0, current_page - 1)
    next_page = current_page + 1
    
    # Get tweets from followed users and self
    tweet_feed = Tweet.objects.filter(
        user__id__in=users_to_include
    ).order_by('-creation_date')[
        current_page * tweets_per_page:(current_page + 1) * tweets_per_page
    ]
    
    # Prefetch related data for efficiency
    tweet_ids = [tweet.id for tweet in tweet_feed]
    
    # Get comment counts
    comment_counts = TweetComment.objects.filter(
        tweet__id__in=tweet_ids
    ).values('tweet').annotate(count=Count('id'))
    
    comment_count_map = {item['tweet']: item['count'] for item in comment_counts}
    
    # Get like counts
    like_counts = TweetLike.objects.filter(
        tweet__id__in=tweet_ids
    ).values('tweet').annotate(count=Count('id'))
    
    like_count_map = {item['tweet']: item['count'] for item in like_counts}
    
    # Add counts to tweets
    for tweet in tweet_feed:
        tweet.tweet_comment_amount = comment_count_map.get(tweet.id, 0)
        tweet.tweet_like_amount = like_count_map.get(tweet.id, 0)
    
    # Get who to follow (exclude self and already followed)
    already_following = Follower.objects.filter(
        follower=current_basic_user_profile
    ).values_list('following__id', flat=True)
    
    who_to_follow = BasicUserProfile.objects.exclude(
        id__in=already_following
    ).exclude(
        id=current_basic_user_profile.id
    ).order_by('?')[:5]  # Random 5 profiles
    
    # Get topics to follow
    try:
        topics_to_follow = Topic.objects.annotate(
            tweet_count=Count('tweet')
        ).order_by('-tweet_count')[:5]
    except ObjectDoesNotExist:
        topics_to_follow = []

    data = {
        "current_basic_user": current_basic_user,
        "current_basic_user_profile": current_basic_user_profile,
        "who_to_follow": who_to_follow,
        "topics_to_follow": topics_to_follow,
        "tweet_feed": tweet_feed,
        "current_page": current_page,
        "previous_page": previous_page,
        "next_page": next_page,
    }
    
    return render(request, "home/home.html", data)


def tweet_single(request, tweet_id):
    """in this view the user can see a single tweet"""

    # admin user session pop
    # admin user session pop
    # Deleting any sessions regarding top-tier type of users

    # Get the current users
    current_basic_user = get_current_user(request, User, ObjectDoesNotExist)

    current_basic_user_profile = get_current_user_profile(
        request,
        User,
        BasicUserProfile,
        ObjectDoesNotExist
    )

    # Topics to follow
    topics_to_follow = get_topics_to_follow(Topic, ObjectDoesNotExist, random)

    # Who to follow box cells
    who_to_follow = get_who_to_follow(
        BasicUserProfile, ObjectDoesNotExist, random
    )

    # Get the current tweet
    try:
        current_tweet = Tweet.objects.get(id=tweet_id)
    except ObjectDoesNotExist:
        current_tweet = None

    # Get the current tweet likes
    try:
        current_tweet_likes = TweetLike.objects.filter(tweet=current_tweet)
    except ObjectDoesNotExist:
        current_tweet_likes = None

    # Get the current tweet comments
    try:
        current_tweet_comments = TweetComment.objects.filter(
            tweet=current_tweet
        ).order_by("-id")
    except ObjectDoesNotExist:
        current_tweet_comments = None

    # Current tweet like form processing
    if request.POST.get("single_tweet_like_submit_btn"):
        current_tweet.tweet_like_amount += 1
        current_tweet.save()
        new_notification = NotificationLike(
            notified=current_tweet.user,
            notifier=current_basic_user_profile,
            tweet=current_tweet,
        )
        new_notification.save()
        return HttpResponseRedirect("/tweet/"+str(current_tweet.id)+"/")

    # current tweet comment form processing
    if request.POST.get("single_tweet_reply_submit_btn"):
        reply_content = request.POST.get("reply_content")
        if bool(reply_content) == False or reply_content == "":
            pass
        else:
            new_comment = TweetComment(
                tweet=current_tweet,
                content=reply_content,
                commentor=current_basic_user_profile,
            )
            new_comment.save()
            current_tweet.tweet_comment_amount += 1
            current_tweet.save()
            return HttpResponseRedirect("/tweet/"+str(current_tweet.id)+"/")

    # tweet comment like form processing
    if request.POST.get("single_tweet_comment_like_submit_btn"):
        comment_id = request.POST.get("comment_id")
        comment = TweetComment.objects.get(id=comment_id)
        comment.like_amount += 1
        comment.save()
        return HttpResponseRedirect("/tweet/"+str(current_tweet.id)+"/")

    data = {
        "current_basic_user": current_basic_user,
        "current_basic_user_profile": current_basic_user_profile,
        "who_to_follow": who_to_follow,
        "topics_to_follow": topics_to_follow,
        "current_tweet": current_tweet,
        "current_tweet_likes": current_tweet_likes,
        "current_tweet_like_amount": len(current_tweet_likes),
        "current_tweet_comments": current_tweet_comments,
    }

    if current_basic_user == None:
        return HttpResponseRedirect("/auth/signup/")
    else:
        return render(request, "home/single_tweet.html", data)
